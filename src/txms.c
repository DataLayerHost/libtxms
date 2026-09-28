/* SPDX-License-Identifier: LicenseRef-CORE */
#include "internal.h"
#include <stdlib.h>
#include <string.h>
void txms_buffer_free(txms_buffer *b)
{
	if (b) { free(b->data); b->data = NULL; b->len = 0; }
}
int txms_alloc(txms_buffer *b, size_t n)
{
	if (!b || b->data) return TXMS_INVALID;
	if (n > TXMS_MAX_INPUT * 12u) return TXMS_LIMIT;
	b->data = malloc(n + 1);
	if (!b->data) return TXMS_NOMEM;
	b->len = 0; b->data[0] = 0;
	return TXMS_OK;
}
int txms_transactions(const void *text, size_t len, txms_buffer *out)
{
	const uint8_t *p = text;
	size_t start = 0, used = 0;
	int rc;
	if (!p || !len || len > TXMS_MAX_INPUT) return TXMS_INVALID;
	if ((rc = txms_alloc(out, len * 4 + 3)) != 0) return rc;
	while (start < len) {
		size_t end = start;
		txms_buffer line = {0}, normalized = {0};
		while (end < len && p[end] != '\n') end++;
		size_t n = end - start;
		if (end < len && n && p[start + n - 1] == '\r') n--;
		if (!n) { rc = TXMS_INVALID; goto fail; }
		if (txms_is_hex(p + start, n)) rc = txms_normalize_hex(p + start, n, &normalized);
		else {
			int all_hex = 1;
			for (size_t k = 0; k < n; k++) if (txms_nibble(p[start + k]) < 0) all_hex = 0;
			if (all_hex || (n >= 2 && p[start] == '0' && (p[start+1] == 'x' || p[start+1] == 'X'))) { rc = TXMS_INVALID; goto fail; }
			rc = txms_decode(p + start, n, &line);
			if (!rc) rc = txms_normalize_hex(line.data, line.len, &normalized);
		}
		txms_buffer_free(&line);
		if (rc) { txms_buffer_free(&normalized); goto fail; }
		if (used) out->data[used++] = '\n';
		memcpy(out->data + used, normalized.data, normalized.len);
		used += normalized.len;
		txms_buffer_free(&normalized);
		start = end + 1;
	}
	out->len = used; out->data[used] = 0;
	return TXMS_OK;
fail:
	txms_buffer_free(out); return rc;
}
