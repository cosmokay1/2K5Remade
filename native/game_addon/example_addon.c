/* Asset-free ABI example: an in-process counter, no franchise or AI headers. */
#include "api.h"
#include <string.h>
static uint32_t counter;
static int start(const NFL2K5AddonHost *host) {
    if(!host || host->size!=sizeof(*host) || !host->memory_range || !host->read_memory) return 0;
    counter=0;return 1;
}
static void stop(void) { counter=0; }
static void poll(void) { ++counter; }
static int event(const char *name,const void *data,size_t size) {
    if(!name || !data || strcmp(name,"example.counter.v1") || size!=sizeof(counter)) return 0;
    memcpy(&counter,data,sizeof(counter));return 1;
}
static int snapshot(const char *name,void *out,size_t capacity) {
    if(!name || !out || strcmp(name,"example.counter.v1") || capacity!=sizeof(counter)) return 0;
    memcpy(out,&counter,sizeof(counter));return 1;
}
static const NFL2K5AddonAPI api={sizeof(NFL2K5AddonAPI),start,stop,poll,event,snapshot};
__declspec(dllexport) const NFL2K5AddonAPI *nfl2k5_addon_query(uint32_t abi) {
    return abi==NFL2K5_ADDON_ABI?&api:NULL;
}
