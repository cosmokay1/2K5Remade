#pragma once
#include "contract_response.h"
namespace franchise {
// Consume the captured proposal exactly; callers cannot replace its terms,
// identity, save hash or revision. Null means no accepted captured proposal.
inline nlohmann::json saved_signing_prepare(const nlohmann::json& request,const nlohmann::json& response) {
    if(request.at("operation")!="negotiate_proposal" || !request.contains("observation") ||
       !response.at("error").is_null()) return nullptr;
    validate_result(response,request);
    const auto& result=response.at("result");
    if(result.at("outcome")!="accepted_proposal") return nullptr;
    const auto& checkpoint=result.at("signing_checkpoint");
    const auto proposal=request.at("request_id").get<std::string>();
    if(proposal.empty() || proposal.size()>200) throw std::runtime_error("Invalid captured proposal identity");
    return {{"protocol",1},{"request_id",proposal+"-guest"},{"operation","guest_signing_prepare"},
        {"timeout_ms",10000},{"team_id",checkpoint.at("team_id")},{"proposal_request_id",proposal},
        {"guest_offer",request.at("guest_offer")},{"expected_revision",checkpoint.at("financial_revision")},
        {"expected_before_sha256",checkpoint.at("saved_payload_sha256")}};
}
}
