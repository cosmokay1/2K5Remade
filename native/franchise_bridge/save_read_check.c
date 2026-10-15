/* Authored bytes and two real native files; production DLL, no game assets. */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include "game_addon.h"
#include "save_read.h"
#include "../game_addon/file_read.h"
static void require(int ok){if(!ok)abort();}
static int range(uint32_t a,size_t n){(void)a;(void)n;abort();return 0;}
static int read_memory(uint32_t a,void *p,size_t n){(void)a;(void)p;(void)n;abort();return 0;}
static void put(unsigned char *p,size_t offset,int32_t value){memcpy(p+offset,&value,4);}
int wmain(int argc,wchar_t **argv) {
    require(argc==2);SetEnvironmentVariableW(L"NFL2K5_FRANCHISE_PROVIDER",NULL);
    SetEnvironmentVariableW(L"NFL2K5_TRACE_FRANCHISE",NULL);
    HMODULE module=LoadLibraryW(argv[1]);require(module!=NULL);
    NFL2K5AddonQuery query=(NFL2K5AddonQuery)GetProcAddress(module,"nfl2k5_addon_query");require(query!=NULL);
    const NFL2K5AddonAPI *api=query(NFL2K5_ADDON_ABI);require(api!=NULL);
    NFL2K5AddonHost host={sizeof(host),range,read_memory};require(api->start(&host));
    FranchiseSaveRead snapshot={0},previous;
    require(!api->snapshot(FRANCHISE_SAVE_READ_SNAPSHOT,&snapshot,sizeof(snapshot)));
    unsigned char *bytes=calloc(1,FRANCHISE_SAVE_BYTES);require(bytes!=NULL);
    memcpy(bytes+0x2E0,"ROST",4);memcpy(bytes+0x30C,"ROST",4);
    put(bytes,0x2E4,0x91020);put(bytes,0x320,1);put(bytes,0x324,0xB288-0x324+1);put(bytes,0x32C,0xB288+0x54-0x32C+1);
    char root[MAX_PATH],paths[2][MAX_PATH];require(GetTempPathA(MAX_PATH,root)>0);
    for(unsigned i=0;i<2;++i) {
        require(GetTempFileNameA(root,"fxg",0,paths[i])!=0);
        HANDLE file=CreateFileA(paths[i],GENERIC_READ|GENERIC_WRITE,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);require(file!=INVALID_HANDLE_VALUE);
        DWORD count;require(WriteFile(file,bytes,FRANCHISE_SAVE_BYTES,&count,NULL) && count==FRANCHISE_SAVE_BYTES);
        LARGE_INTEGER offset;offset.QuadPart=0;require(SetFilePointerEx(file,offset,NULL,FILE_BEGIN));
        require(ReadFile(file,bytes,FRANCHISE_SAVE_BYTES,&count,NULL) && count==FRANCHISE_SAVE_BYTES);
        NFL2K5AddonFileReadV2 located={0};
        located.read=(NFL2K5AddonFileRead){(uintptr_t)file,bytes,FRANCHISE_SAVE_BYTES,FRANCHISE_SAVE_BYTES,0};
        located.guest_mapped=1;located.guest_address=0x100000;
        NFL2K5AddonFileRead *event=&located.read;
        require(api->event(NFL2K5_ADDON_FILE_READ_V2,&located,sizeof(located)));
        require(api->snapshot(FRANCHISE_SAVE_READ_SNAPSHOT,&snapshot,sizeof(snapshot)) && snapshot.sequence==i+1 && snapshot.file_size==FRANCHISE_SAVE_BYTES);
        require(!strcmp(snapshot.payload_sha256,"029c7da24320dc1eb2422141a2b6fa777c1f3d276c7fbb709510ecb45b531450"));
        BY_HANDLE_FILE_INFORMATION info;require(GetFileInformationByHandle(file,&info));
        require(snapshot.volume==info.dwVolumeSerialNumber && snapshot.file_index_high==info.nFileIndexHigh && snapshot.file_index_low==info.nFileIndexLow);
        if(i) require(snapshot.volume!=previous.volume || snapshot.file_index_high!=previous.file_index_high || snapshot.file_index_low!=previous.file_index_low);
        require(snapshot.guest_mapped==1 && snapshot.guest_address==0x100000);
        previous=snapshot;
        located.guest_mapped=2;require(api->event(NFL2K5_ADDON_FILE_READ_V2,&located,sizeof(located)));
        located.guest_mapped=0;require(api->event(NFL2K5_ADDON_FILE_READ_V2,&located,sizeof(located)));
        located.guest_mapped=1;located.guest_address=UINT32_MAX;
        require(api->event(NFL2K5_ADDON_FILE_READ_V2,&located,sizeof(located)));
        located.guest_address=0x100000;
        /* Rejected deliveries do not relabel the last observed candidate. */
        event->completed--;require(api->event(NFL2K5_ADDON_FILE_READ_V2,&located,sizeof(located)));
        event->completed++;event->status=(int32_t)0xC0000008u;require(api->event(NFL2K5_ADDON_FILE_READ_V2,&located,sizeof(located)));
        event->status=0;event->requested--;require(api->event(NFL2K5_ADDON_FILE_READ_V2,&located,sizeof(located)));
        event->requested++;event->native_handle=(uintptr_t)INVALID_HANDLE_VALUE;require(api->event(NFL2K5_ADDON_FILE_READ_V2,&located,sizeof(located)));
        require(CloseHandle(file));
        require(api->snapshot(FRANCHISE_SAVE_READ_SNAPSHOT,&snapshot,sizeof(snapshot)) && !memcmp(&snapshot,&previous,sizeof(snapshot)));
    }
    memset(bytes,0,FRANCHISE_SAVE_BYTES);free(bytes);
    require(api->snapshot(FRANCHISE_SAVE_READ_SNAPSHOT,&snapshot,sizeof(snapshot)) && !memcmp(&snapshot,&previous,sizeof(snapshot)));
    require(!api->snapshot(FRANCHISE_SAVE_READ_SNAPSHOT,&snapshot,sizeof(snapshot)-1));
    api->stop();require(api->start(&host));require(!api->snapshot(FRANCHISE_SAVE_READ_SNAPSHOT,&snapshot,sizeof(snapshot)) && !snapshot.sequence);
    api->stop();require(FreeLibrary(module));
    require(DeleteFileA(paths[0]) && DeleteFileA(paths[1]));
    puts("PASS: delivered save candidate digest/native identity, rejected reads, owned lifetime and restart; no guest access or load claim");return 0;
}
