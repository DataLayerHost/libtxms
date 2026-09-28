/* SPDX-License-Identifier: LicenseRef-CORE */
#include "txms.h"
int LLVMFuzzerTestOneInput(const uint8_t *p, size_t n)
{
	txms_buffer b = {0};
	txms_decode(p, n, &b); txms_buffer_free(&b);
	txms_encode(p, n, &b); txms_buffer_free(&b);
	txms_utf16be_to_utf8(p, n, &b); txms_buffer_free(&b);
	txms_transactions(p, n, &b); txms_buffer_free(&b);
	return 0;
}
