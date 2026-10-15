#include "read_location.h"
#include <stdlib.h>
static void require(int ok){if(!ok)abort();}
static int range(uint32_t address,size_t size){return address>=0x1000 && (uint64_t)address+size<=0x2000;}
int main(void) {
    uintptr_t base=0x10000;uint32_t address=77;
    require(addon_read_location(base,(void*)(base+0x1000),0x1000,range,&address) && address==0x1000);
    address=77;
    require(!addon_read_location(0,(void*)(base+0x1000),1,range,&address));
    require(!addon_read_location(base,(void*)(base-1),1,range,&address));
    require(!addon_read_location(base,(void*)base,1,range,&address));
    require(!addon_read_location(base,(void*)(base+0x1000),0,range,&address));
    require(!addon_read_location(base,(void*)(base+0x1000),0x1001,range,&address));
    require(!addon_read_location(base,(void*)(base+UINT32_MAX),2,range,&address));
    require(!addon_read_location(base,(void*)(base+0x1000),SIZE_MAX,range,&address));
    require(!addon_read_location(base,(void*)(base+0x1000),1,NULL,&address));
    require(!addon_read_location(base,(void*)(base+0x1000),1,range,NULL));
#if UINTPTR_MAX>UINT32_MAX
    require(!addon_read_location(base,(void*)(base+UINT64_C(0x100000000)),1,range,&address));
#endif
    require(address==77);return 0;
}
