#ifndef NFL2K5_ADDON_LOADER_H
#define NFL2K5_ADDON_LOADER_H
#include <stddef.h>
int nfl2k5_addon_start(void);
void nfl2k5_addon_stop(void);
int nfl2k5_sidecar_loaded(void);
void nfl2k5_addon_poll(void);
int nfl2k5_addon_event(const char *name,const void *data,size_t size);
int nfl2k5_addon_snapshot(const char *name,void *out,size_t capacity);
#endif
