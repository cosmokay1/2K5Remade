/* Application-private payroll binding. Arithmetic evidence is not a signing
 * grant. The application coordinator owns publication, source epoch and guest
 * lock; the generic addon ABI still exposes no memory-write function. */
#ifndef NFL2K5_CAP_ENFORCEMENT_H
#define NFL2K5_CAP_ENFORCEMENT_H
#include "finance_state.h"
#include <limits.h>

typedef struct FranchiseCapEnforcement {
    uint64_t source_epoch;
    uint32_t team_index,native_payroll,enforced_payroll;
    FranchiseFinanceSnapshot expected;
} FranchiseCapEnforcement;

/* Compare all contracts, owners, calendar, cap and accumulators. Ignore only
 * cached payroll totals: a repeated native recomputation must not add debt a
 * second time. The independently computed native total is checked separately. */
static int franchise_cap_state_matches(const FranchiseFinanceSnapshot *a,const FranchiseFinanceSnapshot *b) {
    if(!a || !b || a->size!=b->size || a->size<FRANCHISE_FINANCE_HEADER ||
       a->size>sizeof(a->bytes) || memcmp(a->bytes,b->bytes,48)) return 0;
    const uint32_t players=finance_get32(a->bytes+4);
    if(!players || players>FRANCHISE_FINANCE_MAX_PLAYERS ||
       a->size!=FRANCHISE_FINANCE_HEADER+players*FRANCHISE_FINANCE_RECORD ||
       finance_get32(a->bytes)!=1 || finance_get32(a->bytes+8)!=2 ||
       finance_get32(a->bytes+24)!=32) return 0;
    for(unsigned i=0;i<32;++i)
        if(memcmp(a->bytes+48+12*i+4,b->bytes+48+12*i+4,8)) return 0;
    for(uint32_t i=0;i<players;++i) {
        const unsigned char *expected=a->bytes+FRANCHISE_FINANCE_HEADER+i*FRANCHISE_FINANCE_RECORD;
        const unsigned char *live=b->bytes+FRANCHISE_FINANCE_HEADER+i*FRANCHISE_FINANCE_RECORD;
        if(memcmp(expected,live,7)) return 0;
        if(finance_get32(expected+7)==finance_get32(live+7)) continue;
        /* An offer screen temporarily removes an unsigned player from the FA
         * pool. Exactly unchanged zero terms cannot change any club liability.
         * Team ownership, positive amounts/terms and bonus changes still fail. */
        if(finance_get32(expected+7)!=32 || finance_get32(live+7)!=UINT32_MAX ||
           expected[1] || expected[2] || (expected[3]&15) || expected[5]!=2 || (expected[6]&15)) return 0;
    }
    return 1;
}
/* No plan means ordinary native accounting. An armed plan that no longer
 * matches blocks further cap room rather than silently losing retained debt.
 * The caller stores this result at the existing native payroll assignment. */
static uint32_t franchise_cap_enforced_payroll(const FranchiseCapEnforcement *plan,
        const FranchiseFinanceSnapshot *live,uint64_t source_epoch,uint32_t team_index,uint32_t computed) {
    if(!plan || !plan->source_epoch || team_index!=plan->team_index) return computed;
    if(plan->team_index>=32 || !source_epoch || source_epoch!=plan->source_epoch ||
       plan->enforced_payroll>INT32_MAX-1u || computed!=plan->native_payroll ||
       !franchise_cap_state_matches(&plan->expected,live)) return INT32_MAX;
    return plan->enforced_payroll;
}
/* The production issuer must publish the complete accepted after-state before
 * allowing native mutation. Saved recovery must rebind the exact recorded
 * after-state on a new load epoch; that never grants another signing. */
#ifdef __cplusplus
extern "C" {
#endif
int nfl2k5_franchise_publish_cap(const FranchiseCapEnforcement *plan);
#ifdef __cplusplus
}
#endif
#endif
