#include <windows.h>
#include <cstring>
#include <cstdlib>
#include <cstdint>

int wmain(int argc, wchar_t** argv) {
    if (argc < 5) return 2;
    HANDLE unrelated = reinterpret_cast<HANDLE>(static_cast<uintptr_t>(_wcstoui64(argv[4], nullptr, 10)));
    DWORD flags = 0;
    if (GetHandleInformation(unrelated, &flags)) return 3;
    // Deliberately acknowledge without consuming stdin, then retain its read end.
    const char* reply = "{\"protocol\":1,\"request_id\":\"stall\",\"result\":{\"ai_enabled\":true,\"operations\":[]},\"error\":null,\"detail\":null}\n";
    DWORD written = 0;
    for (int i = 0; i < 64; ++i)
        if (!WriteFile(GetStdHandle(STD_OUTPUT_HANDLE), reply,
                       static_cast<DWORD>(std::strlen(reply)), &written, nullptr)) return 1;
    Sleep(INFINITE);
    return 0;
}
