#pragma once
#include "contract_response.h"
namespace franchise {
// Consume the captured proposal exactly; callers cannot replace its terms,
// identity, save hash or revision. Null means no accepted captured proposal.
// The native client adds fresh live financial/identity hashes before submit.
inline nlohmann::json saved_signing_prepare(const nlohmann::json& request,const nlohmann::json& response) {
    if(request.at("operation")!="negotiate_proposal" || !request.contains("observation") ||
       !response.at("error").is_null()) return nullptr;
    validate_result(response,request);
    const auto& result=response.at("result");
    if(result.at("outcome")!="accepted_proposal" && result.at("outcome")!="accepted_amendment_proposal") return nullptr;
    if(result.at("outcome")=="accepted_amendment_proposal" && !request.contains("salary_clock")) return nullptr;
    const auto& checkpoint=result.at("signing_checkpoint");
    const auto proposal=request.at("request_id").get<std::string>();
    if(proposal.empty() || proposal.size()>200) throw std::runtime_error("Invalid captured proposal identity");
    nlohmann::json prepared={{"protocol",1},{"request_id",proposal+"-guest"},{"operation","guest_signing_prepare"},
        {"timeout_ms",10000},{"team_id",checkpoint.at("team_id")},{"proposal_request_id",proposal},
        {"guest_offer",request.at("guest_offer")},{"expected_revision",checkpoint.at("financial_revision")},
        {"expected_before_sha256",checkpoint.at("saved_payload_sha256")}};
    if(request.contains("salary_clock")) {
        prepared["salary_clock"]=request.at("salary_clock");prepared["observation"]=request.at("observation");
    }
    return prepared;
}
// This coordinates saved effects only. It never grants guest memory/file writes.
struct SavedSigningJournal {
    nlohmann::json preparation=nullptr, player=nullptr, charges=nullptr, status=nullptr;
    nlohmann::json live_completion=nullptr;
    bool prepared=false;
    void observe_completed(const std::string& finance,const std::string& identity) {
        if(preparation.is_null() || !prepared ||
           (!status.is_null() && status.at("state")!="prepared"))
            throw std::runtime_error("No prepared journal for native completion");
        auto canonical=[](const std::string& value) {
            return value.size()==64 && value.find_first_not_of("0123456789abcdef")==std::string::npos;
        };
        if(!canonical(finance) || !canonical(identity)) throw std::runtime_error("Invalid completion digests");
        const nlohmann::json observation={{"live_finance_sha256",finance},{"live_identity_sha256",identity}};
        if(!live_completion.is_null() && live_completion!=observation)
            throw std::runtime_error("Native completion changed; recovery required");
        live_completion=observation;
    }
    static SavedSigningJournal capture(const nlohmann::json& request,const nlohmann::json& response) {
        SavedSigningJournal journal;
        journal.preparation=saved_signing_prepare(request,response);
        if(!journal.preparation.is_null()) {
            journal.player=response.at("result").at("offer").at("player_id");
            journal.charges=response.at("result").at("proposal_preview").at(request.contains("amendment_rule")?"combined_player_charges":"contract_charges");
        }
        return journal;
    }
    nlohmann::json next(bool ai_granted) const {
        if(preparation.is_null()) return nullptr;
        if(!status.is_null() && (status.at("state")=="cancelled" ||
            (status.at("state")=="settled" && status.at("save_position")=="confirmed_after"))) return nullptr;
        const auto id=preparation.at("request_id").get<std::string>();
        nlohmann::json request={{"protocol",1},{"request_id",id+"-status"},{"operation","guest_signing_status"},
            {"journal_request_id",id},{"timeout_ms",10000}};
        const bool compared=!live_completion.is_null() && !status.is_null() && status.contains("live_application_matches");
        if(compared && status.at("live_application_matches")==false) return nullptr;
        if(!live_completion.is_null()) request.update(live_completion);
        if(ai_granted && (live_completion.is_null() || compared) && !status.is_null() && status.at("state")=="prepared" && status.at("save_position")=="candidate_after") {
            request.erase("live_finance_sha256");request.erase("live_identity_sha256");
            request["request_id"]=id+"-confirm";request["operation"]="guest_signing_confirm";
            request["expected_after_sha256"]=status.at("current_payload_sha256");
        }
        return request;
    }
    void consume(const nlohmann::json& request,const nlohmann::json& response) {
        if(preparation.is_null()) return;
        const auto op=request.at("operation").get<std::string>();
        if(op!="guest_signing_prepare" && op!="guest_signing_status" && op!="guest_signing_confirm") return;
        if((op=="guest_signing_prepare" ? request.at("request_id") : request.at("journal_request_id"))!=preparation.at("request_id"))
            throw std::runtime_error("Saved-signing request belongs to another journal");
        status=nullptr; // A refused or uncertain confirmation requires a fresh read.
        if(!response.at("error").is_null()) return;
        validate_result(response,request);
        const auto& result=response.at("result");
        if(op=="guest_signing_status") {
            if(result.at("before_payload_sha256")!=preparation.at("expected_before_sha256"))
                throw std::runtime_error("Saved-signing before-save changed");
            if(request.contains("live_finance_sha256") &&
               (live_completion.is_null() || request.at("live_finance_sha256")!=live_completion.at("live_finance_sha256") ||
                request.at("live_identity_sha256")!=live_completion.at("live_identity_sha256")))
                throw std::runtime_error("Completion status differs from captured native result");
            prepared=result.at("state")=="prepared";
            status=result;
        } else if(op=="guest_signing_prepare") {
            prepared=true;
        } else if(op=="guest_signing_confirm") {
            prepared=false;
            const auto revision=preparation.at("expected_revision").get<int64_t>();
            if(revision==std::numeric_limits<int64_t>::max()) throw std::runtime_error("Signing revision exceeds native range");
            if(result.at("player_id")!=player || result.at("charges")!=charges ||
                result.at("financial_revision")!=revision+1)
                throw std::runtime_error("Saved-signing settlement differs from captured acceptance");
        }
    }
};
}
