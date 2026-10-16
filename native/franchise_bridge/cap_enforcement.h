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
    return !memcmp(a->bytes+FRANCHISE_FINANCE_HEADER,b->bytes+FRANCHISE_FINANCE_HEADER,
                   a->size-FRANCHISE_FINANCE_HEADER);
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
