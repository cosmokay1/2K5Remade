/* Authored loader boundary fixture, not a distributed gameplay addon. */
#include "api.h"
#include "file_read.h"
#include <string.h>
static NFL2K5AddonHost host;
static uint32_t file_read_permission;
static int start(const NFL2K5AddonHost *value){
    if(!value || value->size!=sizeof(*value) || !value->read_memory) return 0;
    host=*value;file_read_permission=0;return 1;
}
static void stop(void){memset(&host,0,sizeof(host));file_read_permission=0;}
static void poll(void){}
static int event(const char *name,const void *data,size_t size){
    (void)data;(void)size;uint32_t value;
    if(name && !strcmp(name,NFL2K5_ADDON_FILE_READ)) {
        file_read_permission=host.read_memory(0x1000,&value,sizeof(value))?1:0;return 1;
    }
    if(!name || strcmp(name,"scope.read-twice")) return 0;
    int first=host.read_memory(0x1000,&value,sizeof(value));
    int second=host.read_memory(0x1000,&value,sizeof(value));
    return (first?1:0)|(second?2:0);
}
static int snapshot(const char *name,void *out,size_t capacity){
    if(name && out && !strcmp(name,"scope.file-read-permission") && capacity==sizeof(file_read_permission)) {
        memcpy(out,&file_read_permission,sizeof(file_read_permission));return 1;
    }
    return name && out && !strcmp(name,"scope.read") && capacity==4 && host.read_memory(0x1000,out,capacity);
}
static const NFL2K5AddonAPI api={sizeof(api),start,stop,poll,event,snapshot};
__declspec(dllexport) const NFL2K5AddonAPI *nfl2k5_addon_query(uint32_t abi){return abi==NFL2K5_ADDON_ABI?&api:NULL;}
