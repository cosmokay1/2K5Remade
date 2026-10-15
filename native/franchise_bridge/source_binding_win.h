#ifndef FRANCHISE_SOURCE_BINDING_WIN_H
#define FRANCHISE_SOURCE_BINDING_WIN_H
#include <stdlib.h>
#include "source_binding.h"
#include "save_read_win.h"
/* Compare native identity AND delivered content. Equal bytes in a different
 * container do not select the same franchise. No handle or buffer is retained. */
static int franchise_source_matches_file(const FranchiseSaveRead *source,const wchar_t *path) {
    if(!source || !source->sequence || !path || !*path)return 0;
    HANDLE file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
                            NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
    if(file==INVALID_HANDLE_VALUE)return 0;
    void *bytes=malloc(FRANCHISE_SAVE_BYTES);DWORD count=0;FranchiseSaveRead observed;
    NFL2K5AddonFileReadV2 event={0};event.guest_mapped=source->guest_mapped;event.guest_address=source->guest_address;
    event.read.native_handle=(uintptr_t)file;event.read.bytes=bytes;event.read.requested=FRANCHISE_SAVE_BYTES;
    int ok=bytes && ReadFile(file,bytes,FRANCHISE_SAVE_BYTES,&count,NULL) && count==FRANCHISE_SAVE_BYTES;
    event.read.completed=count;
    ok=ok && franchise_save_read_capture(&event,&observed) &&
        source->volume==observed.volume && source->file_index_high==observed.file_index_high &&
        source->file_index_low==observed.file_index_low && source->file_size==observed.file_size &&
        source->last_write==observed.last_write && !memcmp(source->payload_sha256,observed.payload_sha256,65);
    free(bytes);CloseHandle(file);return ok;
}
#endif
