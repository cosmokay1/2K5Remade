#include "../include/engine_sidecar/pipe_client.h"
#include <iostream>
static void wait_ready(engine_sidecar::PipeClient& client) {
    auto end=std::chrono::steady_clock::now()+std::chrono::seconds(10);
    while(!client.ready() && std::chrono::steady_clock::now()<end)
        std::this_thread::sleep_for(std::chrono::milliseconds(2));
    if(!client.ready()) throw std::runtime_error("Deadline worker did not finish");
}
#ifdef _WIN32
int wmain(int argc,wchar_t** argv) {
#else
int main(int argc,char** argv) {
#endif
    if(argc!=3) return 1;
    try {
        engine_sidecar::PipeClient client(argv[1],{argv[2]});
        const std::string slow=R"({"protocol":1,"request_id":"slow","delay_ms":5500,"payload":"delayed"})";
        {
            engine_sidecar::PipeClient original_budget(argv[1],{argv[2]});
            original_budget.submit(slow);wait_ready(original_budget);
            bool expired=false;try{original_budget.take();}catch(const std::exception&){expired=true;}
            if(!expired) return 7;
        }
        for(int invalid:{-1,0,65001}) {
            bool denied=false;
            try {client.submit(slow,std::chrono::milliseconds(invalid));}
            catch(const std::invalid_argument&){denied=true;}
            if(!denied) return 2;
        }
        client.submit(slow,std::chrono::seconds(8));wait_ready(client);
        if(engine_sidecar::decode_response(client.take(),"slow")["result"]["echo"]!="delayed") return 3;
        client.submit(R"({"protocol":1,"request_id":"expires","delay_ms":500,"payload":"late"})",
                      std::chrono::milliseconds(50));
        wait_ready(client);
        bool timed_out=false;try{client.take();}catch(const std::exception&){timed_out=true;}
        if(!timed_out) return 4;
        bool disconnected=false;try{client.submit(slow);}catch(const std::exception&){disconnected=true;}
        if(!disconnected) return 5;
        std::cout<<"Delayed reply survives five seconds; explicit expiry closes transport without retry.\n";
    } catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 6;}
}
