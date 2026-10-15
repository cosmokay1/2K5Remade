/* Authored files only. The Python driver owns the isolated database/save paths. */
#include "host_client.h"
#include "protocol.h"
#include <windows.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <vector>
#include <iterator>
using Client=std::unique_ptr<FranchiseHostClient,decltype(&franchise_host_destroy)>;
static void require(bool value) {if(!value) throw std::runtime_error("Native saved-signing invariant failed");}
static nlohmann::json receive(FranchiseHostClient* client) {
    int ready=0;const auto started=GetTickCount64();
    while(!ready) {
        require(franchise_host_ready(client,&ready)==FRANCHISE_HOST_OK);
        require(GetTickCount64()-started<10000);
        if(!ready) Sleep(1);
    }
    size_t length=0;
    require(franchise_host_take(client,nullptr,0,&length)==FRANCHISE_HOST_BUFFER_TOO_SMALL && length>1);
    require(franchise_host_check_saved(client)==FRANCHISE_HOST_BUSY);
    std::vector<char> bytes(length);
    require(franchise_host_take(client,bytes.data(),bytes.size(),&length)==FRANCHISE_HOST_OK);
    const std::string response(bytes.data());std::cout<<response<<std::endl;
    return franchise::parse_frame(response);
}
static nlohmann::json submit(FranchiseHostClient* client,const nlohmann::json& request) {
    const auto bytes=request.dump();
    require(franchise_host_submit(client,bytes.data(),bytes.size())==FRANCHISE_HOST_OK);
    return receive(client);
}
int wmain(int argc,wchar_t** argv) {
    try {
        require(argc==7);
        FranchiseHostClient* raw=nullptr;
        require(franchise_host_create(argv[1],argv[2],FRANCHISE_HOST_OFFLINE_FIXTURE,&raw)==FRANCHISE_HOST_OK);
        Client client(raw,&franchise_host_destroy);
        require(franchise_host_check_saved(client.get())==FRANCHISE_HOST_NOT_READY);
        auto hello=nlohmann::json{{"protocol",1},{"request_id","native-hello"},{"operation","hello"}};
        require(submit(client.get(),hello).at("error").is_null());
        std::ifstream input{std::filesystem::path(argv[3])};nlohmann::json proposal;input>>proposal;
        const auto accepted=submit(client.get(),proposal);
        require(accepted.at("error").is_null() && accepted.at("result").at("outcome")=="accepted_proposal");
        require(franchise_host_check_saved(client.get())==FRANCHISE_HOST_NOT_READY); // No implicit preparation.
        std::ifstream financial{std::filesystem::path(argv[6]),std::ios::binary};
        require(financial.good());
        std::vector<char> finance{std::istreambuf_iterator<char>(financial),std::istreambuf_iterator<char>()};
        require(franchise_host_prepare_accepted(client.get(),nullptr,0)==FRANCHISE_HOST_INVALID_ARGUMENT);
        require(franchise_host_prepare_accepted(client.get(),finance.data(),finance.size()-1)==FRANCHISE_HOST_INVALID_ARGUMENT);
        auto changed=finance;changed.at(changed.size()-10)^=1; // unrelated final bank slot's amount
        require(franchise_host_prepare_accepted(client.get(),changed.data(),changed.size())==FRANCHISE_HOST_OK);
        require(receive(client.get()).at("error")=="state_rejected");
        // Replaying the captured proposal must not spend another model request.
        require(submit(client.get(),proposal).at("result").at("outcome")=="accepted_proposal");
        require(franchise_host_prepare_accepted(client.get(),finance.data(),finance.size())==FRANCHISE_HOST_OK);
        const auto prepared=receive(client.get());
        require(prepared.at("error").is_null() && prepared.at("result").at("state")=="prepared");
        require(franchise_host_check_saved(client.get())==FRANCHISE_HOST_OK);
        require(receive(client.get()).at("result").at("save_position")=="before");
        std::filesystem::copy_file(argv[4],argv[5],std::filesystem::copy_options::overwrite_existing);
        require(franchise_host_check_saved(client.get())==FRANCHISE_HOST_OK);
        require(receive(client.get()).at("result").at("save_position")=="candidate_after");
        require(franchise_host_check_saved(client.get())==FRANCHISE_HOST_OK);
        const auto settled=receive(client.get());
        require(settled.at("error").is_null() && settled.at("result").at("state")=="settled");
        require(franchise_host_check_saved(client.get())==FRANCHISE_HOST_OK);
        require(receive(client.get()).at("result").at("save_position")=="confirmed_after");
        require(franchise_host_check_saved(client.get())==FRANCHISE_HOST_NOT_READY);
        client.reset();
        // No runtime budget/ADC: hello fails, but explicit saved-journal recovery reads remain available.
        require(franchise_host_create(argv[1],argv[2],FRANCHISE_HOST_VERTEX_RUNTIME,&raw)==FRANCHISE_HOST_OK);
        client.reset(raw);
        require(submit(client.get(),hello).at("error")=="ai_disabled");
        const auto id=prepared.at("result").at("request_id");
        auto status=nlohmann::json{{"protocol",1},{"request_id","native-recovery"},{"operation","guest_signing_status"},
            {"journal_request_id",id},{"timeout_ms",10000}};
        const auto recovery=submit(client.get(),status);
        require(recovery.at("error").is_null() && recovery.at("result").at("save_position")=="confirmed_after");
        return 0;
    } catch(const std::exception& error) {std::cerr<<error.what()<<std::endl;return 1;}
}
