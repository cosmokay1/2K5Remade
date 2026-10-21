#include "cap_enforcement.h"
#include <stdio.h>
#define CHECK(v) do {if(!(v)) {fprintf(stderr,"cap enforcement failure at %d\n",__LINE__);return 1;}} while(0)
static FranchiseCapEnforcement plan;
static FranchiseFinanceSnapshot live;
int main(void) {
    plan.source_epoch=42;plan.team_index=7;plan.native_payroll=2000;plan.enforced_payroll=3658;
    live.size=FRANCHISE_FINANCE_HEADER+FRANCHISE_FINANCE_RECORD;
    finance_put32(live.bytes,1);finance_put32(live.bytes+4,1);finance_put32(live.bytes+8,2);
    finance_put32(live.bytes+12,80500);finance_put32(live.bytes+24,32);
    plan.expected=live;
    CHECK(franchise_cap_enforced_payroll(NULL,&live,42,7,2000)==2000);
    CHECK(franchise_cap_enforced_payroll(&plan,&live,42,8,2000)==2000);
    CHECK(franchise_cap_enforced_payroll(&plan,&live,42,7,2000)==3658);
    /* Recalculation of an already corrected stored payroll is idempotent. */
    finance_put32(live.bytes+48+12*7,3658);
    CHECK(franchise_cap_enforced_payroll(&plan,&live,42,7,2000)==3658);
    CHECK(franchise_cap_enforced_payroll(&plan,&live,43,7,2000)==INT32_MAX);
    CHECK(franchise_cap_enforced_payroll(&plan,&live,42,7,2001)==INT32_MAX);
    for(unsigned offset=0;offset<live.size;++offset) {
        int payroll=offset>=48 && offset<432 && ((offset-48)%12)<4;
        live.bytes[offset]^=1;
        CHECK(franchise_cap_enforced_payroll(&plan,&live,42,7,2000)==(payroll?3658:INT32_MAX));
        live.bytes[offset]^=1;
    }
    /* Earned salary can require reducing a full annual native rate. */
    plan.enforced_payroll=1900;
    CHECK(franchise_cap_enforced_payroll(&plan,&live,42,7,2000)==1900);
    plan.enforced_payroll=UINT32_MAX;
    CHECK(franchise_cap_enforced_payroll(&plan,&live,42,7,2000)==INT32_MAX);
    plan.enforced_payroll=3658;
    unsigned char *record=live.bytes+FRANCHISE_FINANCE_HEADER;
    memset(record,0,FRANCHISE_FINANCE_RECORD);record[5]=2;finance_put32(record+7,32);plan.expected=live;
    finance_put32(record+7,UINT32_MAX);
    CHECK(franchise_cap_enforced_payroll(&plan,&live,42,7,2000)==3658);
    for(unsigned offset=0;offset<7;++offset) {
        record[offset]^=1;
        CHECK(franchise_cap_enforced_payroll(&plan,&live,42,7,2000)==INT32_MAX);
        record[offset]^=1;
    }
    finance_put32(record+7,7);
    CHECK(franchise_cap_enforced_payroll(&plan,&live,42,7,2000)==INT32_MAX);
    finance_put32(record+7,32);
    CHECK(franchise_cap_enforced_payroll(&plan,&live,42,7,2000)==3658);
    puts("Cap payroll binding: exact state, repeat recomputation, stale/source denial passed");
    return 0;
}
