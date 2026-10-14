#include "host_client.h"
#include "pipe_client.h"
#include <cstring>
#include <memory>
#include <string>

struct FranchiseHostClient {
    std::unique_ptr<franchise::PipeClient> transport;
    std::string reply;
    bool pending = false;
    bool cached = false;
    bool ai_granted = false;
    std::string operation;
};

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
    if ((operation == "negotiate" || operation == "negotiate_proposal") && !client->ai_granted)
        return FRANCHISE_HOST_SERVICE_FAILURE;
    try {
        client->transport->submit(std::move(frame));
        client->operation = std::move(operation);
        client->pending = true;
        return FRANCHISE_HOST_OK;
    } catch (...) { client->ai_granted = false; return FRANCHISE_HOST_SERVICE_FAILURE; }
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
            if (client->operation == "hello")
                client->ai_granted = response.at("error").is_null() &&
                    response.at("result").at("ai_enabled").is_boolean() && response.at("result").at("ai_enabled") == true;
            if (response.at("error") == "ai_disabled") client->ai_granted = false;
            client->cached = true;
        }
        *required_size = client->reply.size()+1;
        if (!buffer || capacity < *required_size) return FRANCHISE_HOST_BUFFER_TOO_SMALL;
        std::memcpy(buffer,client->reply.c_str(),*required_size);
        client->reply.clear();
        client->cached = false;
        return FRANCHISE_HOST_OK;
    } catch (...) { client->ai_granted = false; return FRANCHISE_HOST_SERVICE_FAILURE; }
}

extern "C" void franchise_host_destroy(FranchiseHostClient* client) {
    try { delete client; } catch (...) { /* Static C boundary; no exception text. */ }
}
