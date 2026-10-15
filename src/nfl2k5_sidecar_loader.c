/* Thin host shim. Application behavior lives in a separately loaded DLL. */
#include <stdint.h>
#include "../native/game_addon/loader.h"
#ifdef NFL2K5_FRANCHISE_CLIENT
#include <windows.h>
#include <stdio.h>
#include <wchar.h>
#include "game_addon.h"
#include "addon_selection.h"
#include "../native/game_addon/read_scope.h"
#include "../native/game_addon/runtime_identity.h"
#include "../native/game_addon/file_read.h"
#include "../external/xboxrecomp/src/kernel/file_read_observer.h"
extern uint64_t xbox_ggl_current_serial(void);
#if defined(_MSC_VER)
static __declspec(thread) NFL2K5AddonReadScope read_scope;
#else
static _Thread_local NFL2K5AddonReadScope read_scope;
#endif
int nfl2k5_addon_guest_read_allowed(void) {
    return addon_read_allowed(&read_scope,xbox_ggl_current_serial());
}
extern int nfl2k5_addon_guest_range(uint32_t,size_t);
extern int nfl2k5_addon_guest_read(uint32_t,void *,size_t);
static SRWLOCK module_lock=SRWLOCK_INIT;
static HMODULE module;
static const NFL2K5AddonAPI *api;
static NFL2K5AddonImageIdentity loaded_image;
int nfl2k5_addon_bind_image(const char *sha256) {
    NFL2K5AddonImageIdentity next;
    const int valid=addon_image_identity(&next,sha256);
    AcquireSRWLockExclusive(&module_lock);
    int bound=valid;
    if(api) bound=valid && !memcmp(&next,&loaded_image,sizeof(next));
    else loaded_image=next;
    ReleaseSRWLockExclusive(&module_lock);
    return bound;
}
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
    if(!api || api->size!=sizeof(*api) || !api->start || !api->stop || !api->event ||
       !api->poll || !api->snapshot) {
        api=NULL;FreeLibrary(module);module=NULL;return 0;
    }
    const NFL2K5AddonHost host={sizeof(NFL2K5AddonHost),nfl2k5_addon_guest_range,nfl2k5_addon_guest_read};
    addon_read_begin(&read_scope,xbox_ggl_current_serial());
    int started=api->start(&host);
    addon_read_end(&read_scope);
    if(!started) {
        addon_read_begin(&read_scope,xbox_ggl_current_serial());api->stop();addon_read_end(&read_scope);
        api=NULL;FreeLibrary(module);module=NULL;return 0;
    }
    if(loaded_image.sha256[0]) {
        addon_read_begin(&read_scope,xbox_ggl_current_serial());
        /* Optional metadata: older/other addons may ignore it. */
        api->event(NFL2K5_ADDON_LOADED_IMAGE,&loaded_image,sizeof(loaded_image));
        addon_read_end(&read_scope);
    }
    return 1;
}
int nfl2k5_addon_start(void) {
    AcquireSRWLockExclusive(&module_lock);
    int started=load_addon();
    ReleaseSRWLockExclusive(&module_lock);
    return started;
}
void nfl2k5_addon_stop(void) {
    AcquireSRWLockExclusive(&module_lock);
    if(api) {
        addon_read_begin(&read_scope,xbox_ggl_current_serial());api->stop();addon_read_end(&read_scope);
    }
    api=NULL;
    if(module) FreeLibrary(module);
    module=NULL;
    ReleaseSRWLockExclusive(&module_lock);
}
int nfl2k5_sidecar_loaded(void) {
    AcquireSRWLockShared(&module_lock);
    int loaded=api!=NULL;
    ReleaseSRWLockShared(&module_lock);
    return loaded;
}
void nfl2k5_addon_poll(void) {
    AcquireSRWLockShared(&module_lock);
    if(api) {
        addon_read_begin(&read_scope,xbox_ggl_current_serial());api->poll();addon_read_end(&read_scope);
    }
    ReleaseSRWLockShared(&module_lock);
}
int nfl2k5_addon_event(const char *name,const void *data,size_t size) {
    AcquireSRWLockShared(&module_lock);
    int handled=0;
    if(api && name && data && strcmp(name,NFL2K5_ADDON_LOADED_IMAGE)) {
        addon_read_begin(&read_scope,xbox_ggl_current_serial());
        handled=api->event(name,data,size);addon_read_end(&read_scope);
    }
    ReleaseSRWLockShared(&module_lock);
    return handled;
}
void nfl2k5_addon_file_read(const XboxFileReadEvent *read) {
    if(!read) return;
    const NFL2K5AddonFileRead event={read->native_handle,read->bytes,read->requested,read->completed,read->status};
    nfl2k5_addon_event(NFL2K5_ADDON_FILE_READ,&event,sizeof(event));
}
int nfl2k5_addon_snapshot(const char *name,void *out,size_t capacity) {
    AcquireSRWLockShared(&module_lock);
    int shown=0;
    if(api && name && out) {
        addon_read_begin(&read_scope,xbox_ggl_current_serial());
        shown=api->snapshot(name,out,capacity);addon_read_end(&read_scope);
    }
    ReleaseSRWLockShared(&module_lock);
    return shown;
}
#endif
