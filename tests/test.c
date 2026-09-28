/* SPDX-License-Identifier: LicenseRef-CORE */
#include "txms.h"
#include <assert.h>
#include <string.h>
int main(void)
{
	txms_buffer b = {0}, c = {0};
	assert(txms_is_hex("0XAb00", 6));
	assert(!txms_is_hex("0x", 2)); assert(!txms_is_hex("abc", 3));
	assert(!txms_is_hex("ab\0c", 4)); assert(!txms_is_hex(" ab ", 4));
	assert(txms_normalize_hex("0XAb00", 6, &b) == 0);
	assert(b.len == 6 && !memcmp(b.data, "0xab00", 6)); txms_buffer_free(&b);
	assert(txms_encode("0000007ed800ffff", 16, &b) == 0);
	assert(txms_decode(b.data, b.len, &c) == 0);
	assert(!strcmp((char *)c.data, "0x7ed800ffff"));
	txms_buffer_free(&b); txms_buffer_free(&c);
	assert(txms_decode("~", 1, &b) == TXMS_INVALID);
	assert(txms_decode("~aa", 3, &b) == TXMS_INVALID);
	assert(txms_decode("\xc0\xaf", 2, &b) == TXMS_INVALID);
	assert(txms_utf16be_to_utf8("\xd8\x00", 2, &b) == TXMS_INVALID);
	assert(txms_utf16be_to_utf8("\xd8\x3d\xde\x00", 4, &b) == 0);
	assert(txms_utf8_to_utf16be(b.data, b.len, &c) == 0);
	assert(c.len == 4 && !memcmp(c.data, "\xd8\x3d\xde\x00", 4));
	txms_buffer_free(&b); txms_buffer_free(&c);
	assert(txms_transactions("0XAB\r\n1234\n", 11, &b) == 0);
	assert(!strcmp((char *)b.data, "0xab\n0x1234")); txms_buffer_free(&b);
	assert(txms_transactions("ab\n\ncd", 6, &b) == TXMS_INVALID);
	assert(txms_transactions("abc", 3, &b) == TXMS_INVALID);
	assert(txms_transactions("0xGG", 4, &b) == TXMS_INVALID);
	assert(txms_transactions("~Āā", 5, &b) == TXMS_INVALID); /* JS strips to odd 0x1. */
	for (unsigned v = 0; v < 65536; v++) {
		uint8_t bytes[2] = {(uint8_t)(v >> 8), (uint8_t)v};
		assert(!txms_encode_bytes(bytes, 2, &b));
		assert(!txms_decode(b.data, b.len, &c));
		txms_buffer_free(&b); txms_buffer_free(&c);
	}
	return 0;
}
