#pragma once
#include <string>
#include <vector>
#include <stdexcept>
namespace engine_sidecar {
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
inline std::wstring launch_command(const std::wstring& executable, const std::vector<std::wstring>& arguments) {
    if (!launch_text(executable)) throw std::invalid_argument("Explicit executable required");
    std::wstring command=quote(executable);
    for (const auto& argument : arguments) {
        if (argument.find(L'\0') != std::wstring::npos) throw std::invalid_argument("NUL in launch argument");
        command+=L" "+quote(argument);
    }
    return command;
}
}
