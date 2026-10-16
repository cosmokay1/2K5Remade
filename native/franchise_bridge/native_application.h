#pragma once
#include "cap_enforcement.h"
#include "contract_response.h"
#include <cstring>
namespace franchise {
/* Owner-thread state. Issuance is captured once; live checks never perform I/O.
 * The game shim separately pins judgment/precommit to one guest-lock serial. */
struct NativeApplication {
    FranchiseFinanceSnapshot before{};
    FranchiseCapEnforcement cap{};
    nlohmann::json plan=nullptr;
    uint64_t deadline=0;
    uint32_t context=0,amount=0,flags=0;
    bool dispatched=false,judged=false,consumed=false;
    template<class Hash>
    static NativeApplication capture(const nlohmann::json& request,const nlohmann::json& response,
            const nlohmann::json& prepared,const FranchiseFinanceSnapshot& finance,
            uint64_t submitted,Hash hash) {
        validate_result(response,request);
        const auto& p=response.at("result").at("application_plan");
        if(!prepared.contains("salary_clock") || p.at("source_epoch")!=prepared.at("salary_clock").at("source_epoch") ||
           p.at("guest_offer")!=prepared.at("guest_offer") ||
           p.at("source_slot")!=prepared.at("observation").at("biography").at("source_slot") ||
           p.at("team_index")!=prepared.at("observation").at("team").at("table_index") ||
           hash(finance.bytes,finance.size)!=p.at("before_finance_sha256"))
            throw std::runtime_error("Native permit differs from prepared acceptance");
        NativeApplication result;result.before=finance;result.cap.expected=finance;result.plan=p;
        result.amount=p.at("guest_offer").at("amount_word").get<uint32_t>();
        result.flags=p.at("guest_offer").at("flags_word").get<uint32_t>();
        if(!result.amount || result.amount>65535 || submitted>UINT64_MAX-5000)
            throw std::runtime_error("Invalid native amount or deadline");
        result.deadline=submitted+5000;result.cap.source_epoch=p.at("source_epoch").get<uint64_t>();
        result.cap.team_index=p.at("team_index").get<uint32_t>();
        result.cap.native_payroll=p.at("native_payroll_raw").get<uint32_t>();
        result.cap.enforced_payroll=p.at("enforced_payroll_raw").get<uint32_t>();
        const auto record=FRANCHISE_FINANCE_HEADER+p.at("source_slot").get<uint32_t>()*FRANCHISE_FINANCE_RECORD;
        const auto team=48+12*result.cap.team_index;
        for(const auto& delta:p.at("finance_changes")) {
            const auto i=delta[0].get<uint32_t>();
            if(i>=finance.size || !((i>=record && i<record+7) || (i>=team && i<team+4) || (i>=team+8 && i<team+12)))
                throw std::runtime_error("Permit changes unrelated financial fields");
            result.cap.expected.bytes[i]=delta[1].get<unsigned char>();
        }
        if(hash(result.cap.expected.bytes,finance.size)!=p.at("after_finance_sha256") ||
           finance_get32(result.cap.expected.bytes+team)!=result.cap.enforced_payroll ||
           !franchise_cap_state_matches(&result.cap.expected,&result.cap.expected))
            throw std::runtime_error("Native permit target fingerprint changed");
        return result;
    }
    bool fresh(uint64_t now,uint64_t epoch) const {
        return !plan.is_null() && !consumed && now<deadline && epoch==cap.source_epoch;
    }
    template<class Hash>
    bool check(unsigned stage,uint32_t candidate,uint64_t epoch,uint64_t now,
               const FranchiseFinanceSnapshot& finance,const void *identity,size_t identity_size,Hash hash) {
        const bool prior=judged,spent=consumed;
        if(stage==2) consumed=true; /* Every commit attempt consumes, including mismatches. */
        if(spent || plan.is_null() || (stage!=1 && stage!=2) || (stage==1 && (consumed || prior)) ||
           !candidate || now>=deadline || epoch!=cap.source_epoch || (stage==2 && (!prior || context!=candidate)) ||
           finance.size!=before.size || std::memcmp(finance.bytes,before.bytes,before.size) ||
           hash(static_cast<const unsigned char*>(identity),identity_size)!=plan.at("identity_sha256")) {
            consumed=true;return false;
        }
        if(stage==1){context=candidate;judged=true;}
        return true;
    }
};
}
