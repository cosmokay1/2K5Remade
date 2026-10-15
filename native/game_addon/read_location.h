/* Translate a borrowed host span to a bounded guest locator; no dereference. */
#ifndef NFL2K5_ADDON_READ_LOCATION_H
#define NFL2K5_ADDON_READ_LOCATION_H
#include <stdint.h>
#include <stddef.h>
static inline int addon_read_location(uintptr_t base,const void *bytes,size_t size,
        int (*range)(uint32_t,size_t),uint32_t *out) {
    uintptr_t pointer=(uintptr_t)bytes;
    if(!base || !bytes || !size || !range || !out || pointer<base ||
       pointer-base>UINT32_MAX) return 0;
    uint32_t address=(uint32_t)(pointer-base);
    if(!address || size>UINT64_C(0x100000000)-address || !range(address,size)) return 0;
    *out=address;return 1;
}
#endif
