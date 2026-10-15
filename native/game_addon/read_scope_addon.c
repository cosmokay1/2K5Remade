/* Authored loader boundary fixture, not a distributed gameplay addon. */
#include "api.h"
#include <string.h>
static NFL2K5AddonHost host;
static int start(const NFL2K5AddonHost *value){
    if(!value || value->size!=sizeof(*value) || !value->read_memory) return 0;
    host=*value;return 1;
}
static void stop(void){memset(&host,0,sizeof(host));}
static void poll(void){}
static int event(const char *name,const void *data,size_t size){
    (void)data;(void)size;uint32_t value;
    if(!name || strcmp(name,"scope.read-twice")) return 0;
    int first=host.read_memory(0x1000,&value,sizeof(value));
    int second=host.read_memory(0x1000,&value,sizeof(value));
    return (first?1:0)|(second?2:0);
}
static int snapshot(const char *name,void *out,size_t capacity){
    return name && out && !strcmp(name,"scope.read") && capacity==4 && host.read_memory(0x1000,out,capacity);
}
static const NFL2K5AddonAPI api={sizeof(api),start,stop,poll,event,snapshot};
__declspec(dllexport) const NFL2K5AddonAPI *nfl2k5_addon_query(uint32_t abi){return abi==NFL2K5_ADDON_ABI?&api:NULL;}
