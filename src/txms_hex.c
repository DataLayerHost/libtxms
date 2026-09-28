/* SPDX-License-Identifier: LicenseRef-CORE */
#include "internal.h"
int txms_nibble(uint8_t c)
{
	if (c >= '0' && c <= '9') return c - '0';
	if (c >= 'a' && c <= 'f') return c - 'a' + 10;
	if (c >= 'A' && c <= 'F') return c - 'A' + 10;
	return -1;
}
int txms_is_hex(const void *text, size_t n)
{
	const uint8_t *p = text;
	if (!p || n > TXMS_MAX_INPUT) return 0;
	if (n >= 2 && p[0] == '0' && (p[1] == 'x' || p[1] == 'X')) { p += 2; n -= 2; }
	if (!n || n % 2) return 0;
	for (size_t i = 0; i < n; i++) if (txms_nibble(p[i]) < 0) return 0;
	return 1;
}
int txms_normalize_hex(const void *text, size_t n, txms_buffer *out)
{
	const uint8_t *p = text;
	int rc;
	if (!txms_is_hex(p, n)) return TXMS_INVALID;
	if (n >= 2 && p[0] == '0' && (p[1] == 'x' || p[1] == 'X')) { p += 2; n -= 2; }
	if ((rc = txms_alloc(out, n + 2))) return rc;
	out->data[0] = '0'; out->data[1] = 'x';
	for (size_t i = 0; i < n; i++) out->data[i + 2] = (uint8_t)"0123456789abcdef"[txms_nibble(p[i])];
	out->len = n + 2; out->data[out->len] = 0;
	return TXMS_OK;
}
