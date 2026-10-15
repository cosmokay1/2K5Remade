/* Thin host shim. Application behavior lives in a separately loaded DLL. */
#include <stdint.h>
#include "nfl2k5_sidecar_adapter.h"
#ifdef NFL2K5_FRANCHISE_CLIENT
#include <windows.h>
#include <stdio.h>
#include <wchar.h>
#include "nfl2k5_franchise_host.h"
#include "game_addon.h"
#include "addon_selection.h"
extern int nfl2k5_addon_guest_range(uint32_t,size_t);
extern int nfl2k5_addon_guest_read(uint32_t,void *,size_t);
static SRWLOCK display_lock=SRWLOCK_INIT;
static HMODULE module;
static const NFL2K5AddonAPI *api;
static int load_addon(void) {
    if(module) return 0;
    if(!sidecar_selected()) return 1;
    wchar_t path[32768];
    DWORD length=GetEnvironmentVariableW(L"NFL2K5_SIDECAR_ADDON",path,32768);
    if(length>=32768) return 0;
    const int explicit_path=length!=0;
    if(!length) {
        if(!sidecar_path(path,32768,L"franchise-addon.dll")) return 0;
    }
    /* Require an absolute path; never search the working directory or PATH. */
    if(!((path[0] && path[1]==L':' && (path[2]==L'\\' || path[2]==L'/')) ||
         (path[0]==L'\\' && path[1]==L'\\'))) return 0;
    if(!explicit_path && GetFileAttributesW(path)==INVALID_FILE_ATTRIBUTES) {
        DWORD error=GetLastError();
        if(error==ERROR_FILE_NOT_FOUND || error==ERROR_PATH_NOT_FOUND) return 1;
    }
    module=LoadLibraryExW(path,NULL,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
    if(!module) { fprintf(stderr,"[SIDECAR] Addon load failed (%lu).\n",(unsigned long)GetLastError());return 0; }
    NFL2K5AddonQuery query=(NFL2K5AddonQuery)GetProcAddress(module,"nfl2k5_addon_query");
    api=query?query(NFL2K5_ADDON_ABI):NULL;
    if(!api || api->size!=sizeof(*api) || !api->start || !api->stop || !api->fsm ||
       !api->poll || !api->signing || !api->display) {
        api=NULL;FreeLibrary(module);module=NULL;return 0;
    }
    const NFL2K5AddonHost host={sizeof(NFL2K5AddonHost),nfl2k5_addon_guest_range,nfl2k5_addon_guest_read};
    if(!api->start(&host)) { api->stop();api=NULL;FreeLibrary(module);module=NULL;return 0; }
    return 1;
}
int nfl2k5_franchise_start(void) {
    AcquireSRWLockExclusive(&display_lock);
    int started=load_addon();
    ReleaseSRWLockExclusive(&display_lock);
    return started;
}
void nfl2k5_franchise_stop(void) {
    AcquireSRWLockExclusive(&display_lock);
    if(api) api->stop();
    api=NULL;
    if(module) FreeLibrary(module);
    module=NULL;
    ReleaseSRWLockExclusive(&display_lock);
}
int nfl2k5_sidecar_loaded(void) {
    AcquireSRWLockShared(&display_lock);
    int loaded=api!=NULL;
    ReleaseSRWLockShared(&display_lock);
    return loaded;
}
void nfl2k5_franchise_guest_poll(void) { if(api) api->poll(); }
int nfl2k5_franchise_display(FranchiseSigningDisplay *out) {
    AcquireSRWLockShared(&display_lock);
    int shown=api ? api->display(out) : 0;
    ReleaseSRWLockShared(&display_lock);
    return shown;
}
#endif
void nfl2k5_diag_fsm(uint32_t object,uint32_t descriptor,int push) {
#ifdef NFL2K5_FRANCHISE_CLIENT
    if(api) api->fsm(object,descriptor,push);
#else
    (void)object;(void)descriptor;(void)push;
#endif
}
void nfl2k5_diag_signing(uint32_t stage,uint32_t context,uint32_t result,uint32_t code,uint32_t stack) {
#ifdef NFL2K5_FRANCHISE_CLIENT
    if(api) api->signing(stage,context,result,code,stack);
#else
    (void)stage;(void)context;(void)result;(void)code;(void)stack;
#endif
}
