/* SPDX-License-Identifier: LicenseRef-CORE */
#include "txms.h"
#include <stdio.h>
#include <string.h>
int main(void)
{
	char line[65536];
	while (fgets(line, sizeof(line), stdin)) {
		txms_buffer b = {0}, d = {0};
		size_t n = strcspn(line, "\r\n");
		if (txms_encode(line, n, &b) || txms_decode(b.data, b.len, &d)) return 1;
		for (size_t i = 0; i < b.len; i++) printf("%02x", b.data[i]);
		printf("\t%.*s\n", (int)d.len, d.data);
		txms_buffer_free(&b); txms_buffer_free(&d);
	}
	return ferror(stdin) ? 1 : 0;
}
