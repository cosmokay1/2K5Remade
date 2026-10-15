#ifndef NFL2K5_ADDON_LOADER_H
#define NFL2K5_ADDON_LOADER_H
#include <stddef.h>
/* Set the validated XBE load-input digest before starting an addon.
 * A loaded addon cannot be rebound to a different image. No write authority. */
int nfl2k5_addon_bind_image(const char *sha256);
int nfl2k5_addon_start(void);
void nfl2k5_addon_stop(void);
int nfl2k5_sidecar_loaded(void);
void nfl2k5_addon_poll(void);
int nfl2k5_addon_event(const char *name,const void *data,size_t size);
int nfl2k5_addon_snapshot(const char *name,void *out,size_t capacity);
/* True only inside one uninterrupted guest-lock-owned addon invocation. */
int nfl2k5_addon_guest_read_allowed(void);
#endif
