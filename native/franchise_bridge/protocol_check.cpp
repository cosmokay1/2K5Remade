#include "protocol.h"
#include <iostream>

int main() {
    try {
        const std::string valid = R"({"protocol":1,"request_id":"one","result":{},"error":null,"detail":null})";
        franchise::decode_response(valid, "one");
        for (const std::string& bad : {
            std::string(R"({"protocol":true,"request_id":"one","result":{},"error":null,"detail":null})"),
            std::string(R"({"protocol":1,"protocol":2,"request_id":"one","result":{},"error":null,"detail":null})"),
            std::string(R"({"protocol":1,"request_id":"other","result":{},"error":null,"detail":null})"),
            std::string(R"({"protocol":1,"request_id":"one","result":{},"error":"busy","detail":null})"),
            std::string(R"({"protocol":1,"request_id":"one","result":null,"error":null,"detail":null})"),
            std::string("not JSON")}) {
            bool rejected = false;
            try { franchise::decode_response(bad, "one"); }
            catch (const std::exception&) { rejected = true; }
            if (!rejected) throw std::runtime_error("Malformed response accepted");
        }
        franchise::decode_response(R"({"protocol":1,"request_id":"one","result":null,"error":"busy","detail":null})", "one");
        std::cout << "Protocol envelope validation passed" << std::endl;
        return 0;
    } catch (const std::exception& error) { std::cerr << error.what() << std::endl; return 1; }
}
