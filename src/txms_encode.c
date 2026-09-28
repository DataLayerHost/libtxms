/* SPDX-License-Identifier: LicenseRef-CORE */
#include "internal.h"
#include "unicode_ranges.h"
int txms_escape(uint16_t c)
{
	if (c == 0x7e || c == 0xfffd) return 1;
	size_t lo = 0, hi = sizeof(txms_ranges) / sizeof(txms_ranges[0]);
	while (lo < hi) {
		size_t mid = lo + (hi - lo) / 2;
		if (c < txms_ranges[mid][0]) hi = mid;
		else if (c > txms_ranges[mid][1]) lo = mid + 1;
		else return 1;
	}
	return 0;
}
int txms_encode(const void *hex, size_t n, txms_buffer *out)
{
	const uint8_t *p = hex;
	int rc;
	if (!p || n > TXMS_MAX_INPUT) return TXMS_INVALID;
	if (n >= 2 && p[0] == '0' && (p[1] == 'x' || p[1] == 'X')) { p += 2; n -= 2; }
	if (!n) return TXMS_INVALID;
	for (size_t i = 0; i < n; i++) if (txms_nibble(p[i]) < 0) return TXMS_INVALID;
	if ((rc = txms_alloc(out, ((n + 3) / 4) * 5))) return rc;
	/* JS pads the first UTF-16 code unit on the left, including odd nibbles. */
	size_t width = n % 4 ? n % 4 : 4;
	for (size_t i = 0; i < n; width = 4) {
		uint16_t c = 0;
		for (size_t j = 0; j < width; j++) c = (uint16_t)((c << 4) | txms_nibble(p[i++]));
		if (txms_escape(c)) {
			out->data[out->len++] = '~';
			out->len += txms_put(out->data + out->len, 0x100 + (c >> 8));
			out->len += txms_put(out->data + out->len, 0x100 + (c & 255));
		} else out->len += txms_put(out->data + out->len, c);
	}
	out->data[out->len] = 0; return 0;
}
int txms_encode_bytes(const void *bytes, size_t n, txms_buffer *out)
{
	const uint8_t *p = bytes;
	txms_buffer hex = {0};
	int rc;
	if (!p || !n || n > TXMS_MAX_INPUT / 2) return TXMS_INVALID;
	if ((rc = txms_alloc(&hex, n * 2))) return rc;
	for (size_t i = 0; i < n; i++) {
		hex.data[i * 2] = (uint8_t)"0123456789abcdef"[p[i] >> 4];
		hex.data[i * 2 + 1] = (uint8_t)"0123456789abcdef"[p[i] & 15];
	}
	rc = txms_encode(hex.data, n * 2, out); txms_buffer_free(&hex); return rc;
}
