/* SPDX-License-Identifier: LicenseRef-CORE */
#ifndef TXMS_H
#define TXMS_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define TXMS_MAX_INPUT (16u * 1024u * 1024u)
typedef struct { uint8_t *data; size_t len; } txms_buffer;
typedef enum { TXMS_OK = 0, TXMS_INVALID = -1, TXMS_LIMIT = -2, TXMS_NOMEM = -3 } txms_status;
/* Initialize outputs to {0}; free successful outputs before reusing them.
 * Text inputs/outputs are UTF-8, explicit length, with an extra sentinel NUL.
 * encode accepts odd hex lengths like txms.js; is_hex is deliberately stricter.
 * decode mirrors JS leading-zero removal and may return odd digits or "0x".
 */
void txms_buffer_free(txms_buffer *buffer);
int txms_is_hex(const void *text, size_t len);
int txms_normalize_hex(const void *text, size_t len, txms_buffer *out);
int txms_encode(const void *hex, size_t len, txms_buffer *out);
int txms_encode_bytes(const void *bytes, size_t len, txms_buffer *out);
int txms_decode(const void *utf8, size_t len, txms_buffer *out);
int txms_utf16be_to_utf8(const void *bytes, size_t len, txms_buffer *out);
int txms_utf8_to_utf16be(const void *text, size_t len, txms_buffer *out);
/* Newline batch normalization. All lines validated before returning.
 * CRLF and one terminal newline accepted; no whitespace trimming.
 * Output: one nonempty, even-length, lowercase 0x transaction per line.
 */
int txms_transactions(const void *text, size_t len, txms_buffer *out);
#ifdef __cplusplus
}
#endif
#endif
