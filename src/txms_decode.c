/* SPDX-License-Identifier: LicenseRef-CORE */
#include "internal.h"
#include <string.h>
static void unit(txms_buffer *b, uint32_t c)
{
	for (int shift = 12; shift >= 0; shift -= 4) b->data[b->len++] = (uint8_t)"0123456789abcdef"[(c >> shift) & 15];
}
int txms_decode(const void *text, size_t n, txms_buffer *out)
{
	const uint8_t *p = text;
	int rc;
	if (!p || n > TXMS_MAX_INPUT) return TXMS_INVALID;
	if ((rc = txms_alloc(out, n * 4 + 2))) return rc;
	out->data[0] = '0'; out->data[1] = 'x'; out->len = 2;
	for (size_t i = 0; i < n;) {
		uint32_t c;
		if (txms_next(p, n, &i, &c)) goto invalid;
		if (c == '~') {
			uint32_t a, b;
			/* Reject malformed escapes instead of reproducing JS NaN coercion. */
			if (txms_next(p, n, &i, &a) || txms_next(p, n, &i, &b) || a < 0x100 || a > 0x1ff || b < 0x100 || b > 0x1ff) goto invalid;
			unit(out, ((a & 255) << 8) | (b & 255));
		} else if (c > 0xffff) {
			unit(out, 0xd800 + ((c - 0x10000) >> 10)); unit(out, 0xdc00 + ((c - 0x10000) & 1023));
		} else unit(out, c);
	}
	size_t first = 2;
	while (first < out->len && out->data[first] == '0') first++;
	memmove(out->data + 2, out->data + first, out->len - first);
	out->len -= first - 2; out->data[out->len] = 0; return 0;
invalid:
	txms_buffer_free(out); return TXMS_INVALID;
}
