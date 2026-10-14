#pragma once
#include <string>
#include <optional>
#include <limits>
#include <stdexcept>
namespace franchise {
enum class ServiceMode { OfflineFixture, VertexRuntime };
struct BudgetLaunch { std::wstring database; std::wstring scope; unsigned long long request_limit; std::optional<unsigned long long> token_limit=std::nullopt; };
// Quote one Windows command-line argument, including embedded quotes/backslashes.
inline std::wstring quote(const std::wstring& value) {
    std::wstring result = L"\"";
    size_t slashes = 0;
    for (wchar_t c : value) {
        if (c == L'\\') { ++slashes; continue; }
        result.append(c == L'"' ? slashes * 2 + 1 : slashes, L'\\');
        slashes = 0;
        result += c;
    }
    result.append(slashes * 2, L'\\');
    return result + L"\"";
}

inline bool launch_text(const std::wstring& value) {
    return value.find_first_not_of(L" \t\r\n")!=std::wstring::npos && value.find(L'\0')==std::wstring::npos;
}
inline std::wstring launch_command(const std::wstring& python,const std::wstring& database,ServiceMode mode,
                                  const std::optional<BudgetLaunch>& budget=std::nullopt) {
    if(!launch_text(python) || !launch_text(database) || (mode!=ServiceMode::OfflineFixture && mode!=ServiceMode::VertexRuntime))
        throw std::invalid_argument("Explicit supported launch configuration required");
    if(budget && (mode!=ServiceMode::VertexRuntime || !launch_text(budget->database) || !launch_text(budget->scope) ||
                  budget->request_limit==0 || budget->request_limit>static_cast<unsigned long long>(std::numeric_limits<long long>::max())))
        throw std::invalid_argument("Invalid explicit runtime budget");
    if(budget && budget->token_limit && (*budget->token_limit==0 ||
        *budget->token_limit>static_cast<unsigned long long>(std::numeric_limits<long long>::max())))
        throw std::invalid_argument("Invalid explicit token budget");
    auto command=quote(python)+L" -m franchise.sidecar --database "+quote(database)+
        (mode==ServiceMode::OfflineFixture?L" --provider offline-fixture":L" --provider vertex --impersonate-runtime");
    if(budget) command+=L" --ai-budget-database "+quote(budget->database)+L" --ai-budget-scope "+quote(budget->scope)+
        L" --ai-request-limit "+std::to_wstring(budget->request_limit);
    if(budget && budget->token_limit) command+=L" --ai-token-limit "+std::to_wstring(*budget->token_limit);
    return command;
}
}
