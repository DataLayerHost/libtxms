# libtxms

A standalone C11 implementation of the TxMS codec. No Kamailio, Node, Dart, or runtime Unicode dependency. Licensed under the [CORE License](LICENSE).

## Build and test

```sh
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
make sanitize
cmake --install build --prefix /usr/local
```

Use `-DBUILD_SHARED_LIBS=ON` for a shared library. A header, library, CMake target export and `txms.pc` are installed. Consumers can use `pkg-config --cflags --libs txms`. macOS and Linux are tested. The codec uses standard C11 and has no platform API dependencies.

```c
#include <txms.h>

txms_buffer encoded = {0}, decoded = {0};
if (txms_encode("0x1234abcd", 10, &encoded) == TXMS_OK) {
  if (txms_decode(encoded.data, encoded.len, &decoded) == TXMS_OK) {
    /* decoded.data contains "0x1234abcd"; decoded.len excludes the NUL. */
  }
}
txms_buffer_free(&decoded);
txms_buffer_free(&encoded);
```

All inputs have explicit byte lengths. Outputs are allocated by the library and include an extra NUL sentinel; use the length, especially for UTF-16BE. Initialize each output to `{0}` and free it before reuse. Errors leave outputs empty. Input is capped at 16 MiB; output arithmetic is checked before allocation. APIs are reentrant and own no mutable global state.

## API and wire behavior

- `txms_encode`: hexadecimal → UTF-8 TxMS. Optional `0x`/`0X`, either case, nonempty. Odd nibble counts are accepted, matching JavaScript. The first UTF-16 code unit is padded on the left to four hex digits.
- `txms_encode_bytes`: explicit-length binary → TxMS, including embedded zero bytes. It produces the same result as encoding the corresponding hex string.
- `txms_decode`: UTF-8 TxMS → lowercase `0x` hex. Escapes are `~` followed by two U+0100–U+01FF code units. Their low bytes reconstruct the original UTF-16 unit. Surrogates in the transaction are escaped independently.
- `txms_is_hex`: nonempty even hex digits with an optional prefix. No whitespace, embedded NUL or separators.
- `txms_normalize_hex`: strict detection followed by lowercase, prefixed normalization. Preserves leading zeroes.
- `txms_utf16be_to_utf8` / `txms_utf8_to_utf16be`: strict Unicode conversion. Reject unpaired surrogates, overlong UTF-8, truncated input and invalid scalars.
- `txms_transactions`: validates a complete newline-separated batch atomically. Valid hex bypasses TxMS decoding. CRLF delimiters and one terminal LF are accepted; whitespace and BOMs are not stripped. Empty lines, invalid prefixed hex and odd strings consisting entirely of hex digits are rejected. Every final transaction must have a nonempty even number of digits.

**The reference codec is lossy for leading zeroes.** JavaScript decoding strips every leading zero nibble, so `encode("0001")` decodes to `"0x1"`, and zero decodes to `"0x"`. This implementation preserves that behavior. Binary input is supported, but the original length/leading zeroes cannot be recovered without out-of-band information. The gateway batch API rejects odd or empty decoded results instead of inventing bytes. Use plain normalized hex to preserve leading zeroes for submission.

Malformed escapes are rejected rather than reproducing JavaScript's `NaN` coercion. Valid encoded data remains byte-for-byte compatible. The special-character table uses Unicode 16.0 categories C and Z, plus U+FFFD and `~`. It is checked in for reproducible behavior; regenerate with `node tools/unicode.mjs` only after reviewing compatibility changes.

## Reference provenance and cross-language tests

Sources inspected before implementation:

- [txms.js](https://github.com/bchainhub/txms.js), commit `53de2be00f10a9439781f90d6a92db418ef2fdef`: primary behavioral reference; CORE License. Its `test/samples.json` is preserved as `tests/typescript-samples.json`.
- [flutter_txms](https://github.com/bchainhub/flutter_txms), commit `3a593f0c3021007ee21b74932d2d640bc6fff2a3`: cross-check.

The Flutter implementation encodes the selected vectors identically, but its escape decoder retains the `01` prefix of each escape character. For example, `~Āž` decodes to `0x10017e` in Dart and `0x7e` in JavaScript/C. The test records this known upstream divergence; the C library follows TypeScript. Neither reference repository is modified.

```sh
# Build a separate copy of the pinned TypeScript checkout first (npm install; npm run build).
node tests/compatibility.mjs build/txms_oracle /path/to/txms.js/dist/index.js
# Copies the Flutter checkout into a temporary directory before running Flutter.
python3 tests/flutter_compatibility.py build/txms_oracle /path/to/flutter_txms
```

The TypeScript comparison covers all 65,536 BMP code units, 1,000 deterministic randomized byte strings, published samples, odd hex lengths, prefixes and zero padding: 66,543 comparisons. Unit tests also cover invalid encodings, UTF-16 conversion and batch validation.

```sh
CC=clang cmake -S . -B build-fuzz -DTXMS_FUZZ=ON -DTXMS_SANITIZE=ON
cmake --build build-fuzz
build-fuzz/txms_fuzz -runs=20000 -max_len=2048
```

No transaction structure or signature validation is attempted; those belong to the blockchain node.

## Conan 2 packages

A Conan 2 recipe and a separate C consumer test are included. The codec has no
third-party runtime dependencies, so no Conan dependency lockfile is needed or
committed. Release sources are pinned by version and SHA-256 instead. Build,
package-cache, generated preset and local environment files are ignored by Git.

```sh
python3 -m pip install 'conan>=2.12,<3'
conan profile detect
conan create . --build=missing --no-remote
conan create . --build=missing --no-remote -o 'libtxms/*:shared=True'
# Consume the package from the local Conan cache:
conan install --requires=libtxms/0.1.0 --build=missing -g CMakeDeps -g CMakeToolchain
```

Consumers use `find_package(txms CONFIG REQUIRED)` and link `txms::txms`.
Conan packages include the CORE license and attribution. Packaging recipes and
the standalone `test_package` are MIT licensed under [packaging/LICENSE](packaging/LICENSE);
the library remains CORE licensed. `shared` and `fPIC` are supported. CI builds
static/shared packages on Linux, macOS and Windows; Windows packaging checks
run in hosted CI and have not been executed locally.

## GitHub releases

[release.yml](.github/workflows/release.yml) starts when a stable GitHub Release
is **published**, using tags such as `0.1.0` without a `v` prefix. It calls the
complete CI workflow at the tagged commit, including sanitizers, compatibility
tests, fuzz checks and Conan consumer tests. The release is already visible while
tests run; assets are attached only after all tests and package checks pass.

1. Update `CMakeLists.txt`, commit the version/workflow changes and push them.
2. Create and publish a GitHub Release for the matching tag, such as `0.1.0`,
   through GitHub's Releases page. Pushing a tag alone does not run this workflow.
3. After checking the tag/version and passing tests, the workflow uploads:
   - `libtxms-0.1.0.tar.gz`: source from the exact tested Git commit.
   - `release.json`: version, commit and source checksum.
   - `SHA256SUMS`: checksums for all release assets.

The workflow uploads assets to the existing release using `GITHUB_TOKEN` after
CI succeeds. Prereleases are skipped. Existing assets are not overwritten.
No prebuilt platform libraries are attached; consumers can build from source
or use the included local Conan recipe. ConanCenter publication is disabled.

Local validation details are in [tests/VALIDATION.md](tests/VALIDATION.md).
