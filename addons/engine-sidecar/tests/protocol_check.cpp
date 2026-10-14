#include <engine_sidecar/protocol.h>
#include <engine_sidecar/launch.h>
#include <iostream>
#include <stdexcept>
using namespace engine_sidecar;
void require(bool value) { if(!value) throw std::runtime_error("check failed"); }
int main() {
    const std::string good=R"({"protocol":1,"request_id":"a","result":{"echo":"hello"},"error":null,"detail":null})";
    require(decode_response(good,"a")["result"]["echo"]=="hello");
    for(const std::string bad : {
        R"({"protocol":1,"protocol":1,"request_id":"a","result":{},"error":null,"detail":null})",
        R"({"protocol":1,"request_id":"b","result":{},"error":null,"detail":null})",
        R"({"protocol":1,"request_id":"a","result":{},"error":"failure","detail":null})"}) {
        bool rejected=false;try { decode_response(bad,"a"); } catch(...) { rejected=true; } require(rejected);
    }
    require(launch_command(L"tool with spaces.exe",{L"",L"a\"b",L"tail\\"})==
        L"\"tool with spaces.exe\" \"\" \"a\\\"b\" \"tail\\\\\"");
    std::cout<<"Envelope validation and explicit launch quoting passed\n";
}
