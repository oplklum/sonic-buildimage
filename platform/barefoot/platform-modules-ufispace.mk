# Ufispace S9180-32X Platform modules

UFISPACE_S9180_32X_PLATFORM_MODULE_VERSION = 1.1.0

export UFISPACE_S9180_32X_PLATFORM_MODULE_VERSION

UFISPACE_S9180_32X_PLATFORM_MODULE = sonic-platform-ufispace-s9180-32x_$(UFISPACE_S9180_32X_PLATFORM_MODULE_VERSION)_amd64.deb
$(UFISPACE_S9180_32X_PLATFORM_MODULE)_SRC_PATH = $(PLATFORM_PATH)/sonic-platform-modules-ufispace
$(UFISPACE_S9180_32X_PLATFORM_MODULE)_DEPENDS += $(LINUX_HEADERS) $(LINUX_HEADERS_COMMON)
$(UFISPACE_S9180_32X_PLATFORM_MODULE)_PLATFORM = x86_64-ufispace_s9180_32x-r0
SONIC_DPKG_DEBS += $(UFISPACE_S9180_32X_PLATFORM_MODULE)

$(eval $(call add_extra_package,$(UFISPACE_S9180_32X_PLATFORM_MODULE)))

