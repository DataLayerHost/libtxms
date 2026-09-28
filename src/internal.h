/* SPDX-License-Identifier: LicenseRef-CORE */
#ifndef TXMS_INTERNAL_H
#define TXMS_INTERNAL_H
#include "txms.h"
int txms_alloc(txms_buffer *b, size_t n);
int txms_nibble(uint8_t c);
int txms_next(const uint8_t *p, size_t n, size_t *i, uint32_t *cp);
size_t txms_put(uint8_t *p, uint32_t cp);
int txms_escape(uint16_t cp);
#endif
