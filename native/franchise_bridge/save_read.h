/* Read evidence only. A candidate is neither a successful load nor a namespace. */
#ifndef FRANCHISE_SAVE_READ_H
#define FRANCHISE_SAVE_READ_H
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#define FRANCHISE_SAVE_READ_SNAPSHOT "franchise.save-read.v2"
#define FRANCHISE_SAVE_BYTES 720044u
/* Owned scalars only; guest_address is a locator, never a retained host pointer. */
typedef struct FranchiseSaveRead {
    uint64_t sequence, file_size, last_write;
    uint32_t volume, file_index_high, file_index_low;
    uint32_t guest_mapped, guest_address;
    char payload_sha256[65];
} FranchiseSaveRead;
/* Same observed FXG roster envelope as inspect_franchise_save.py. This is a
 * cheap candidate filter, deliberately not the full roster/calendar validator. */
static inline int franchise_save_read_shape(const void *bytes,size_t size) {
    if(!bytes || size!=FRANCHISE_SAVE_BYTES) return 0;
    const unsigned char *p=bytes;uint32_t length,count;int32_t start,end;
    memcpy(&length,p+0x2E4,4);memcpy(&count,p+0x320,4);
    memcpy(&start,p+0x324,4);memcpy(&end,p+0x32C,4);
    return !memcmp(p+0x2E0,"ROST",4) && !memcmp(p+0x30C,"ROST",4) &&
        length==0x91020u && count && count<=(0x75C40u-0xB288u)/0x54u &&
        (int64_t)0x324+start-1==0xB288 &&
        (int64_t)0x32C+end-1==0xB288+(int64_t)count*0x54;
}
#endif
