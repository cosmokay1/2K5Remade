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
static DWORD owner;
static bool ready;
static unsigned preparations;
static FranchiseHostStatus preparation_status=FRANCHISE_HOST_NOT_READY;
static void require(bool ok) { if(!ok) throw std::runtime_error("Held signing host invariant failed"); }
FranchiseHostStatus franchise_host_create(const wchar_t*,const wchar_t*,FranchiseHostMode mode,FranchiseHostClient** out) {
    require(mode==FRANCHISE_HOST_VERTEX_RUNTIME);client.pending=false;*out=&client;return FRANCHISE_HOST_OK;
}
FranchiseHostStatus franchise_host_create_with_budget(const wchar_t* p,const wchar_t* d,FranchiseHostMode m,
    const wchar_t*,const wchar_t*,unsigned long long,FranchiseHostClient** out) { return franchise_host_create(p,d,m,out); }
FranchiseHostStatus franchise_host_create_with_token_budget(const wchar_t* p,const wchar_t* d,FranchiseHostMode m,
    const wchar_t*,const wchar_t*,unsigned long long,unsigned long long,FranchiseHostClient** out) { return franchise_host_create(p,d,m,out); }
FranchiseHostStatus franchise_host_submit(FranchiseHostClient* c,const char* bytes,size_t length) {
    require(GetCurrentThreadId()==owner && !c->pending);submitted=franchise::parse_frame(std::string(bytes,length));
    require(submitted.at("protocol")==1);++submissions;c->pending=true;return FRANCHISE_HOST_OK;
}
FranchiseHostStatus franchise_host_ready(FranchiseHostClient*,int* out) { require(GetCurrentThreadId()==owner);*out=ready;return FRANCHISE_HOST_OK; }
FranchiseHostStatus franchise_host_prepare_accepted(FranchiseHostClient* c) {
    require(GetCurrentThreadId()==owner && !c->pending);++preparations;
    if(preparation_status!=FRANCHISE_HOST_OK) return preparation_status;
    const std::string request=R"({"protocol":1,"request_id":"authored-guest","operation":"guest_signing_prepare"})";
    return franchise_host_submit(c,request.data(),request.size());
}
FranchiseHostStatus franchise_host_take(FranchiseHostClient* c,char* buffer,size_t capacity,size_t* required) {
    require(GetCurrentThreadId()==owner && c->pending && ready);const char response[]="{\"fixture\":true}";
    require(capacity>=sizeof(response));std::memcpy(buffer,response,sizeof(response));*required=sizeof(response);
    c->pending=false;return FRANCHISE_HOST_OK;
}
FranchiseHostStatus franchise_host_signing_display(const char*,FranchiseSigningDisplay* out) {
    *out={};std::strcpy(out->offer,"Authored response");return FRANCHISE_HOST_OK;
}
void franchise_host_destroy(FranchiseHostClient*) { client.pending=false; }
struct SubmitIntent { FranchiseSigningObservation observation; unsigned long long epoch; };
static DWORD WINAPI foreign_submit(void* data) {
    const auto* intent=static_cast<SubmitIntent*>(data);
    return nfl2k5_franchise_submit_held(&intent->observation,intent->epoch)==1 ? 0 : 1;
}
static void submit_foreign(const FranchiseSigningObservation& observation,unsigned long long epoch) {
    SubmitIntent intent={observation,epoch};
    HANDLE thread=CreateThread(nullptr,0,foreign_submit,&intent,0,nullptr);require(thread!=nullptr);
    require(WaitForSingleObject(thread,5000)==WAIT_OBJECT_0);DWORD code=1;
    require(GetExitCodeThread(thread,&code) && !code);CloseHandle(thread);
}
int main(int argc,char** argv) {
    try {
        owner=GetCurrentThreadId();
        _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_SIGNING",L"0");
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
        require(nfl2k5_franchise_submit_held(&observation,nfl2k5_franchise_submission_epoch())==1);
        ready=false;nfl2k5_franchise_poll();require(submissions==2);
        ready=true;nfl2k5_franchise_poll();
        nfl2k5_franchise_signing_context(&observation);
        require(submissions==3 && submitted["operation"]=="negotiate_proposal");
        require(!submitted.contains("performance_format") && submitted["guest_offer"]["amount_word"]==829);
        require(submitted["expected_revision"]==0 && submitted["observation"]["biography"]["first_name"]=="Authored");
        nfl2k5_franchise_poll();
        require(nfl2k5_franchise_submit_held(&observation,nfl2k5_franchise_submission_epoch())==1);
        nfl2k5_franchise_signing_context(&observation);require(submissions==3); // No repeated inference.
        submit_foreign(observation,nfl2k5_franchise_submission_epoch());
        nfl2k5_franchise_signing_context(&observation);require(submissions==3);
        observation.offer_amount=830;nfl2k5_franchise_signing_context(&observation);
        require(nfl2k5_franchise_submit_held(&observation,nfl2k5_franchise_submission_epoch())==1);
        nfl2k5_franchise_signing_context(&observation);
        require(submissions==4 && submitted["guest_offer"]["amount_word"]==830);
        nfl2k5_franchise_poll();
        // A foreign callback copies current terms; only a fresh owner sample submits.
        observation.offer_amount=831;
        submit_foreign(observation,nfl2k5_franchise_submission_epoch());require(submissions==4);
        nfl2k5_franchise_signing_context(&observation);
        require(submissions==5 && submitted["operation"]=="negotiate_proposal" && submitted["guest_offer"]["amount_word"]==831);
        nfl2k5_franchise_poll();
        // Changed terms, invalid samples and screen changes discard old intent.
        observation.offer_amount=832;
        submit_foreign(observation,nfl2k5_franchise_submission_epoch());
        observation.offer_amount=833;nfl2k5_franchise_signing_context(&observation);require(submissions==5);
        submit_foreign(observation,nfl2k5_franchise_submission_epoch());
        nfl2k5_franchise_signing_context(nullptr);nfl2k5_franchise_signing_context(&observation);require(submissions==5);
        const auto old_epoch=nfl2k5_franchise_submission_epoch();
        submit_foreign(observation,old_epoch);
        nfl2k5_franchise_on_fsm(0,0);nfl2k5_franchise_on_fsm(0x557B2C,1);
        submit_foreign(observation,old_epoch);
        nfl2k5_franchise_signing_context(&observation);
        require(submissions==6 && submitted["operation"]=="signing_context");
        submit_foreign(observation,nfl2k5_franchise_submission_epoch());
        nfl2k5_franchise_signing_context(&observation); // Intent consumed while the read is pending.
        nfl2k5_franchise_signing_context(nullptr); // Must cancel that consumed intent too.
        nfl2k5_franchise_poll();nfl2k5_franchise_signing_context(&observation);
        require(submissions==7 && submitted["operation"]=="signing_context");nfl2k5_franchise_poll();
        // Malformed input is held without creating a proposal or reading past strings.
        auto malformed=observation;std::memset(malformed.first_name,'x',sizeof(malformed.first_name));
        submit_foreign(malformed,nfl2k5_franchise_submission_epoch());
        require(nfl2k5_franchise_submit_held(nullptr,nfl2k5_franchise_submission_epoch())==1);
        nfl2k5_franchise_signing_context(&observation);require(submissions==7);
        require(preparations==0); // Opt-in default never prepares a journal.
        nfl2k5_franchise_stop();
        _wputenv_s(L"NFL2K5_FRANCHISE_NEGOTIATION",L"0");require(nfl2k5_franchise_start()==1);
        require(nfl2k5_franchise_submit_held(&observation,nfl2k5_franchise_submission_epoch())==0);nfl2k5_franchise_stop();
        _wputenv_s(L"NFL2K5_FRANCHISE_GUEST_SIGNING",L"1");
        require(nfl2k5_franchise_start()==0); // Requires held negotiation.
        _wputenv_s(L"NFL2K5_FRANCHISE_NEGOTIATION",L"1");
        for(auto status:{FRANCHISE_HOST_OK,FRANCHISE_HOST_NOT_READY,FRANCHISE_HOST_SERVICE_FAILURE}) {
            preparation_status=status;preparations=0;
            require(nfl2k5_franchise_start()==1);
            nfl2k5_franchise_on_fsm(0x557B2C,1);nfl2k5_franchise_poll();
            nfl2k5_franchise_signing_context(&observation);nfl2k5_franchise_poll();
            submit_foreign(observation,nfl2k5_franchise_submission_epoch());
            nfl2k5_franchise_signing_context(&observation);nfl2k5_franchise_poll();
            require(preparations==1);
            if(status==FRANCHISE_HOST_OK) {
                require(submitted["operation"]=="guest_signing_prepare");
                // Navigate away with preparation pending, then consume it.
                nfl2k5_franchise_on_fsm(0,0);nfl2k5_franchise_poll();
            }
            const auto count=submissions;
            nfl2k5_franchise_on_fsm(0x557B2C,1);
            ++observation.offer_amount;
            submit_foreign(observation,nfl2k5_franchise_submission_epoch());
            nfl2k5_franchise_signing_context(&observation);
            if(status!=FRANCHISE_HOST_NOT_READY) require(submissions==count && preparations==1);
            require(nfl2k5_franchise_submit_held(nullptr,0)==1); // Never releases retail judgment.
            nfl2k5_franchise_stop();
        }
        // Obsolete acceptance must never reserve a signing.
        preparations=0;preparation_status=FRANCHISE_HOST_OK;
        require(nfl2k5_franchise_start()==1);
        nfl2k5_franchise_on_fsm(0x557B2C,1);nfl2k5_franchise_poll();
        nfl2k5_franchise_signing_context(&observation);nfl2k5_franchise_poll();
        submit_foreign(observation,nfl2k5_franchise_submission_epoch());
        nfl2k5_franchise_signing_context(&observation);
        ++observation.offer_amount;nfl2k5_franchise_signing_context(&observation);
        nfl2k5_franchise_poll();require(preparations==0);nfl2k5_franchise_stop();
        require(argc==1 || argc==2);
        if(argc==2) {
            std::ofstream receipt(argv[1]);receipt<<"held-signing-host-passed\n";receipt.close();require(receipt.good());
        }
        std::cout<<"Held signing host request/poll/duplicate/foreign handoff/stale intent checks passed\n";return 0;
    } catch(const std::exception& error) { std::cerr<<error.what()<<"\n";nfl2k5_franchise_stop();return 1; }
}
