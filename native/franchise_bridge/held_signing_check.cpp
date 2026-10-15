/* Authored transport replies only. Exercise the actual C host's submit/poll
 * state machine without a service, model, game memory or financial writes. */
#include "../../src/nfl2k5_franchise_host.h"
#include "protocol.h"
#include <windows.h>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <fstream>
#include <stdexcept>
struct FranchiseHostClient { bool pending=false; };
static FranchiseHostClient client;
static nlohmann::json submitted;
static unsigned submissions;
static bool ready;
static void require(bool ok) { if(!ok) throw std::runtime_error("Held signing host invariant failed"); }
FranchiseHostStatus franchise_host_create(const wchar_t*,const wchar_t*,FranchiseHostMode mode,FranchiseHostClient** out) {
    require(mode==FRANCHISE_HOST_VERTEX_RUNTIME);client.pending=false;*out=&client;return FRANCHISE_HOST_OK;
}
FranchiseHostStatus franchise_host_create_with_budget(const wchar_t* p,const wchar_t* d,FranchiseHostMode m,
    const wchar_t*,const wchar_t*,unsigned long long,FranchiseHostClient** out) { return franchise_host_create(p,d,m,out); }
FranchiseHostStatus franchise_host_create_with_token_budget(const wchar_t* p,const wchar_t* d,FranchiseHostMode m,
    const wchar_t*,const wchar_t*,unsigned long long,unsigned long long,FranchiseHostClient** out) { return franchise_host_create(p,d,m,out); }
FranchiseHostStatus franchise_host_submit(FranchiseHostClient* c,const char* bytes,size_t length) {
    require(!c->pending);submitted=franchise::parse_frame(std::string(bytes,length));
    require(submitted.at("protocol")==1);++submissions;c->pending=true;return FRANCHISE_HOST_OK;
}
FranchiseHostStatus franchise_host_ready(FranchiseHostClient*,int* out) { *out=ready;return FRANCHISE_HOST_OK; }
FranchiseHostStatus franchise_host_take(FranchiseHostClient* c,char* buffer,size_t capacity,size_t* required) {
    require(c->pending && ready);const char response[]="{\"fixture\":true}";
    require(capacity>=sizeof(response));std::memcpy(buffer,response,sizeof(response));*required=sizeof(response);
    c->pending=false;return FRANCHISE_HOST_OK;
}
FranchiseHostStatus franchise_host_signing_display(const char*,FranchiseSigningDisplay* out) {
    *out={};std::strcpy(out->offer,"Authored response");return FRANCHISE_HOST_OK;
}
void franchise_host_destroy(FranchiseHostClient*) { client.pending=false; }
static DWORD WINAPI foreign_submit(void*) { return nfl2k5_franchise_submit_held(1)==1 ? 0 : 1; }
int main(int argc,char** argv) {
    try {
        for(const auto* key:{L"NFL2K5_FRANCHISE_AI_BUDGET_DATABASE",L"NFL2K5_FRANCHISE_AI_BUDGET_SCOPE",
             L"NFL2K5_FRANCHISE_AI_REQUEST_LIMIT",L"NFL2K5_FRANCHISE_AI_TOKEN_LIMIT"}) _wputenv_s(key,L"");
        _wputenv_s(L"NFL2K5_FRANCHISE_PROVIDER",L"vertex");
        _wputenv_s(L"NFL2K5_FRANCHISE_PYTHON",L"authored-python");
        _wputenv_s(L"NFL2K5_FRANCHISE_DATABASE",L"authored-db");
        _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_SAVE",L"authored-save");
        _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_BINDINGS",L"authored-bindings");
        _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_REVISION",L"0");
        _wputenv_s(L"NFL2K5_FRANCHISE_SAVED_PERFORMANCE",L"1");
        _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_OFFER",L"1");
        _wputenv_s(L"NFL2K5_FRANCHISE_NEGOTIATION",L"1");
        require(nfl2k5_franchise_start()==1);
        nfl2k5_franchise_on_fsm(0x557B2C,1);require(submissions==1 && submitted["operation"]=="hello");
        ready=true;nfl2k5_franchise_poll();
        FranchiseSigningObservation observation={};
        observation.offer_amount=829;observation.offer_flags=(1u<<29)|(2u<<16)|4u;
        std::strcpy(observation.first_name,"Authored");std::strcpy(observation.last_name,"Receiver");
        std::strcpy(observation.photo,"00000000");std::strcpy(observation.dob,"000000");
        nfl2k5_franchise_signing_context(&observation);require(submissions==2);
        require(nfl2k5_franchise_submit_held(1)==1);
        ready=false;nfl2k5_franchise_poll();require(submissions==2);
        ready=true;nfl2k5_franchise_poll();
        nfl2k5_franchise_signing_context(&observation);
        require(submissions==3 && submitted["operation"]=="negotiate_proposal");
        require(!submitted.contains("performance_format") && submitted["guest_offer"]["amount_word"]==829);
        require(submitted["expected_revision"]==0 && submitted["observation"]["biography"]["first_name"]=="Authored");
        nfl2k5_franchise_poll();
        require(nfl2k5_franchise_submit_held(1)==1);
        nfl2k5_franchise_signing_context(&observation);require(submissions==3); // No repeated inference.
        HANDLE thread=CreateThread(nullptr,0,foreign_submit,nullptr,0,nullptr);require(thread!=nullptr);
        require(WaitForSingleObject(thread,5000)==WAIT_OBJECT_0);DWORD code=1;
        require(GetExitCodeThread(thread,&code) && !code);CloseHandle(thread);require(submissions==3);
        observation.offer_amount=830;nfl2k5_franchise_signing_context(&observation);
        require(nfl2k5_franchise_submit_held(1)==1);
        nfl2k5_franchise_signing_context(&observation);
        require(submissions==4 && submitted["guest_offer"]["amount_word"]==830);
        nfl2k5_franchise_stop();
        _wputenv_s(L"NFL2K5_FRANCHISE_NEGOTIATION",L"0");require(nfl2k5_franchise_start()==1);
        require(nfl2k5_franchise_submit_held(1)==0);nfl2k5_franchise_stop();
        require(argc==1 || argc==2);
        if(argc==2) {
            std::ofstream receipt(argv[1]);receipt<<"held-signing-host-passed\n";receipt.close();require(receipt.good());
        }
        std::cout<<"Held signing host request/poll/duplicate/owner checks passed\n";return 0;
    } catch(const std::exception& error) { std::cerr<<error.what()<<"\n";nfl2k5_franchise_stop();return 1; }
}
