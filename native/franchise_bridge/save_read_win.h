/* Windows franchise application adapter, outside the generic engine transport. */
#ifndef FRANCHISE_SAVE_READ_WIN_H
#define FRANCHISE_SAVE_READ_WIN_H
#include <windows.h>
#include <bcrypt.h>
#include "save_read.h"
#include "../game_addon/file_read.h"
static inline int franchise_save_read_digest(const void *bytes,size_t size,char out[65]) {
    if(!out || !franchise_save_read_shape(bytes,size))return 0;
    BCRYPT_ALG_HANDLE algorithm=NULL;unsigned char hash[32];
    if(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,NULL,0)!=0)return 0;
    NTSTATUS status=BCryptHash(algorithm,NULL,0,(PUCHAR)bytes,(ULONG)size,hash,sizeof(hash));
    BCryptCloseAlgorithmProvider(algorithm,0);if(status!=0)return 0;
    static const char hex[]="0123456789abcdef";
    for(size_t i=0;i<sizeof(hash);++i){out[i*2]=hex[hash[i]>>4];out[i*2+1]=hex[hash[i]&15];}
    out[64]=0;return 1;
}
static inline int franchise_save_read_capture(const NFL2K5AddonFileReadV2 *located,FranchiseSaveRead *out) {
    if(!located || located->guest_mapped>1 || (!located->guest_mapped && located->guest_address) ||
       (located->guest_mapped && (!located->guest_address ||
        located->read.completed>UINT64_C(0x100000000)-located->guest_address))) return 0;
    const NFL2K5AddonFileRead *event=&located->read;
    if(!event || !out || event->status!=0 || event->completed>event->requested ||
       !franchise_save_read_shape(event->bytes,event->completed)) return 0;
    HANDLE file=(HANDLE)event->native_handle;
    BY_HANDLE_FILE_INFORMATION before,after;
    if(GetFileType(file)!=FILE_TYPE_DISK || !GetFileInformationByHandle(file,&before) ||
       (before.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY) || before.nFileSizeHigh ||
       before.nFileSizeLow!=FRANCHISE_SAVE_BYTES) return 0;
    char digest[65];
    if(!franchise_save_read_digest(event->bytes,event->completed,digest))return 0;
    if(!GetFileInformationByHandle(file,&after) ||
       before.dwVolumeSerialNumber!=after.dwVolumeSerialNumber ||
       before.nFileIndexHigh!=after.nFileIndexHigh || before.nFileIndexLow!=after.nFileIndexLow ||
       before.nFileSizeHigh!=after.nFileSizeHigh || before.nFileSizeLow!=after.nFileSizeLow ||
       memcmp(&before.ftLastWriteTime,&after.ftLastWriteTime,sizeof(FILETIME))) return 0;
    FranchiseSaveRead result={0};
    result.file_size=before.nFileSizeLow;
    result.guest_mapped=located->guest_mapped;result.guest_address=located->guest_address;
    result.last_write=((uint64_t)before.ftLastWriteTime.dwHighDateTime<<32)|before.ftLastWriteTime.dwLowDateTime;
    result.volume=before.dwVolumeSerialNumber;result.file_index_high=before.nFileIndexHigh;result.file_index_low=before.nFileIndexLow;
    memcpy(result.payload_sha256,digest,sizeof(digest));
    *out=result;return 1;
}
#endif
