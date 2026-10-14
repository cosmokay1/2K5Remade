#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include "game_addon.h"
#include "../../src/nfl2k5_sidecar_adapter.h"
#include "../../src/nfl2k5_franchise_host.h"
int nfl2k5_addon_guest_range(uint32_t address,size_t size) { (void)address;(void)size;return 0; }
int nfl2k5_addon_guest_read(uint32_t address,void *out,size_t size) {
    (void)address;(void)out;(void)size;return 0;
}
int wmain(int argc,wchar_t **argv) {
    if(argc!=3) return 1;
    _wputenv_s(L"NFL2K5_FRANCHISE_PROVIDER",L"");
    SetEnvironmentVariableW(L"NFL2K5_TRACE_FRANCHISE",NULL);
    SetEnvironmentVariableW(L"NFL2K5_SIDECAR_ADDON",L"relative.dll");
    if(nfl2k5_franchise_start()) return 2;
    SetEnvironmentVariableW(L"NFL2K5_SIDECAR_ADDON",L"C:\\missing-sidecar-fixture\\addon.dll");
    if(nfl2k5_franchise_start()) return 10;
    SetEnvironmentVariableW(L"NFL2K5_SIDECAR_ADDON",argv[2]);
    if(nfl2k5_franchise_start()) return 11;
    if(!SetEnvironmentVariableW(L"NFL2K5_SIDECAR_ADDON",argv[1])) return 3;
    HMODULE dll=LoadLibraryW(argv[1]);
    if(!dll) return 4;
    NFL2K5AddonQuery query=(NFL2K5AddonQuery)GetProcAddress(dll,"nfl2k5_addon_query");
    if(!query || query(0) || !query(NFL2K5_ADDON_ABI)) return 5;
    const NFL2K5AddonAPI *api=query(NFL2K5_ADDON_ABI);
    NFL2K5AddonHost bad={0,nfl2k5_addon_guest_range,nfl2k5_addon_guest_read};
    if(api->start(&bad) || api->start(NULL)) return 6;
    FreeLibrary(dll);
    for(int cycle=0;cycle<2;++cycle) {
        if(!nfl2k5_franchise_start() || nfl2k5_franchise_start()) return 7;
        nfl2k5_diag_fsm(0,0x557B2C,1);
        nfl2k5_franchise_guest_poll();
        nfl2k5_diag_signing(0,0,0,0,0);
        FranchiseSigningDisplay display={0};
        if(nfl2k5_franchise_display(&display)) return 8;
        nfl2k5_franchise_stop();nfl2k5_franchise_stop();
        if(nfl2k5_franchise_display(&display)) return 9;
    }
    puts("Loadable addon ABI, forwarding, disabled-service and reload checks passed");
    return 0;
}
