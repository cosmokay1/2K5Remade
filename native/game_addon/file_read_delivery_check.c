/* Authored temporary file only: actual kernel -> host loader -> example DLL. */
#include "kernel.h"
#include "file_read_observer.h"
#include "loader.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>
void *recomp_lookup(ULONG a){(void)a;abort();}
void *recomp_lookup_manual(ULONG a){(void)a;abort();}
int nfl2k5_addon_guest_range(uint32_t a,size_t n){(void)a;(void)n;return 0;}
int nfl2k5_addon_guest_read(uint32_t a,void *p,size_t n){(void)a;(void)p;(void)n;return 0;}
static BY_HANDLE_FILE_INFORMATION source;
static unsigned reads;
static void require(int ok){if(!ok)abort();}
static void forward(const XboxFileReadEvent *event){
    BY_HANDLE_FILE_INFORMATION actual;
    require(GetFileInformationByHandle((HANDLE)event->native_handle,&actual));
    require(actual.dwVolumeSerialNumber==source.dwVolumeSerialNumber &&
        actual.nFileIndexHigh==source.nFileIndexHigh && actual.nFileIndexLow==source.nFileIndexLow);
    ++reads;nfl2k5_addon_file_read(event);
}
int wmain(int argc,wchar_t **argv){
    require(argc==2);
    wchar_t folder[32768],selection[32768];
    DWORD n=GetModuleFileNameW(NULL,folder,32768);require(n && n<32768);
    *wcsrchr(folder,L'\\')=0;wcscat(folder,L"\\addons");CreateDirectoryW(folder,NULL);
    wcscat(folder,L"\\franchise");CreateDirectoryW(folder,NULL);
    wcscpy(selection,folder);wcscat(selection,L"\\enabled.ini");
    require(GetFileAttributesW(selection)==INVALID_FILE_ATTRIBUTES);
    FILE *enabled=_wfopen(selection,L"wb");require(enabled!=NULL);
    require(fputs("enabled=1\n",enabled)>=0 && fclose(enabled)==0);
    SetEnvironmentVariableW(L"NFL2K5_SIDECAR_ADDON",argv[1]);
    require(nfl2k5_addon_start());
    char root[MAX_PATH],path[MAX_PATH];require(GetTempPathA(MAX_PATH,root)>0);
    snprintf(path,sizeof(path),"%saddon-read-%lu.dat",root,(unsigned long)GetCurrentProcessId());
    HANDLE file=CreateFileA(path,GENERIC_READ|GENERIC_WRITE,FILE_SHARE_READ,NULL,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,NULL);
    require(file!=INVALID_HANDLE_VALUE && GetFileInformationByHandle(file,&source));
    DWORD wrote;require(WriteFile(file,"abcde",5,&wrote,NULL) && wrote==5);
    xbox_SetFileReadObserver(forward);
    LARGE_INTEGER offset;offset.QuadPart=0;XBOX_IO_STATUS_BLOCK io;char bytes[8];
    require(xbox_NtReadFile(file,NULL,NULL,NULL,&io,bytes,3,&offset)==STATUS_SUCCESS && io.Information==3 && !memcmp(bytes,"abc",3));
    uint64_t count=0;require(reads==1 && nfl2k5_addon_snapshot("example.read-bytes.v1",&count,sizeof(count)) && count==3);
    require(!nfl2k5_addon_guest_read_allowed());
    offset.QuadPart=4;require(xbox_NtReadFile(file,NULL,NULL,NULL,&io,bytes,8,&offset)==STATUS_SUCCESS && io.Information==1);
    require(reads==2 && nfl2k5_addon_snapshot("example.read-bytes.v1",&count,sizeof(count)) && count==4);
    offset.QuadPart=5;require(xbox_NtReadFile(file,NULL,NULL,NULL,&io,bytes,8,&offset)==STATUS_END_OF_FILE);
    require(reads==3 && nfl2k5_addon_snapshot("example.read-bytes.v1",&count,sizeof(count)) && count==4);
    xbox_SetFileReadObserver(NULL);nfl2k5_addon_stop();
    CloseHandle(file);require(DeleteFileA(path));require(DeleteFileW(selection));
    puts("PASS: actual native file identity and bytes through kernel observer, host loader and DLL; no guest authority");return 0;
}
