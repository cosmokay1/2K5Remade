/* Production DLL, authored native file and guest memory only. */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include "game_addon.h"
#include "load_read.h"
static unsigned char *payload;
static int readable;
static uint32_t table[3]={FRANCHISE_SAVE_BYTES,0,9};
static void require(int ok){if(!ok)abort();}
static int range(uint32_t address,size_t size){return readable && ((address==0xBDC1CC && size==sizeof(table)) || (address>=0x100000 && (uint64_t)address+size<=0x100000+FRANCHISE_SAVE_BYTES));}
static int read_memory(uint32_t address,void *out,size_t size){
    if(!range(address,size))return 0;
    memcpy(out,address==0xBDC1CC?(const void*)table:payload+address-0x100000,size);return 1;
}
static void put(size_t offset,int32_t value){memcpy(payload+offset,&value,4);}
int wmain(int argc,wchar_t **argv){
    require(argc==2);SetEnvironmentVariableW(L"NFL2K5_FRANCHISE_PROVIDER",NULL);
    HMODULE module=LoadLibraryW(argv[1]);require(module!=NULL);
    NFL2K5AddonQuery query=(NFL2K5AddonQuery)GetProcAddress(module,"nfl2k5_addon_query");require(query!=NULL);
    const NFL2K5AddonAPI *api=query(NFL2K5_ADDON_ABI);require(api!=NULL);
    NFL2K5AddonHost host={sizeof(host),range,read_memory};require(api->start(&host));
    payload=calloc(1,FRANCHISE_SAVE_BYTES);require(payload!=NULL);
    memcpy(payload+0x2E0,"ROST",4);memcpy(payload+0x30C,"ROST",4);
    put(0x2E4,0x91020);put(0x320,1);put(0x324,0xB288-0x324+1);put(0x32C,0xB288+0x54-0x32C+1);
    char root[MAX_PATH],path[MAX_PATH];require(GetTempPathA(MAX_PATH,root)>0 && GetTempFileNameA(root,"ldr",0,path));
    HANDLE file=CreateFileA(path,GENERIC_READ|GENERIC_WRITE,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);require(file!=INVALID_HANDLE_VALUE);
    DWORD count;require(WriteFile(file,payload,FRANCHISE_SAVE_BYTES,&count,NULL) && count==FRANCHISE_SAVE_BYTES);
    FranchiseLoadEvent event={FRANCHISE_LOAD_BEGIN,0x100000,0,0,0x400000};
    NFL2K5AddonFileReadV2 read={0};read.guest_mapped=1;read.guest_address=event.buffer;
    read.read.native_handle=(uintptr_t)file;read.read.bytes=payload;read.read.completed=read.read.requested=FRANCHISE_SAVE_BYTES;
    FranchiseLoadRead state;
    for(unsigned attempt=0;attempt<4;++attempt){
        readable=1;event.stage=FRANCHISE_LOAD_BEGIN;event.offset=0;require(api->event(FRANCHISE_LOAD_EVENT,&event,sizeof(event)));
        readable=0;require(api->event(NFL2K5_ADDON_FILE_READ_V2,&read,sizeof(read)));
        if(attempt==1)require(api->event(NFL2K5_ADDON_FILE_READ_V2,&read,sizeof(read))); /* duplicate */
        if(attempt==2)payload[0x100]^=1; /* same layout, different input bytes */
        readable=attempt!=3;event.stage=FRANCHISE_LOAD_INPUT;require(api->event(FRANCHISE_LOAD_EVENT,&event,sizeof(event)));
        if(attempt==2)payload[0x100]^=1;
        event.stage=FRANCHISE_LOAD_DECODED;event.offset=FRANCHISE_SAVE_BYTES;require(api->event(FRANCHISE_LOAD_EVENT,&event,sizeof(event)));
        require(api->snapshot(FRANCHISE_LOAD_READ_SNAPSHOT,&state,sizeof(state)) && state.epoch==attempt+1);
        require(state.phase==(attempt?FRANCHISE_LOAD_INVALID:FRANCHISE_LOAD_DECODED_SEEN));
        if(!attempt){require(state.source.guest_address==event.buffer && state.source.sequence==1);require(!strcmp(state.source.payload_sha256,"029c7da24320dc1eb2422141a2b6fa777c1f3d276c7fbb709510ecb45b531450"));}
    }
    readable=1;event.stage=FRANCHISE_LOAD_BEGIN;event.offset=0;table[2]=8;require(api->event(FRANCHISE_LOAD_EVENT,&event,sizeof(event)));
    require(api->snapshot(FRANCHISE_LOAD_READ_SNAPSHOT,&state,sizeof(state)) && state.phase==FRANCHISE_LOAD_INVALID);
    api->stop();require(api->start(&host));require(!api->snapshot(FRANCHISE_LOAD_READ_SNAPSHOT,&state,sizeof(state)));api->stop();
    require(CloseHandle(file) && DeleteFileA(path));free(payload);require(FreeLibrary(module));
    puts("PASS: production load read/input/decoded correlation, duplicate/changed/unreadable rejection, restart; no namespace or application grant");return 0;
}
