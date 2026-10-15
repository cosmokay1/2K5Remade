#ifndef NFL2K5_ADDON_SELECTION_H
#define NFL2K5_ADDON_SELECTION_H
#include <windows.h>
#include <stdio.h>
#include <wchar.h>
#include <string.h>
/* Selection belongs to this installed executable, independent of content pack. */
static int sidecar_path(wchar_t *out,size_t capacity,const wchar_t *leaf) {
    DWORD size=GetModuleFileNameW(NULL,out,(DWORD)capacity);
    if(!size || size>=capacity) return 0;
    wchar_t *slash=wcsrchr(out,L'\\');
    if(!slash) return 0;
    *slash=0;
    const wchar_t suffix[]=L"\\addons\\franchise\\";
    if(wcslen(out)+wcslen(suffix)+wcslen(leaf)>=capacity) return 0;
    wcscat(out,suffix);wcscat(out,leaf);return 1;
}
static int sidecar_selected(void) {
    wchar_t path[32768];char text[16]={0};
    if(!sidecar_path(path,32768,L"enabled.ini")) return 0;
    FILE *file=_wfopen(path,L"rb");
    if(!file) return 0;
    size_t size=fread(text,1,sizeof(text),file);int valid=!ferror(file);
    fclose(file);
    return valid && size==10 && !memcmp(text,"enabled=1\n",10);
}
static int sidecar_installed(void) {
    wchar_t path[32768];
    if(!sidecar_path(path,32768,L"franchise-addon.dll")) return 0;
    DWORD attributes=GetFileAttributesW(path);
    return attributes!=INVALID_FILE_ATTRIBUTES && !(attributes&FILE_ATTRIBUTE_DIRECTORY);
}
static int sidecar_select(int enabled) {
    wchar_t path[32768],temporary[32768];
    if(!sidecar_path(path,32768,L"enabled.ini") ||
       !sidecar_path(temporary,32768,L"enabled.ini.tmp")) return 0;
    if(enabled && !sidecar_installed()) return 0;
    FILE *file=_wfopen(temporary,L"wb");
    if(!file) return 0;
    int written=fputs(enabled?"enabled=1\n":"enabled=0\n",file)>=0;
    int closed=fclose(file)==0;
    if(!written || !closed || !MoveFileExW(temporary,path,MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)) {
        DeleteFileW(temporary);return 0;
    }
    return 1;
}
#endif
