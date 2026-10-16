/* Pure authored permit state machine. Hash callback is deliberately a fixture
 * fingerprint; production uses Windows BCrypt SHA256 over the same bytes. */
#include "native_application.h"
#include <cstdio>
#include <functional>
using nlohmann::json;
static std::string fingerprint(const unsigned char *bytes,size_t size) {
    uint64_t hash=1469598103934665603ULL;
    for(size_t i=0;i<size;++i) hash=(hash^bytes[i])*1099511628211ULL;
    char out[17];std::snprintf(out,sizeof(out),"%016llx",(unsigned long long)hash);
    return std::string(out)+out+out+out;
}
static void require(bool value){if(!value)throw std::runtime_error("native application regression");}
int main(){
    FranchiseFinanceSnapshot before{};before.size=FRANCHISE_FINANCE_HEADER+FRANCHISE_FINANCE_RECORD;
    finance_put32(before.bytes,1);finance_put32(before.bytes+4,1);finance_put32(before.bytes+8,2);finance_put32(before.bytes+24,32);
    finance_put32(before.bytes+48,5000);
    const unsigned char identity[]={1,2,3};
    auto after=before;finance_put32(after.bytes+48,6000);
    json changes=json::array();for(uint32_t i=0;i<before.size;++i)if(before.bytes[i]!=after.bytes[i])changes.push_back({i,after.bytes[i]});
    json plan={{"format","native-signing-permit-v1"},{"journal_request_id","journal"},{"source_epoch",7},
        {"team_index",0},{"source_slot",0},{"guest_offer",{{"amount_word",600},{"flags_word",196608}}},
        {"before_finance_sha256",fingerprint(before.bytes,before.size)},{"identity_sha256",fingerprint(identity,sizeof(identity))},
        {"after_finance_sha256",fingerprint(after.bytes,after.size)},{"finance_changes",changes},
        {"native_payroll_raw",4000},{"enforced_payroll_raw",6000},{"valid_for_ms",5000}};
    json request={{"protocol",1},{"request_id","issue"},{"operation","guest_signing_authorize"},{"journal_request_id","journal"},
        {"live_finance_sha256",plan["before_finance_sha256"]},{"live_identity_sha256",plan["identity_sha256"]}};
    json prepared={{"salary_clock",{{"source_epoch",7}}},{"guest_offer",plan["guest_offer"]},
        {"observation",{{"biography",{{"source_slot",0}}},{"team",{{"table_index",0}}}}}};
    json response={{"protocol",1},{"request_id","issue"},{"error",nullptr},{"result",{{"request_id","issue"},{"application_plan",plan}}}};
    auto capture=[&](){return franchise::NativeApplication::capture(request,response,prepared,before,100,fingerprint);};
    auto fresh=capture();require(fresh.fresh(5099,7));require(!fresh.fresh(5100,7));require(!fresh.fresh(101,8));
    require(fresh.check(1,1000,7,101,before,identity,sizeof(identity),fingerprint));
    require(fresh.check(2,1000,7,102,before,identity,sizeof(identity),fingerprint));
    require(!fresh.check(2,1000,7,103,before,identity,sizeof(identity),fingerprint));
    require(!fresh.fresh(104,7));
    for(unsigned kind=0;kind<6;++kind){
        auto permit=capture();auto state=before;unsigned char changed[]={1,2,4};
        require(permit.check(1,1000,7,101,before,identity,sizeof(identity),fingerprint));
        if(kind==0)state.bytes[16]^=1;
        if(kind==1)state.bytes[FRANCHISE_FINANCE_HEADER]^=1;
        if(kind==2)state.bytes[48]^=1;
        require(!permit.check(2,kind==3?1001:1000,kind==4?8:7,kind==5?5100:102,state,
            kind==1?changed:identity,sizeof(identity),fingerprint));
        require(!permit.check(2,1000,7,103,before,identity,sizeof(identity),fingerprint));
    }
    auto bypass=capture();require(!bypass.check(2,1000,7,101,before,identity,sizeof(identity),fingerprint));
    auto repeated=capture();require(repeated.check(1,1000,7,101,before,identity,sizeof(identity),fingerprint));
    require(!repeated.check(1,1000,7,102,before,identity,sizeof(identity),fingerprint));
    require(!repeated.check(2,1000,7,103,before,identity,sizeof(identity),fingerprint));
    for(unsigned kind=0;kind<4;++kind){auto bad=response;
        if(kind==0)bad["result"]["application_plan"]["finance_changes"].push_back({16,99});
        if(kind==1)bad["result"]["application_plan"]["source_epoch"]=8;
        if(kind==2)bad["result"]["application_plan"]["guest_offer"]["amount_word"]=601;
        if(kind==3)bad["result"]["application_plan"]["after_finance_sha256"]=std::string(64,'0');
        bool rejected=false;try{franchise::NativeApplication::capture(request,bad,prepared,before,100,fingerprint);}catch(...){rejected=true;}require(rejected);
    }
    puts("Native acceptance/clock/state/deadline and one-use application checks passed");
}
