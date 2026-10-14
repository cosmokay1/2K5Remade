#ifndef NFL2K5_GAME_ADDON_H
#define NFL2K5_GAME_ADDON_H
#include <stdint.h>
#include <stddef.h>
#include "host_client.h"
#define NFL2K5_ADDON_ABI 1u
#ifdef __cplusplus
extern "C" {
#endif
typedef struct NFL2K5AddonHost {
    uint32_t size;
    int (*memory_range)(uint32_t address, size_t size);
    int (*read_memory)(uint32_t address, void *destination, size_t size);
} NFL2K5AddonHost;
typedef struct NFL2K5AddonAPI {
    uint32_t size;
    int (*start)(const NFL2K5AddonHost *host);
    void (*stop)(void);
    void (*fsm)(uint32_t object, uint32_t descriptor, int push);
    void (*poll)(void);
    void (*signing)(uint32_t stage, uint32_t context, uint32_t result, uint32_t return_code, uint32_t stack);
    int (*display)(FranchiseSigningDisplay *out);
} NFL2K5AddonAPI;
typedef const NFL2K5AddonAPI *(*NFL2K5AddonQuery)(uint32_t abi);
#ifdef __cplusplus
}
#endif
#endif
