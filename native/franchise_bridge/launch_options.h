#pragma once
#include "../../addons/engine-sidecar/include/engine_sidecar/launch.h"
#include <string>
#include <optional>
#include <limits>
#include <stdexcept>
namespace franchise {
enum class ServiceMode { OfflineFixture, VertexRuntime, LocalRules };
struct BudgetLaunch { std::wstring database; std::wstring scope; unsigned long long request_limit; std::optional<unsigned long long> token_limit=std::nullopt; };
using engine_sidecar::quote;
using engine_sidecar::launch_text;
inline std::vector<std::wstring> launch_arguments(const std::wstring& python,const std::wstring& database,ServiceMode mode,
                                  const std::optional<BudgetLaunch>& budget=std::nullopt) {
    if(!launch_text(python) || !launch_text(database) || (mode!=ServiceMode::OfflineFixture && mode!=ServiceMode::VertexRuntime && mode!=ServiceMode::LocalRules))
        throw std::invalid_argument("Explicit supported launch configuration required");
    if(budget && (mode!=ServiceMode::VertexRuntime || !launch_text(budget->database) || !launch_text(budget->scope) ||
                  budget->request_limit==0 || budget->request_limit>static_cast<unsigned long long>(std::numeric_limits<long long>::max())))
        throw std::invalid_argument("Invalid explicit runtime budget");
    if(budget && budget->token_limit && (*budget->token_limit==0 ||
        *budget->token_limit>static_cast<unsigned long long>(std::numeric_limits<long long>::max())))
        throw std::invalid_argument("Invalid explicit token budget");
    std::vector<std::wstring> arguments={L"-m",L"franchise.sidecar",L"--database",database,L"--provider",
        mode==ServiceMode::OfflineFixture?L"offline-fixture":mode==ServiceMode::LocalRules?L"local-rules":L"vertex"};
    if(mode==ServiceMode::VertexRuntime) arguments.push_back(L"--impersonate-runtime");
    if(budget) {
        arguments.insert(arguments.end(),{L"--ai-budget-database",budget->database,L"--ai-budget-scope",budget->scope,
            L"--ai-request-limit",std::to_wstring(budget->request_limit)});
        if(budget->token_limit) arguments.insert(arguments.end(),{L"--ai-token-limit",std::to_wstring(*budget->token_limit)});
    }
    return arguments;
}
inline std::wstring launch_command(const std::wstring& python,const std::wstring& database,ServiceMode mode,
                                  const std::optional<BudgetLaunch>& budget=std::nullopt) {
    return engine_sidecar::launch_command(python,launch_arguments(python,database,mode,budget));
}
}
