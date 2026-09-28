# Validation report — 2026-09-28

- macOS arm64 / Apple Clang 21: unit tests, ASan and UBSan passed.
- Debian 12 arm64 / Clang 14: unit tests, ASan and UBSan passed through the gateway build.
- 66,543 byte-for-byte TypeScript encode/decode comparisons passed (Node 24.2.0, Unicode 16).
- All 65,536 BMP values also exercised by the C unit tests.
- Flutter cross-check: six matching encodings, two matching decodes and four known escape-decoding divergences verified.
- Reference suites in temporary copies: 68 JavaScript tests and 35 Flutter tests passed.
- Seeded decoder/encoder/UTF-16/batch libFuzzer target: 20,000 iterations, no sanitizer findings.
- Shared library installation, relocatable pkg-config metadata and an independent CMake find_package consumer verified on macOS.
- GitHub workflow and issue-template YAML parsed successfully; hosted CI has not yet run.

The original TypeScript and Flutter repositories were not modified. The reference
codec loses leading zero nibbles; libtxms preserves that behavior and documents
its effect on binary round trips. Malformed escape inputs are deliberately rejected.

## Release and Conan automation follow-up

- GitHub Actions workflows passed `actionlint` 1.7.12 and YAML parsing.
- Release tooling tests passed: tag/version matching, exact-commit archives,
  dirty-tree rejection and dependency metadata.
- libtxms Conan 2.32.0 static/shared packages and their separate C consumer passed
  on macOS arm64 and Debian 12 arm64. The staged ConanCenter download recipe also
  passed both configurations on both operating systems using the same checksummed
  archive served by a local HTTP server.
- ConanCenter metadata tests verify preserved older versions, idempotent updates,
  refusal to replace a version checksum, and tampered-archive rejection.
- macOS codec and gateway sanitizer suites passed after the CMake packaging changes.
- No release or upstream ConanCenter PR was published. Hosted Windows packaging
  and the actual GitHub publication steps remain to be exercised by CI after push.
