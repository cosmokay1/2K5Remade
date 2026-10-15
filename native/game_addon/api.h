/* Native addon ABI. Application message names/payloads belong to the addon. */
#ifndef NFL2K5_GAME_ADDON_API_H
#define NFL2K5_GAME_ADDON_API_H
#include <stdint.h>
#include <stddef.h>
#define NFL2K5_ADDON_ABI 2u
#ifdef __cplusplus
extern "C" {
#endif
typedef struct NFL2K5AddonHost {
    uint32_t size;
    int (*memory_range)(uint32_t address, size_t size);
    /* The Remade host refuses reads outside an uninterrupted guest-lock-owned
     * invocation. Treat zero as unavailable; a saved function pointer does not
     * extend that scope. */
    int (*read_memory)(uint32_t address, void *destination, size_t size);
} NFL2K5AddonHost;
typedef struct NFL2K5AddonAPI {
    uint32_t size;
    int (*start)(const NFL2K5AddonHost *host);
    void (*stop)(void);
    void (*poll)(void);
    /* Synchronous borrowed buffers; never retain pointers after return.
     * Return 0 for unknown messages or invalid sizes. Snapshot readers must
     * not block on I/O; ownership and consistency belong to the application. */
    int (*event)(const char *name, const void *data, size_t size);
    int (*snapshot)(const char *name, void *out, size_t capacity);
} NFL2K5AddonAPI;
typedef const NFL2K5AddonAPI *(*NFL2K5AddonQuery)(uint32_t abi);
#ifdef __cplusplus
}
#endif
#endif
