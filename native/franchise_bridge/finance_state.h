/* Application-private, read-only league financial comparison. No write grant.
 * The owner must quiesce guest mutations before relying on a comparison; two
 * equal reads alone cannot establish transaction ownership or authorization.
 */
#ifndef NFL2K5_FINANCE_STATE_H
#define NFL2K5_FINANCE_STATE_H
#include "game_addon.h"
#include <string.h>
#define FRANCHISE_FINANCE_SNAPSHOT "franchise.finance-state.v1"
/* Same observed bank ceiling as inspect_franchise_save, not a retail constant. */
#define FRANCHISE_FINANCE_MAX_PLAYERS 5198u
#define FRANCHISE_FINANCE_HEADER 432u
#define FRANCHISE_FINANCE_RECORD 11u
typedef struct FranchiseFinanceSnapshot {
    uint32_t size;
    unsigned char bytes[FRANCHISE_FINANCE_HEADER + FRANCHISE_FINANCE_RECORD * FRANCHISE_FINANCE_MAX_PLAYERS];
} FranchiseFinanceSnapshot;
static void finance_put32(unsigned char *out,uint32_t value) {
    for(unsigned i=0;i<4;++i) out[i]=(unsigned char)(value>>(8*i));
}
static uint32_t finance_get32(const unsigned char *in) {
    return (uint32_t)in[0]|((uint32_t)in[1]<<8)|((uint32_t)in[2]<<16)|((uint32_t)in[3]<<24);
}
static int finance_read(const NFL2K5AddonHost *host,uint32_t address,void *out,size_t size) {
    return address && (uint64_t)address+size<=UINT64_C(0x100000000) &&
        host->memory_range(address,size) && host->read_memory(address,out,size);
}
static int finance_member(const NFL2K5AddonHost *host,FranchiseFinanceSnapshot *out,
                          uint32_t table,uint32_t count,uint32_t owner,uint32_t base,uint32_t players) {
    if(count>players || (count && !table)) return 0;
    for(uint32_t i=0;i<count;++i) {
        unsigned char raw[4];uint32_t pointer,slot;uint64_t location=(uint64_t)table+4u*i;
        if(location>UINT32_MAX || !finance_read(host,(uint32_t)location,raw,4)) return 0;
        pointer=finance_get32(raw);
        if(pointer<base || (pointer-base)%0x54u || (slot=(pointer-base)/0x54u)>=players) return 0;
        unsigned char *destination=out->bytes+FRANCHISE_FINANCE_HEADER+slot*FRANCHISE_FINANCE_RECORD+7;
        if(finance_get32(destination)!=UINT32_MAX) return 0; /* duplicate across any roster */
        finance_put32(destination,owner);
    }
    return 1;
}
static int franchise_finance_capture(const NFL2K5AddonHost *host,FranchiseFinanceSnapshot *out) {
    unsigned char root[4],header[8],calendar[28],teams[128],mode[4],cap[4],free_header[8],raw[4];
    uint32_t bank,players,base;
    if(!out) return 0;
    memset(out,0,sizeof(*out)); /* failures never leave a valid-looking size */
    if(!host || host->size!=sizeof(*host) || !host->memory_range || !host->read_memory ||
       !finance_read(host,0xB72918u,root,4) || !(bank=finance_get32(root)) ||
       !finance_read(host,bank,header,8) || !(players=finance_get32(header)) ||
       players>FRANCHISE_FINANCE_MAX_PLAYERS || !(base=finance_get32(header+4)) ||
       (uint64_t)base+(uint64_t)players*0x54u>UINT64_C(0x100000000) ||
       !host->memory_range(base,(size_t)players*0x54u) || bank>UINT32_MAX-0x40u ||
       !finance_read(host,0xE576A0u,mode,4) || finance_get32(mode)!=2 ||
       !finance_read(host,0xE576A4u,calendar,28) || finance_get32(calendar+8)!=32 ||
       !finance_read(host,0xE5786Cu,teams,128) ||
       !finance_read(host,0xE3C278u,cap,4) || !finance_get32(cap) || finance_get32(cap)>INT32_MAX ||
       !finance_read(host,bank+0x38u,free_header,8)) return 0;
    for(unsigned i=0;i<7;++i)
        if(finance_get32(calendar+4*i)>(i==2?32u:i==6?65535u:255u)) return 0;
    /* Little-endian v1, bank count, mode, raw cap, seven calendar words. */
    finance_put32(out->bytes,1);finance_put32(out->bytes+4,players);
    memcpy(out->bytes+8,mode,4);memcpy(out->bytes+12,cap,4);memcpy(out->bytes+16,calendar,28);
    /* Four-byte reserved zero after calendar, then 32 payroll/flag/accumulator triples. */
    for(uint32_t i=0;i<players;++i) {
        unsigned char *record=out->bytes+FRANCHISE_FINANCE_HEADER+i*FRANCHISE_FINANCE_RECORD;
        if(!finance_read(host,base+i*0x54u+8u,record,1) ||
           !finance_read(host,base+i*0x54u+10u,record+1,2) ||
           !finance_read(host,base+i*0x54u+36u,record+3,4)) return 0;
        finance_put32(record+7,UINT32_MAX);
    }
    for(uint32_t i=0;i<32;++i) {
        uint32_t team=finance_get32(teams+4*i);unsigned char count,accumulator[2];
        unsigned char *destination=out->bytes+48+12*i;
        if(!team || team>UINT32_MAX-0x1F4u || !host->memory_range(team,0x1F4u)) return 0;
        for(uint32_t j=0;j<i;++j) if(team==finance_get32(teams+4*j)) return 0;
        if(!finance_read(host,team+0x11Cu,&count,1) || count>71 ||
           !finance_member(host,out,team,count,i,base,players) ||
           !finance_read(host,team+0x124u,destination,4) ||
           !finance_read(host,0xE5775Cu+4*i,destination+4,4) ||
           !finance_read(host,team+0x19Cu,accumulator,2)) return 0;
        finance_put32(destination+8,(uint32_t)accumulator[0]|((uint32_t)accumulator[1]<<8));
    }
    /* 324060 supplies bank+38 to 2425C0: DWORD count, relocated pointer list.
     * This is a vector, not a Team object and not serialized relative pointers. */
    if(!finance_member(host,out,finance_get32(free_header+4),finance_get32(free_header),32,base,players)) return 0;
    /* Reject selection/table/bank changes during the read. This does not lock
     * guest contracts, and must not be treated as an atomic world snapshot. */
    unsigned char check[128];
    if(!finance_read(host,0xB72918u,raw,4) || memcmp(root,raw,4) ||
       !finance_read(host,bank,check,8) || memcmp(header,check,8) ||
       !finance_read(host,bank+0x38u,check,8) || memcmp(free_header,check,8) ||
       !finance_read(host,0xE576A0u,check,4) || memcmp(mode,check,4) ||
       !finance_read(host,0xE576A4u,check,28) || memcmp(calendar,check,28) ||
       !finance_read(host,0xE5786Cu,check,128) || memcmp(teams,check,128) ||
       !finance_read(host,0xE3C278u,check,4) || memcmp(cap,check,4)) return 0;
    out->size=FRANCHISE_FINANCE_HEADER+players*FRANCHISE_FINANCE_RECORD;
    return 1;
}
#endif
