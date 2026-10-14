#include <windows.h>
#include <cstring>

int main() {
    // Deliberately acknowledge without consuming stdin, then retain its read end.
    const char* reply = "{\"protocol\":1,\"request_id\":\"stall\",\"result\":{\"ai_enabled\":true,\"operations\":[]},\"error\":null,\"detail\":null}\n";
    DWORD written = 0;
    if (!WriteFile(GetStdHandle(STD_OUTPUT_HANDLE), reply,
                   static_cast<DWORD>(std::strlen(reply)), &written, nullptr)) return 1;
    Sleep(INFINITE);
    return 0;
}
