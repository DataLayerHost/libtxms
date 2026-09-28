/* SPDX-License-Identifier: MIT */
#include <txms.h>
#include <string.h>
int main(void)
{
	txms_buffer encoded = {0}, decoded = {0};
	int rc = 1;
	if (txms_encode("0x1234abcd", 10, &encoded) != TXMS_OK) goto done;
	if (txms_decode(encoded.data, encoded.len, &decoded) != TXMS_OK) goto done;
	if (decoded.len == 10 && !memcmp(decoded.data, "0x1234abcd", 10)) rc = 0;
done:
	txms_buffer_free(&encoded);
	txms_buffer_free(&decoded);
	return rc;
}
