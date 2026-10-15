#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "game_addon.h"
#include "addon_selection.h"
#include "../../src/nfl2k5_sidecar_adapter.h"
#include "../../src/nfl2k5_franchise_host.h"
extern void nfl2k5_modpacks_init(const char *root);
extern int nfl2k5_modpacks_count(void);
extern int nfl2k5_modpacks_get(int row);
extern int nfl2k5_modpacks_toggle(int row);
extern void nfl2k5_modpacks_set(int row,int on);
extern void nfl2k5_modpacks_value(int row,int value,char *out,size_t capacity);
static unsigned toasts;
void xbox_PresentToast(const char *header,const char *line1,const char *line2,unsigned ms) {
    (void)header;(void)line1;(void)line2;(void)ms;++toasts;
}
int nfl2k5_addon_guest_range(uint32_t address,size_t size) { (void)address;(void)size;return 0; }
int nfl2k5_addon_guest_read(uint32_t address,void *out,size_t size) {
    (void)address;(void)out;(void)size;return 0;
}
int wmain(int argc,wchar_t **argv) {
    if(argc!=3) return 1;
    _wputenv_s(L"NFL2K5_FRANCHISE_PROVIDER",L"");
    SetEnvironmentVariableW(L"NFL2K5_TRACE_FRANCHISE",NULL);
    wchar_t installed[32768],selection[32768],folder[32768];
    if(!sidecar_path(installed,32768,L"franchise-addon.dll") ||
       !sidecar_path(selection,32768,L"enabled.ini")) return 12;
    DWORD length=GetModuleFileNameW(NULL,folder,32768);
    if(!length || length>=32768) return 13;
    *wcsrchr(folder,L'\\')=0;wcscat(folder,L"\\addons");CreateDirectoryW(folder,NULL);
    wcscat(folder,L"\\franchise");CreateDirectoryW(folder,NULL);
    if(!CopyFileW(argv[1],installed,FALSE)) return 14;
    DeleteFileW(selection);
    if(sidecar_selected() || !nfl2k5_franchise_start()) return 15;
    nfl2k5_franchise_stop();
    FILE *malformed=_wfopen(selection,L"wb");if(!malformed) return 28;
    fputs("enabled=1\ntrailing",malformed);fclose(malformed);
    if(sidecar_selected() || !nfl2k5_franchise_start()) return 29;
    nfl2k5_franchise_stop();
    char temporary[MAX_PATH],root[MAX_PATH],path[MAX_PATH],value[64];
    if(!GetTempPathA(MAX_PATH,temporary) || !GetTempFileNameA(temporary,"mod",0,root)) return 18;
    DeleteFileA(root);CreateDirectoryA(root,NULL);
    snprintf(path,sizeof(path),"%s\\mods",root);CreateDirectoryA(path,NULL);
    snprintf(path,sizeof(path),"%s\\mods\\packs",root);CreateDirectoryA(path,NULL);
    snprintf(path,sizeof(path),"%s\\mods\\packs\\Fixture",root);CreateDirectoryA(path,NULL);
    snprintf(path,sizeof(path),"%s\\mods\\packs\\Fixture\\pack.json",root);
    FILE *file=fopen(path,"wb");if(!file) return 19;fputs("{\"name\":\"Fixture\"}",file);fclose(file);
    snprintf(path,sizeof(path),"%s\\mods\\packs\\Fixture\\default.xbe",root);
    file=fopen(path,"wb");if(!file) return 20;fputs("synthetic marker, not a game",file);fclose(file);
    snprintf(path,sizeof(path),"%s\\mods\\active-pack.ini",root);
    file=fopen(path,"wb");if(!file) return 21;fputs("Fixture\n",file);fclose(file);
    nfl2k5_modpacks_init(root);
    if(nfl2k5_modpacks_count()!=2 || !nfl2k5_modpacks_toggle(0) || !nfl2k5_modpacks_get(1)) return 22;
    nfl2k5_modpacks_set(0,1);
    if(!sidecar_selected() || !nfl2k5_modpacks_get(0) || !nfl2k5_modpacks_get(1) || toasts!=1) return 16;
    nfl2k5_modpacks_value(0,1,value,sizeof(value));
    if(strcmp(value,"On - restart")) return 23;
    file=fopen(path,"rb");if(!file) return 24;
    char active[32]={0};fgets(active,sizeof(active),file);fclose(file);
    if(strcmp(active,"Fixture\n")) return 25;
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
    nfl2k5_modpacks_set(0,0);
    if(sidecar_selected() || !nfl2k5_franchise_start() || !nfl2k5_modpacks_get(1)) return 17;
    nfl2k5_franchise_stop();
    DeleteFileW(installed);DeleteFileW(selection);
    if(nfl2k5_modpacks_toggle(0) || sidecar_select(1)) return 26;
    nfl2k5_modpacks_value(0,0,value,sizeof(value));
    if(strcmp(value,"Not installed")) return 27;
    /* Let the existing empty patch-folder scan finish before fixture cleanup. */
    Sleep(50);
    snprintf(path,sizeof(path),"%s\\mods\\packs\\Fixture\\pack.json",root);DeleteFileA(path);
    snprintf(path,sizeof(path),"%s\\mods\\packs\\Fixture\\default.xbe",root);DeleteFileA(path);
    snprintf(path,sizeof(path),"%s\\mods\\packs\\Fixture",root);RemoveDirectoryA(path);
    snprintf(path,sizeof(path),"%s\\mods\\active-pack.ini",root);DeleteFileA(path);
    snprintf(path,sizeof(path),"%s\\mods\\packs",root);RemoveDirectoryA(path);
    snprintf(path,sizeof(path),"%s\\mods\\patches",root);RemoveDirectoryA(path);
    snprintf(path,sizeof(path),"%s\\mods",root);RemoveDirectoryA(path);RemoveDirectoryA(root);
    puts("Loadable addon ABI, forwarding, disabled-service and reload checks passed");
    return 0;
}
