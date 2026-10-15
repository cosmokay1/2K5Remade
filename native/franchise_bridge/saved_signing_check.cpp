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
        require(argc==10 || argc==11);
        FranchiseHostClient* raw=nullptr;
        require(franchise_host_create(argv[1],argv[2],FRANCHISE_HOST_OFFLINE_FIXTURE,&raw)==FRANCHISE_HOST_OK);
        Client client(raw,&franchise_host_destroy);
        require(franchise_host_check_saved(client.get())==FRANCHISE_HOST_NOT_READY);
        auto hello=nlohmann::json{{"protocol",1},{"request_id","native-hello"},{"operation","hello"}};
        if(argc==11) {
            require(submit(client.get(),hello).at("error")=="invalid_request");
            const std::string denied="{\"protocol\":1,\"request_id\":\"denied\",\"operation\":\"negotiate_proposal\"}";
            require(franchise_host_submit(client.get(),denied.data(),denied.size())==FRANCHISE_HOST_SERVICE_FAILURE);
            hello["loaded_image_sha256"]=std::string(64,'b');
            require(submit(client.get(),hello).at("error")=="state_rejected");
            const std::wstring digest(argv[10]);require(digest.size()==64);
            hello["loaded_image_sha256"]=std::string(digest.begin(),digest.end());
        }
        require(franchise_host_loaded_payload_matches(client.get(),std::string(64,'a').c_str())==FRANCHISE_HOST_NOT_READY);
        const auto greeting=submit(client.get(),hello);require(greeting.at("error").is_null());
        if(argc==11){
            const auto digest=greeting.at("result").at("runtime_binding").at("snapshot_payload_sha256").get<std::string>();
            require(franchise_host_loaded_payload_matches(client.get(),digest.c_str())==FRANCHISE_HOST_OK);
            std::string different=digest;different[0]=digest[0]=='a'?'b':'a';
            require(franchise_host_loaded_payload_matches(client.get(),different.c_str())==FRANCHISE_HOST_INVALID_ARGUMENT);
        }
        std::ifstream input{std::filesystem::path(argv[3])};nlohmann::json proposal;input>>proposal;
        const auto accepted=submit(client.get(),proposal);
        require(accepted.at("error").is_null() && accepted.at("result").at("outcome")=="accepted_proposal");
        require(franchise_host_check_saved(client.get())==FRANCHISE_HOST_NOT_READY); // No implicit preparation.
        std::ifstream financial{std::filesystem::path(argv[6]),std::ios::binary};
        require(financial.good());
        std::vector<char> finance{std::istreambuf_iterator<char>(financial),std::istreambuf_iterator<char>()};
        std::ifstream biographies{std::filesystem::path(argv[7]),std::ios::binary};require(biographies.good());
        std::vector<char> identities{std::istreambuf_iterator<char>(biographies),std::istreambuf_iterator<char>()};
        require(franchise_host_prepare_accepted(client.get(),nullptr,0,nullptr,0)==FRANCHISE_HOST_INVALID_ARGUMENT);
        require(franchise_host_prepare_accepted(client.get(),finance.data(),finance.size()-1,identities.data(),identities.size())==FRANCHISE_HOST_INVALID_ARGUMENT);
        require(franchise_host_prepare_accepted(client.get(),finance.data(),finance.size(),nullptr,0)==FRANCHISE_HOST_INVALID_ARGUMENT);
        require(franchise_host_prepare_accepted(client.get(),finance.data(),finance.size(),identities.data(),identities.size()-1)==FRANCHISE_HOST_INVALID_ARGUMENT);
        auto changed=finance;changed.at(changed.size()-10)^=1; // unrelated final bank slot's amount
        require(franchise_host_prepare_accepted(client.get(),changed.data(),changed.size(),identities.data(),identities.size())==FRANCHISE_HOST_OK);
        require(receive(client.get()).at("error")=="state_rejected");
        // Replaying the captured proposal must not spend another model request.
        require(submit(client.get(),proposal).at("result").at("outcome")=="accepted_proposal");
        auto changed_identity=identities;changed_identity.at(16)^=1; // unselected roster player's photo bytes
        require(franchise_host_prepare_accepted(client.get(),finance.data(),finance.size(),changed_identity.data(),changed_identity.size())==FRANCHISE_HOST_OK);
        require(receive(client.get()).at("error")=="state_rejected");
        require(submit(client.get(),proposal).at("result").at("outcome")=="accepted_proposal");
        require(franchise_host_prepare_accepted(client.get(),finance.data(),finance.size(),identities.data(),identities.size())==FRANCHISE_HOST_OK);
        const auto prepared=receive(client.get());
        require(prepared.at("error").is_null() && prepared.at("result").at("state")=="prepared");
        require(franchise_host_check_saved(client.get())==FRANCHISE_HOST_OK);
        std::ifstream final_finance{std::filesystem::path(argv[8]),std::ios::binary};require(final_finance.good());
        std::ifstream final_identity{std::filesystem::path(argv[9]),std::ios::binary};require(final_identity.good());
        std::vector<char> completed_finance{std::istreambuf_iterator<char>(final_finance),std::istreambuf_iterator<char>()};
        std::vector<char> completed_identity{std::istreambuf_iterator<char>(final_identity),std::istreambuf_iterator<char>()};
        require(franchise_host_observe_completed(client.get(),nullptr,0,nullptr,0)==FRANCHISE_HOST_INVALID_ARGUMENT);
        // A completion while an older status request is pending must still be compared.
        require(franchise_host_observe_completed(client.get(),completed_finance.data(),completed_finance.size(),
                                                completed_identity.data(),completed_identity.size())==FRANCHISE_HOST_OK);
        require(receive(client.get()).at("result").at("save_position")=="before");
        require(franchise_host_check_saved(client.get())==FRANCHISE_HOST_OK);
        const auto compared=receive(client.get());
        require(compared.at("result").at("live_application_matches")==true && compared.at("result").at("save_position")=="before");
        std::filesystem::copy_file(argv[4],argv[5],std::filesystem::copy_options::overwrite_existing);
        require(franchise_host_check_saved(client.get())==FRANCHISE_HOST_OK);
        require(receive(client.get()).at("result").at("save_position")=="candidate_after");
        require(franchise_host_check_saved(client.get())==FRANCHISE_HOST_OK);
        const auto settled=receive(client.get());
        require(settled.at("error").is_null() && settled.at("result").at("state")=="settled");
        require(franchise_host_check_saved(client.get())==FRANCHISE_HOST_OK);
        require(receive(client.get()).at("result").at("save_position")=="confirmed_after");
        require(franchise_host_check_saved(client.get())==FRANCHISE_HOST_NOT_READY);
        if(argc==11) {
            auto wrong=hello;wrong["loaded_image_sha256"]=std::string(64,'b');
            require(submit(client.get(),wrong).at("error")=="state_rejected");
            require(franchise_host_loaded_payload_matches(client.get(),std::string(64,'a').c_str())==FRANCHISE_HOST_NOT_READY);
            const std::string denied="{\"protocol\":1,\"request_id\":\"revoked\",\"operation\":\"negotiate_proposal\"}";
            require(franchise_host_submit(client.get(),denied.data(),denied.size())==FRANCHISE_HOST_SERVICE_FAILURE);
        }
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
