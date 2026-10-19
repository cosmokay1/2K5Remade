#pragma once
#include "../../addons/engine-sidecar/include/engine_sidecar/pipe_client.h"
#include "contract_response.h"
#include "launch_options.h"
namespace franchise {
// Application validation stays outside the reusable process transport.
class PipeClient : public engine_sidecar::PipeClient {
    nlohmann::json request_;
public:
    PipeClient(const std::wstring& python,const std::wstring& database,ServiceMode mode,
               const std::optional<BudgetLaunch>& budget=std::nullopt)
        : engine_sidecar::PipeClient(python,launch_arguments(python,database,mode,budget)) {}
    void submit(std::string text) {
        auto request=parse_frame(text);
        auto timeout=std::chrono::milliseconds(5000);
        if(request.contains("timeout_ms")) {
            const auto& budget=request.at("timeout_ms");
            if(!budget.is_number_integer() || budget<1 || budget>60000)
                throw std::invalid_argument("Bounded franchise request timeout required");
            // Allow the service to report its own deadline before closing IPC.
            timeout=std::chrono::milliseconds(budget.get<int64_t>()+1000);
        }
        engine_sidecar::PipeClient::submit(std::move(text),timeout);
        request_=std::move(request);
    }
    std::string take() {
        auto response=engine_sidecar::PipeClient::take();
        try {
            validate_result(decode_response(response,request_["request_id"].get<std::string>()),request_);
            return response;
        } catch (...) { abort(); throw; }
    }
};
}
