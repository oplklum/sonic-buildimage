/* SPDX-License-Identifier: GPL-2.0-only */
/*
 * Intel PCH/PCU SPI flash driver.
 *
 * Copyright (C) 2016, Intel Corporation
 * Author: Mika Westerberg <mika.westerberg@linux.intel.com>
 */

#ifndef INTEL_SPI_H
#define INTEL_SPI_H

#include <linux/platform_data/intel-spi.h>
#include <linux/string.h>

#define mem_clear(data, size) memset((data), 0, (size))
struct intel_spi;
struct resource;

struct intel_spi *intel_spi_probe(struct device *dev,
	struct resource *mem, const struct intel_spi_boardinfo *info);
int intel_spi_remove(struct intel_spi *ispi);

#endif /* INTEL_SPI_H */
