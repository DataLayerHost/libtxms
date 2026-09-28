/* SPDX-License-Identifier: LicenseRef-CORE */
#include "internal.h"
int txms_next(const uint8_t *p, size_t n, size_t *i, uint32_t *cp)
{
	uint32_t c, min;
	unsigned extra;
	if (*i >= n) return TXMS_INVALID;
	c = p[(*i)++];
	if (c < 128) { *cp = c; return 0; }
	if (c >= 0xc2 && c <= 0xdf) { extra = 1; min = 0x80; c &= 31; }
	else if (c >= 0xe0 && c <= 0xef) { extra = 2; min = 0x800; c &= 15; }
	else if (c >= 0xf0 && c <= 0xf4) { extra = 3; min = 0x10000; c &= 7; }
	else return TXMS_INVALID;
	if (n - *i < extra) return TXMS_INVALID;
	while (extra--) {
		uint8_t b = p[(*i)++];
		if ((b & 0xc0) != 0x80) return TXMS_INVALID;
		c = (c << 6) | (b & 63);
	}
	if (c < min || c > 0x10ffff || (c >= 0xd800 && c <= 0xdfff)) return TXMS_INVALID;
	*cp = c; return 0;
}
size_t txms_put(uint8_t *p, uint32_t c)
{
	if (c < 128) { p[0] = (uint8_t)c; return 1; }
	if (c < 0x800) { p[0] = (uint8_t)(0xc0 | (c >> 6)); p[1] = (uint8_t)(0x80 | (c & 63)); return 2; }
	if (c < 0x10000) { p[0] = (uint8_t)(0xe0 | (c >> 12)); p[1] = (uint8_t)(0x80 | ((c >> 6) & 63)); p[2] = (uint8_t)(0x80 | (c & 63)); return 3; }
	p[0] = (uint8_t)(0xf0 | (c >> 18)); p[1] = (uint8_t)(0x80 | ((c >> 12) & 63)); p[2] = (uint8_t)(0x80 | ((c >> 6) & 63)); p[3] = (uint8_t)(0x80 | (c & 63)); return 4;
}
int txms_utf16be_to_utf8(const void *bytes, size_t n, txms_buffer *out)
{
	const uint8_t *p = bytes;
	int rc;
	if (!p || n % 2 || n > TXMS_MAX_INPUT) return TXMS_INVALID;
	if ((rc = txms_alloc(out, n * 2))) return rc;
	for (size_t i = 0; i < n; i += 2) {
		uint32_t c = ((uint32_t)p[i] << 8) | p[i + 1];
		if (c >= 0xd800 && c <= 0xdbff) {
			if (n - i < 4) goto invalid;
			uint32_t lo = ((uint32_t)p[i + 2] << 8) | p[i + 3];
			if (lo < 0xdc00 || lo > 0xdfff) goto invalid;
			c = 0x10000 + ((c - 0xd800) << 10) + lo - 0xdc00; i += 2;
		} else if (c >= 0xdc00 && c <= 0xdfff) goto invalid;
		out->len += txms_put(out->data + out->len, c);
	}
	out->data[out->len] = 0; return 0;
invalid:
	txms_buffer_free(out); return TXMS_INVALID;
}
int txms_utf8_to_utf16be(const void *text, size_t n, txms_buffer *out)
{
	const uint8_t *p = text;
	int rc;
	if (!p || n > TXMS_MAX_INPUT) return TXMS_INVALID;
	if ((rc = txms_alloc(out, n * 2))) return rc;
	for (size_t i = 0; i < n;) {
		uint32_t c;
		if (txms_next(p, n, &i, &c)) { txms_buffer_free(out); return TXMS_INVALID; }
		if (c > 0xffff) {
			uint32_t hi = 0xd800 + ((c - 0x10000) >> 10);
			out->data[out->len++] = (uint8_t)(hi >> 8); out->data[out->len++] = (uint8_t)hi;
			c = 0xdc00 + ((c - 0x10000) & 1023);
		}
		out->data[out->len++] = (uint8_t)(c >> 8); out->data[out->len++] = (uint8_t)c;
	}
	out->data[out->len] = 0; return 0;
}
