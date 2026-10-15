#include "host_client.h"
#include "pipe_client.h"
#include "signing_display.h"
#include "saved_signing.h"
#include "finance_state.h"
#include "identity_state.h"
#include <bcrypt.h>
#include <cstring>
#include <memory>
#include <string>

struct FranchiseHostClient {
    std::unique_ptr<franchise::PipeClient> transport;
    std::string reply,loaded_payload;
    DWORD owner=GetCurrentThreadId();
    bool pending = false;
    bool cached = false;
    bool ai_granted = false;
    bool journal_capable = false;
    std::string request;
    franchise::SavedSigningJournal candidate, journal;
    std::string operation;
};
static std::string signing_state_sha256(const unsigned char* bytes,size_t size) {
    BCRYPT_ALG_HANDLE algorithm=nullptr;unsigned char digest[32];
    if(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0)
        throw std::runtime_error("Signing state SHA256 unavailable");
    const auto hashed=BCryptHash(algorithm,nullptr,0,const_cast<PUCHAR>(bytes),static_cast<ULONG>(size),digest,sizeof(digest));
    BCryptCloseAlgorithmProvider(algorithm,0);
    if(hashed<0) throw std::runtime_error("Signing state SHA256 failed");
    std::string fingerprint;fingerprint.reserve(64);
    for(const auto byte:digest) {fingerprint+="0123456789abcdef"[byte>>4];fingerprint+="0123456789abcdef"[byte&15];}
    return fingerprint;
}
extern "C" FranchiseHostStatus franchise_host_signing_display(const char* response,FranchiseSigningDisplay* out) {
    if(!response || !out) return FRANCHISE_HOST_INVALID_ARGUMENT;
    *out={};
    try {
        auto text=franchise::signing_display(franchise::parse_frame(response));
        auto copy=[](char* target,size_t capacity,const std::string& source) {
            if(source.size()>=capacity) throw std::runtime_error("Display text exceeds capacity");
            std::memcpy(target,source.c_str(),source.size()+1);
        };
        copy(out->priorities,sizeof(out->priorities),text.priorities);
        copy(out->offer,sizeof(out->offer),text.offer);
        copy(out->history,sizeof(out->history),text.history);
        return FRANCHISE_HOST_OK;
    } catch(...) { *out={}; return FRANCHISE_HOST_INVALID_ARGUMENT; }
}

extern "C" FranchiseHostStatus franchise_host_create(const wchar_t* python, const wchar_t* database,
    FranchiseHostMode mode, FranchiseHostClient** out_client) {
    if (!out_client) return FRANCHISE_HOST_INVALID_ARGUMENT;
    *out_client = nullptr;
    if (!python || !*python || !database || !*database ||
        (mode != FRANCHISE_HOST_OFFLINE_FIXTURE && mode != FRANCHISE_HOST_VERTEX_RUNTIME))
        return FRANCHISE_HOST_INVALID_ARGUMENT;
    try {
        auto client = std::make_unique<FranchiseHostClient>();
        client->transport = std::make_unique<franchise::PipeClient>(python,database,
            mode == FRANCHISE_HOST_OFFLINE_FIXTURE ? franchise::ServiceMode::OfflineFixture : franchise::ServiceMode::VertexRuntime);
        *out_client = client.release();
        return FRANCHISE_HOST_OK;
    } catch (...) { return FRANCHISE_HOST_SERVICE_FAILURE; }
}

extern "C" FranchiseHostStatus franchise_host_create_with_budget(const wchar_t* python,const wchar_t* database,
    FranchiseHostMode mode,const wchar_t* budget_database,const wchar_t* budget_scope,
    unsigned long long request_limit,FranchiseHostClient** out_client) {
    if(!out_client) return FRANCHISE_HOST_INVALID_ARGUMENT;
    *out_client=nullptr;
    if(!python || !database || !budget_database || !budget_scope || mode!=FRANCHISE_HOST_VERTEX_RUNTIME)
        return FRANCHISE_HOST_INVALID_ARGUMENT;
    try {
        franchise::BudgetLaunch budget{budget_database,budget_scope,request_limit};
        franchise::launch_command(python,database,franchise::ServiceMode::VertexRuntime,budget);
        auto client=std::make_unique<FranchiseHostClient>();
        client->transport=std::make_unique<franchise::PipeClient>(python,database,franchise::ServiceMode::VertexRuntime,budget);
        *out_client=client.release();return FRANCHISE_HOST_OK;
    } catch(const std::invalid_argument&) { return FRANCHISE_HOST_INVALID_ARGUMENT; }
      catch(...) { return FRANCHISE_HOST_SERVICE_FAILURE; }
}

extern "C" FranchiseHostStatus franchise_host_create_with_token_budget(const wchar_t* python,const wchar_t* database,
    FranchiseHostMode mode,const wchar_t* budget_database,const wchar_t* budget_scope,
    unsigned long long request_limit,unsigned long long token_limit,FranchiseHostClient** out_client) {
    if(!out_client) return FRANCHISE_HOST_INVALID_ARGUMENT;
    *out_client=nullptr;
    if(!python || !database || !budget_database || !budget_scope || mode!=FRANCHISE_HOST_VERTEX_RUNTIME)
        return FRANCHISE_HOST_INVALID_ARGUMENT;
    try {
        franchise::BudgetLaunch budget{budget_database,budget_scope,request_limit,token_limit};
        franchise::launch_command(python,database,franchise::ServiceMode::VertexRuntime,budget);
        auto client=std::make_unique<FranchiseHostClient>();
        client->transport=std::make_unique<franchise::PipeClient>(python,database,franchise::ServiceMode::VertexRuntime,budget);
        *out_client=client.release();return FRANCHISE_HOST_OK;
    } catch(const std::invalid_argument&) { return FRANCHISE_HOST_INVALID_ARGUMENT; }
      catch(...) { return FRANCHISE_HOST_SERVICE_FAILURE; }
}

extern "C" FranchiseHostStatus franchise_host_submit(FranchiseHostClient* client, const char* bytes, size_t length) {
    if (!client || !bytes || !length || length > 4095 || std::memchr(bytes,0,length) ||
        std::memchr(bytes,'\r',length) || std::memchr(bytes,'\n',length)) return FRANCHISE_HOST_INVALID_ARGUMENT;
    if (client->pending || client->cached) return FRANCHISE_HOST_BUSY;
    std::string frame, operation;
    try {
        frame.assign(bytes,length);
        const auto request = franchise::parse_frame(frame);
        if (!request.is_object() || !request.contains("request_id") || !request.at("request_id").is_string() ||
            request.at("request_id").get<std::string>().empty() || !request.contains("operation") ||
            !request.at("operation").is_string() || request.at("operation").get<std::string>().empty()) return FRANCHISE_HOST_INVALID_ARGUMENT;
        operation = request.at("operation").get<std::string>();
    } catch (...) { return FRANCHISE_HOST_INVALID_ARGUMENT; }
    const bool journal_write=operation=="guest_signing_prepare" || operation=="guest_signing_confirm";
    if ((operation == "negotiate" || operation == "negotiate_proposal" || journal_write) && !client->ai_granted)
        return FRANCHISE_HOST_SERVICE_FAILURE;
    if(journal_write && !client->journal_capable)
        return FRANCHISE_HOST_SERVICE_FAILURE;
    try {
        if(operation=="hello" || operation=="bind_runtime"){client->loaded_payload.clear();client->ai_granted=false;}
        client->transport->submit(std::move(frame));
        client->request.assign(bytes,length);
        client->candidate={};
        client->operation = std::move(operation);
        client->pending = true;
        return FRANCHISE_HOST_OK;
    } catch (...) { client->ai_granted = false;client->loaded_payload.clear(); return FRANCHISE_HOST_SERVICE_FAILURE; }
}

static bool valid_signing_images(const void* finance_state,size_t finance_size,const void* identity_state,size_t identity_size) {
    const auto* image=static_cast<const unsigned char*>(finance_state);
    if(!image || finance_size<FRANCHISE_FINANCE_HEADER || finance_size>sizeof(FranchiseFinanceSnapshot::bytes) ||
       finance_get32(image)!=1 || !finance_get32(image+4) || finance_get32(image+4)>FRANCHISE_FINANCE_MAX_PLAYERS ||
       finance_size!=FRANCHISE_FINANCE_HEADER+FRANCHISE_FINANCE_RECORD*finance_get32(image+4) ||
       finance_get32(image+8)!=2 || finance_get32(image+24)!=32 || finance_get32(image+44))
        return false;
    const auto* identities=static_cast<const unsigned char*>(identity_state);
    if(!identities || identity_size<FRANCHISE_IDENTITY_HEADER || identity_size>sizeof(FranchiseIdentitySnapshot::bytes) ||
       finance_get32(identities)!=1 || finance_get32(identities+4)!=finance_get32(image+4) ||
       finance_get32(identities+8)>finance_get32(image+4) ||
       identity_size!=FRANCHISE_IDENTITY_HEADER+FRANCHISE_IDENTITY_RECORD*finance_get32(identities+8))
        return false;
    return true;
}

extern "C" FranchiseHostStatus franchise_host_prepare_accepted(FranchiseHostClient* client,const void* finance_state,size_t finance_size,
                                                              const void* identity_state,size_t identity_size) {
    if(!client) return FRANCHISE_HOST_INVALID_ARGUMENT;
    if(client->pending || client->cached) return FRANCHISE_HOST_BUSY;
    if(client->candidate.preparation.is_null()) return FRANCHISE_HOST_NOT_READY;
    if(!client->ai_granted || !client->journal_capable) return FRANCHISE_HOST_SERVICE_FAILURE;
    if(!valid_signing_images(finance_state,finance_size,identity_state,identity_size)) return FRANCHISE_HOST_INVALID_ARGUMENT;
    const auto* image=static_cast<const unsigned char*>(finance_state);
    const auto* identities=static_cast<const unsigned char*>(identity_state);
    try {
        auto journal=client->candidate;
        journal.preparation["live_finance_sha256"]=signing_state_sha256(image,finance_size);
        journal.preparation["live_identity_sha256"]=signing_state_sha256(identities,identity_size);
        const auto request=journal.preparation.dump();
        const auto status=franchise_host_submit(client,request.data(),request.size());
        if(status==FRANCHISE_HOST_OK) client->journal=std::move(journal);
        return status;
    } catch(...) {client->ai_granted=false;client->loaded_payload.clear();return FRANCHISE_HOST_SERVICE_FAILURE;}
}

extern "C" FranchiseHostStatus franchise_host_observe_completed(FranchiseHostClient* client,const void* finance_state,size_t finance_size,
                                                               const void* identity_state,size_t identity_size) {
    if(!client || !valid_signing_images(finance_state,finance_size,identity_state,identity_size)) return FRANCHISE_HOST_INVALID_ARGUMENT;
    try {
        client->journal.observe_completed(signing_state_sha256(static_cast<const unsigned char*>(finance_state),finance_size),
                                          signing_state_sha256(static_cast<const unsigned char*>(identity_state),identity_size));
        return FRANCHISE_HOST_OK;
    } catch(...) {client->ai_granted=false;client->loaded_payload.clear();return FRANCHISE_HOST_SERVICE_FAILURE;}
}

extern "C" FranchiseHostStatus franchise_host_check_saved(FranchiseHostClient* client) {
    if(!client) return FRANCHISE_HOST_INVALID_ARGUMENT;
    if(client->pending || client->cached) return FRANCHISE_HOST_BUSY;
    try {
        const auto next=client->journal.next(client->ai_granted);
        if(next.is_null()) return FRANCHISE_HOST_NOT_READY;
        const auto request=next.dump();
        return franchise_host_submit(client,request.data(),request.size());
    } catch(...) {client->ai_granted=false;client->loaded_payload.clear();return FRANCHISE_HOST_SERVICE_FAILURE;}
}

extern "C" FranchiseHostStatus franchise_host_ready(FranchiseHostClient* client, int* ready_out) {
    if (!ready_out) return FRANCHISE_HOST_INVALID_ARGUMENT;
    *ready_out = 0;
    if (!client) return FRANCHISE_HOST_INVALID_ARGUMENT;
    try {
        *ready_out = client->cached || (client->pending && client->transport->ready());
        return FRANCHISE_HOST_OK;
    } catch (...) { return FRANCHISE_HOST_SERVICE_FAILURE; }
}

extern "C" FranchiseHostStatus franchise_host_take(FranchiseHostClient* client, char* buffer,
    size_t capacity, size_t* required_size) {
    if (!required_size) return FRANCHISE_HOST_INVALID_ARGUMENT;
    *required_size = 0;
    if (!client || (!buffer && capacity)) return FRANCHISE_HOST_INVALID_ARGUMENT;
    try {
        if (!client->cached) {
            if (!client->pending || !client->transport->ready()) return FRANCHISE_HOST_NOT_READY;
            client->pending = false;
            client->reply = client->transport->take();
            const auto response = franchise::parse_frame(client->reply); // Already transport-validated.
            if (client->operation == "hello" || client->operation == "bind_runtime") {
                client->ai_granted = client->operation=="hello" && response.at("error").is_null() &&
                    response.at("result").at("ai_enabled").is_boolean() && response.at("result").at("ai_enabled") == true;
                client->journal_capable=false;client->loaded_payload.clear();
                if(response.at("error").is_null() && response.at("result").contains("runtime_binding"))
                    client->loaded_payload=response.at("result").at("runtime_binding").at("snapshot_payload_sha256").get<std::string>();
                if(client->ai_granted) {
                    const auto& ops=response.at("result").at("operations");
                    client->journal_capable=true;
                    for(const auto* name:{"guest_signing_prepare","guest_signing_confirm","guest_signing_status"})
                        client->journal_capable=client->journal_capable && std::find(ops.begin(),ops.end(),name)!=ops.end();
                }
            }
            if (response.at("error") == "ai_disabled") client->ai_granted = false;
            const auto request=franchise::parse_frame(client->request);
            client->journal.consume(request,response);
            client->candidate=franchise::SavedSigningJournal::capture(request,response);
            client->cached = true;
        }
        *required_size = client->reply.size()+1;
        if (!buffer || capacity < *required_size) return FRANCHISE_HOST_BUFFER_TOO_SMALL;
        std::memcpy(buffer,client->reply.c_str(),*required_size);
        client->reply.clear();
        client->cached = false;
        return FRANCHISE_HOST_OK;
    } catch (...) { client->ai_granted = false;client->loaded_payload.clear();client->transport->abort();return FRANCHISE_HOST_SERVICE_FAILURE; }
}

extern "C" void franchise_host_destroy(FranchiseHostClient* client) {
    try { delete client; } catch (...) { /* Static C boundary; no exception text. */ }
}

extern "C" FranchiseHostStatus franchise_host_loaded_payload_matches(FranchiseHostClient* client,const char* sha256) {
    if(!client || !sha256 || GetCurrentThreadId()!=client->owner)return FRANCHISE_HOST_INVALID_ARGUMENT;
    if(client->loaded_payload.size()!=64)return FRANCHISE_HOST_NOT_READY;
    for(size_t i=0;i<64;++i)if(!sha256[i] || client->loaded_payload[i]!=sha256[i])return FRANCHISE_HOST_INVALID_ARGUMENT;
    return sha256[64]==0 ? FRANCHISE_HOST_OK : FRANCHISE_HOST_INVALID_ARGUMENT;
}
