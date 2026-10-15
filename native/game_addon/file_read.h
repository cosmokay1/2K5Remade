/* Optional in-process observation; never put native pointers on a sidecar wire. */
#ifndef NFL2K5_ADDON_FILE_READ_H
#define NFL2K5_ADDON_FILE_READ_H
#include <stddef.h>
#include <stdint.h>
#define NFL2K5_ADDON_FILE_READ "engine.file-read.v1"
typedef struct NFL2K5AddonFileRead {
    uintptr_t native_handle;
    const void *bytes;
    size_t requested, completed;
    int32_t status;
} NFL2K5AddonFileRead;
/* The handle and bytes are borrowed only during event(). Copy bounded needed
 * data before returning; do not modify bytes, close/retain the handle or block
 * on a process/network request. bytes is NULL for empty/failed/oversized reads.
 * A read may occur without guest-lock ownership; this event grants no extra
 * guest-memory access, writes, save/franchise identity or application permission.
 * No file offset, path, deserialization or immutable-source assertion is made.
 * Addons that do not understand this optional event may ignore it.
 */
#endif
