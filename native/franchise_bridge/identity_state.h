/* Application-private sampled roster identities, not a transaction or grant. */
#ifndef NFL2K5_IDENTITY_STATE_H
#define NFL2K5_IDENTITY_STATE_H
#include "finance_state.h"
#define FRANCHISE_IDENTITY_SNAPSHOT "franchise.identity-state.v1"
#define FRANCHISE_IDENTITY_HEADER 12u
#define FRANCHISE_IDENTITY_RECORD 211u
/* Allocate on the heap: the expanded-bank bound exceeds a Windows stack. */
typedef struct FranchiseIdentitySnapshot {
    uint32_t size;
    unsigned char bytes[FRANCHISE_IDENTITY_HEADER+FRANCHISE_IDENTITY_RECORD*FRANCHISE_FINANCE_MAX_PLAYERS];
} FranchiseIdentitySnapshot;
static int identity_name(const NFL2K5AddonHost *host,uint32_t pointer,unsigned char *out) {
    int surrogate=0;
    if(!pointer || pointer%2) return 0;
    for(uint32_t i=0;i<50;++i) {
        unsigned char raw[2];uint64_t location=(uint64_t)pointer+2*i;
        if(location>UINT32_MAX || !finance_read(host,(uint32_t)location,raw,2)) return 0;
        uint32_t ch=(uint32_t)raw[0]|((uint32_t)raw[1]<<8);
        if(!ch) return i!=0 && !surrogate;
        if(ch<32) return 0;
        if(ch>=0xD800 && ch<=0xDBFF) {if(surrogate) return 0;surrogate=1;}
        else if(ch>=0xDC00 && ch<=0xDFFF) {if(!surrogate) return 0;surrogate=0;}
        else if(surrogate) return 0;
        memcpy(out+2*i,raw,2);
    }
    return 0; /* bounded names require a terminator */
}
static int franchise_identity_capture(const NFL2K5AddonHost *host,const FranchiseFinanceSnapshot *finance,
                                      FranchiseIdentitySnapshot *out) {
    unsigned char root[4],header[8],check[8];uint32_t bank,base,count,members=0;
    if(!out) return 0;
    memset(out,0,sizeof(*out));
    if(!host || host->size!=sizeof(*host) || !host->memory_range || !host->read_memory || !finance ||
       finance->size<FRANCHISE_FINANCE_HEADER || finance->size>sizeof(finance->bytes) ||
       finance_get32(finance->bytes)!=1 || !(count=finance_get32(finance->bytes+4)) || count>FRANCHISE_FINANCE_MAX_PLAYERS ||
       finance->size!=FRANCHISE_FINANCE_HEADER+FRANCHISE_FINANCE_RECORD*count ||
       !finance_read(host,0xB72918u,root,4) || !(bank=finance_get32(root)) ||
       !finance_read(host,bank,header,8) || finance_get32(header)!=count || !(base=finance_get32(header+4)) ||
       (uint64_t)base+(uint64_t)count*0x54u>UINT64_C(0x100000000) ||
       !host->memory_range(base,(size_t)count*0x54u)) return 0;
    for(uint32_t slot=0;slot<count;++slot) {
        uint32_t owner=finance_get32(finance->bytes+FRANCHISE_FINANCE_HEADER+slot*FRANCHISE_FINANCE_RECORD+7);
        if(owner==UINT32_MAX) continue; /* no persistent actor binding in this bank slot */
        if(owner>32) return 0;
        unsigned char record[0x28],again[0x28];
        unsigned char *destination=out->bytes+FRANCHISE_IDENTITY_HEADER+members*FRANCHISE_IDENTITY_RECORD;
        if(!finance_read(host,base+slot*0x54u,record,sizeof(record))) return 0;
        finance_put32(destination,slot);memcpy(destination+4,record+4,4);memcpy(destination+8,record+0x19,3);
        if(!identity_name(host,finance_get32(record+0x10),destination+11) ||
           !identity_name(host,finance_get32(record+0x14),destination+111) ||
           !finance_read(host,base+slot*0x54u,again,sizeof(again)) ||
           memcmp(record+4,again+4,4) || memcmp(record+0x19,again+0x19,3) || memcmp(record+0x10,again+0x10,8)) return 0;
        ++members;
    }
    if(!finance_read(host,0xB72918u,check,4) || memcmp(root,check,4) ||
       !finance_read(host,bank,check,8) || memcmp(header,check,8)) return 0;
    finance_put32(out->bytes,1);finance_put32(out->bytes+4,count);finance_put32(out->bytes+8,members);
    out->size=FRANCHISE_IDENTITY_HEADER+members*FRANCHISE_IDENTITY_RECORD;
    return 1;
}
#endif
