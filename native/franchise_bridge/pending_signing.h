/* Private read-only guard for the original signing cleanup queues.
 * A clear result is only a prerequisite, never application authority or a
 * promise that the guest cannot yield. Addresses require the pinned game base. */
#ifndef NFL2K5_PENDING_SIGNING_H
#define NFL2K5_PENDING_SIGNING_H
#include "finance_state.h"
static int franchise_pending_signing_clear(const NFL2K5AddonHost *host,uint32_t context) {
    unsigned char raw[16],root[4],bank[8],trades[15*0x3C],offers[100*0x10],check[100*0x10];
    if(!host || host->size!=sizeof(*host) || !host->memory_range || !host->read_memory ||
       !finance_read(host,context,raw,sizeof(raw)) ||
       !finance_read(host,0xB72918u,root,sizeof(root)) ||
       !finance_read(host,finance_get32(root),bank,sizeof(bank))) return 0;
    const uint32_t player=finance_get32(raw),players=finance_get32(bank),base=finance_get32(bank+4);
    if(!base || !players || players>FRANCHISE_FINANCE_MAX_PLAYERS || player<base ||
       (uint64_t)base+(uint64_t)players*0x54u>UINT64_C(0x100000000) ||
       (player-base)%0x54u || (player-base)/0x54u>=players ||
       !host->memory_range(base,(size_t)players*0x54u) ||
       !finance_read(host,0xE3C27Cu,trades,sizeof(trades)) ||
       !finance_read(host,0xE3C600u,offers,sizeof(offers))) return 0;
    /* 2BAAE0 matches any of six participant pointers in an active 3C-byte row. */
    for(unsigned i=0;i<15;++i) {
        const unsigned char *row=trades+i*0x3C;
        if(!finance_get32(row)) continue;
        for(unsigned j=0;j<3;++j)
            if(finance_get32(row+0xC+4*j)==player || finance_get32(row+0x24+4*j)==player) return 0;
    }
    /* 323060 uses 322840/322BA0: 100 inline records, byte B low two bits active. */
    for(unsigned i=0;i<100;++i)
        if((offers[i*0x10+0xB]&3u) && finance_get32(offers+i*0x10)==player) return 0;
    /* Detect changes while sampling; this is not a mutation lock or ABA proof. */
    return finance_read(host,context,check,sizeof(raw)) && !memcmp(raw,check,sizeof(raw)) &&
        finance_read(host,0xB72918u,check,sizeof(root)) && !memcmp(root,check,sizeof(root)) &&
        finance_read(host,finance_get32(root),check,sizeof(bank)) && !memcmp(bank,check,sizeof(bank)) &&
        finance_read(host,0xE3C27Cu,check,sizeof(trades)) && !memcmp(trades,check,sizeof(trades)) &&
        finance_read(host,0xE3C600u,check,sizeof(offers)) && !memcmp(offers,check,sizeof(offers));
}
#endif
