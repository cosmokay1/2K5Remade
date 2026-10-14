#include <engine_sidecar/pipe_client.h>
#include <iostream>
int wmain(int argc,wchar_t** argv) {
    if(argc!=3) return 1;
    try {
        engine_sidecar::PipeClient client(argv[1],{argv[2]});
        client.submit(R"({"protocol":1,"request_id":"echo-1","operation":"echo","payload":"no game required"})");
        auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(10);
        while(!client.ready() && std::chrono::steady_clock::now()<deadline)
            std::this_thread::sleep_for(std::chrono::milliseconds(2));
        auto result=engine_sidecar::decode_response(client.take(),"echo-1");
        if(result["result"]["echo"]!="no game required") return 2;
        std::cout<<"Standalone echo round trip passed\n";
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n';return 3; }
}
