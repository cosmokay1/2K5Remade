/* Real addon drawing and host input hooks; authored data, no game/AI process. */
#include "negotiation_screen_fixture.h"
#include "../../src/nfl2k5_franchise_host.h"
#include <windows.h>
#include <wincodec.h>
#include <filesystem>
#include <cstring>
#include <cstdio>
extern "C" int franchise_negotiation_screen_event(const char*,const void*,size_t);
extern "C" int nfl2k5_addon_event(const char *name,const void *data,size_t size) {
    return franchise_negotiation_screen_event(name,data,size);
}
static nlohmann::json fixture;
static bool available=true,loading=false;
static bool editing=false,checking=false;
static unsigned long long preview_epoch=1;
static unsigned preview_calls;
static uint32_t preview_amount;
static bool submitting=false,agent_waiting=false;
static unsigned submit_calls;
static std::string notice;
extern "C" int nfl2k5_franchise_send_offer(unsigned long long epoch,uint32_t amount,uint32_t flags) {
    if(!submitting || checking || epoch!=preview_epoch || !amount || !flags) return 0;
    ++submit_calls;checking=agent_waiting=true;++preview_epoch;return 1;
}
extern "C" int nfl2k5_franchise_preview_offer(unsigned long long epoch,uint32_t amount,uint32_t flags) {
    if(epoch!=preview_epoch || checking || !amount || !flags) return 0;
    ++preview_calls;preview_amount=amount;checking=true;++preview_epoch;return 1;
}
extern "C" int nfl2k5_franchise_negotiation_view(FranchiseNegotiationView *out) {
    *out={};if(!available) return 0;
    if(loading) {std::strcpy(out->summary.title,"Contract negotiation");return 1;}
    const auto response=fixture.dump();if(response.size()>=sizeof(out->response)) return 0;
    std::memcpy(out->response,response.c_str(),response.size()+1);
    out->preview_enabled=editing;out->preview_pending=checking;out->preview_epoch=preview_epoch;
    out->submit_enabled=submitting && !checking;out->proposal_pending=agent_waiting;
    std::snprintf(out->notice,sizeof(out->notice),"%s",notice.c_str());
    std::strcpy(out->summary.title,"Authored Player");
    std::strcpy(out->summary.offer,"Read-only preview. Contract application is held.");return 1;
}
static void require(bool ok,const char *message){if(!ok) throw std::runtime_error(message);}
static void png(const std::filesystem::path& path,int width,int height,const void *pixels) {
    IWICImagingFactory *factory=nullptr;IWICStream *stream=nullptr;IWICBitmapEncoder *encoder=nullptr;
    IWICBitmapFrameEncode *frame=nullptr;
    auto ok=[](HRESULT status){require(SUCCEEDED(status),"PNG encoding failed");};
    ok(CoCreateInstance(CLSID_WICImagingFactory,nullptr,CLSCTX_INPROC_SERVER,IID_PPV_ARGS(&factory)));
    ok(factory->CreateStream(&stream));ok(stream->InitializeFromFilename(path.c_str(),GENERIC_WRITE));
    ok(factory->CreateEncoder(GUID_ContainerFormatPng,nullptr,&encoder));ok(encoder->Initialize(stream,WICBitmapEncoderNoCache));
    ok(encoder->CreateNewFrame(&frame,nullptr));ok(frame->Initialize(nullptr));ok(frame->SetSize(width,height));
    WICPixelFormatGUID format=GUID_WICPixelFormat32bppBGRA;ok(frame->SetPixelFormat(&format));
    require(IsEqualGUID(format,GUID_WICPixelFormat32bppBGRA),"PNG format changed");
    ok(frame->WritePixels(height,width*4,width*height*4,const_cast<BYTE*>(static_cast<const BYTE*>(pixels))));
    ok(frame->Commit());ok(encoder->Commit());frame->Release();encoder->Release();stream->Release();factory->Release();
}
static void press(int analog,int button=0) {
    NFL2K5AddonInput input{};nfl2k5_addon_ui_input(&input);
    if(analog>=0) input.analog[analog]=255;
    input.buttons=0;if(button==2) input.axes[3]=-24000;else if(button==1) input.axes[3]=24000;else input.buttons=button;
    nfl2k5_addon_ui_input(&input);
}
int main(int argc,char** argv) {
    if(argc!=2) return 1;
    try {
        CoInitializeEx(nullptr,COINIT_MULTITHREADED);
        std::filesystem::path output=argv[1];std::filesystem::create_directories(output);
        _putenv_s("NFL2K5_FRANCHISE_SCREEN_PREVIEW","");_putenv_s("NFL2K5_FRANCHISE_SCREEN_PORT","0");
        const void *pixels=nullptr;int changed=0;
        fixture=negotiation_screen_fixture();
        require(!nfl2k5_addon_ui_draw(1280,800,&pixels,&changed),"Preview must default off");
        _putenv_s("NFL2K5_FRANCHISE_SCREEN_PREVIEW","1");
        _putenv_s("NFL2K5_FRANCHISE_NEGOTIATION","1");
        require(!nfl2k5_addon_ui_draw(1280,800,&pixels,&changed),"Read-only preview accepted negotiation mode");
        _putenv_s("NFL2K5_FRANCHISE_NEGOTIATION","0");
        _putenv_s("NFL2K5_FRANCHISE_GUEST_SIGNING","0");
        _putenv_s("NFL2K5_FRANCHISE_SCREEN_PORT","bad");
        require(!nfl2k5_addon_ui_draw(1280,800,&pixels,&changed),"Invalid controller port accepted");
        _putenv_s("NFL2K5_FRANCHISE_SCREEN_PORT","0");
        for(const int height:{800,720}) {
            fixture=negotiation_screen_fixture();fixture["request_id"]=std::to_string(height);
            auto capture=[&](const char *name){
                require(nfl2k5_addon_ui_draw(1280,height,&pixels,&changed),"Real addon renderer did not produce a frame");
                const auto* data=static_cast<const unsigned char*>(pixels);
                size_t light=0;for(int i=0;i<1280*height;++i){require(data[i*4+3]==255,"Full-screen alpha must be opaque");if(data[i*4]>80)++light;}
                require(light>2000,"Text was not rendered");
                png(output/(std::to_string(height)+"-"+name+".png"),1280,height,pixels);
            };
            loading=true;capture("loading");require(changed,"Loading view must render before any reply");
            loading=false;capture("contract");require(changed,"First context needs pixels");
            require(nfl2k5_addon_ui_draw(1280,height,&pixels,&changed) && !changed,"Unchanged screen redrew");
            editing=true;capture("editable-contract");press(0);capture("edit-offer");
            press(-1,8);capture("edit-adjusted");
            press(3);require(nfl2k5_addon_ui_draw(1280,height,&pixels,&changed) && !changed,"Y still switches contract tabs");
            press(4);capture("current-while-editing");
            press(5);capture("return-to-retained-edit");
            press(1);capture("review-retained-draft");
            for(int i=0;i<4;++i) {press(7);capture((std::string("draft-section-")+std::to_string(i)).c_str());}
            press(0);capture("resume-retained-draft");
            const auto before_checks=preview_calls;press(2);capture("edit-checking");
            require(preview_calls==before_checks+1,"Explicit check was not queued");
            require(preview_amount==423,"Switching current/review/sections lost the edited amount");
            press(2);require(preview_calls==before_checks+1,"Repeated check escaped pending guard");
            press(4);capture("current-during-check");
            checking=false;++preview_epoch;
            fixture["request_id"]="checked-draft-"+std::to_string(height);
            auto& checked=fixture["result"]["offer_context"];
            checked["amount_word"]=preview_amount;
            checked["offer"]["salaries"]=nlohmann::json::array();checked["preview"]["contract_charges"]=nlohmann::json::array();
            for(const auto& row:franchise::guest_annual_rows(preview_amount,4,1,2,4)) {
                checked["offer"]["salaries"].push_back(row.salary);checked["preview"]["contract_charges"].push_back(row.charge());
            }
            checked["offer"]["signing_bonus"]=preview_amount*4*1000*4;
            capture("current-after-checked-reply");
            press(1);capture("checked-offer-return");
            press(0);capture("unchanged-edit");press(2);capture("unchanged-checking");
            checking=false;++preview_epoch;capture("edit-checked-identical-reply");
            press(0);capture("edit-again");press(1);capture("edit-cancelled");
            require(nfl2k5_addon_ui_draw(1280,height,&pixels,&changed),"Cancel left the native screen");
            editing=false;capture("editing-disabled");
            NFL2K5AddonInput other{};other.port=1;other.analog[7]=255;nfl2k5_addon_ui_input(&other);
            require(!other.analog[7],"Other port reached the native menu");
            require(nfl2k5_addon_ui_draw(1280,height,&pixels,&changed) && !changed,"Other port navigated the view");
            press(7);capture("performance");press(7);capture("personality");press(7);capture("agent-empty");
            for(const auto* trait:{"money","security","playing_time","winning","loyalty"}) {
                fixture=negotiation_screen_fixture();fixture["request_id"]=std::string("trait-")+trait+std::to_string(height);
                fixture["result"]["player_context"]["personality"][trait]=1;
                fixture["result"]["player_context"]["relationships"]={{"trust",0},{"respect",1},{"team_connection",nullptr}};
                capture((std::string("trait-")+trait).c_str());press(7);press(7);
                capture((std::string("bars-")+trait).c_str());
            }
            fixture=negotiation_screen_fixture();fixture["request_id"]="before-counter"+std::to_string(height);
            auto checkpoint=fixture["result"];
            fixture["result"]={{"signing_checkpoint",checkpoint},{"counter",checkpoint["offer_context"]["offer"]},
                {"offer",checkpoint["offer_context"]["offer"]},{"counter_validation",{{"status","eligible"}}},{"reason",
                    u8"We\u2019d appreciate a clear role as much as the money in this offer. "
                    "We want a clear path to starting and a deal that reflects the production in the records you have. "
                    "Where the records are missing, we should talk about that uncertainty rather than assume the worst. "
                    "Our counter keeps the annual salaries and bonus explicit so you can review the cap impact. "
                    "This is a proposal, and we are waiting for your response. END OF AGENT RESPONSE."}};
            fixture["request_id"]="authored-counter"+std::to_string(height);
            capture("counter-contract");press(7);press(7);press(7);capture("agent-full");
            for(int i=0;i<12;++i)press(-1,2);capture("agent-bottom");
            press(-1,1);capture("agent-up"); // end clamping must allow immediate upward movement
            fixture["request_id"]="short-conversation"+std::to_string(height);
            fixture["result"]["counter"]=nullptr;
            fixture["result"]["reason"]="The term works for us. Before we agree, we need to discuss his role on the team.";
            capture("conversation-short-contract");press(7);press(7);press(7);capture("conversation-short");
            // Exactly one native B pulse, then quarantine the held B button.
            NFL2K5AddonInput input{};nfl2k5_addon_ui_input(&input);input.analog[1]=255;
            nfl2k5_addon_ui_input(&input);require(input.analog[1]==255,"Back did not leave the native offer menu");
            input.analog[1]=255;nfl2k5_addon_ui_input(&input);require(!input.analog[1],"Held Back leaked twice");
            require(!nfl2k5_addon_ui_draw(1280,height,&pixels,&changed),"Closed screen remained visible");
            input={};nfl2k5_addon_ui_input(&input);
            available=false;nfl2k5_addon_ui_draw(1280,height,&pixels,&changed);available=true;
            fixture=negotiation_screen_fixture();fixture["request_id"]="missing-history"+std::to_string(height);
            fixture["result"]["performance_context"]["saved_history"]=nlohmann::json::array();
            capture("missing-contract");press(7);capture("missing-performance");
            fixture=negotiation_screen_fixture();fixture["request_id"]="receiving"+std::to_string(height);
            fixture["result"]["performance_context"]["saved_history"]=nlohmann::json::array();
            for(int period=1;period<=2;++period) {
                const std::pair<const char*,int> entries[]={{"games",period==1?15:4},{"receptions",period==1?109:18},
                    {"receiving_yards",period==1?1204:271},{"receiving_touchdowns",period==1?7:2}};
                for(const auto& entry:entries) fixture["result"]["performance_context"]["saved_history"].push_back(
                    {{"metric",entry.first},{"value",entry.second},{"unit",std::string(entry.first)=="receiving_yards"?"yards":"count"},{"period_code_raw",period},{"mode_code_raw",0},{"candidate_calendar_year",2001+period}});
            }
            capture("receiver-contract");press(7);capture("receiver-performance");
            fixture=negotiation_screen_fixture();fixture["request_id"]="ineligible"+std::to_string(height);
            fixture["result"]["offer_context"]["preview"]=nullptr;
            fixture["result"]["offer_context"]["reason"]="The salary minimum has not been classified. Player classification must be resolved before an offer can be evaluated.";
            capture("ineligible-offer");
            fixture=negotiation_screen_fixture();fixture["request_id"]="legacy-amendment"+std::to_string(height);
            auto& amendment=fixture["result"]["offer_context"];
            amendment["outcome"]="amendment_comparison";
            amendment["preview"]=nullptr;
            amendment["offer"]={{"salaries",{4708000,7060000,9412000}},{"signing_bonus",21180000},{"guaranteed_salaries",{0,0,0}}};
            amendment["amendment"]={{"current_charges",{3864000,4640000,5412000}},
                {"carried_bonus_charges",{2320000,2320000,2320000}},
                {"combined_player_charges",{14088000,16440000,18792000}},{"room_before",89216000},{"room_after",78992000}};
            capture("legacy-amendment");
            editing=true;capture("legacy-edit-enabled");press(0);press(-1,8);capture("legacy-unchecked-edit");
            press(4);capture("legacy-current-unchecked-edit");press(5);capture("legacy-retained-unchecked-edit");
            editing=false;
            fixture=negotiation_screen_fixture();fixture["request_id"]="long-contract"+std::to_string(height);
            fixture["result"]["offer_context"]["offer"]={{"salaries",{1000000,1000000,1000000,1000000,1000000,1000000,1000000}},
                {"signing_bonus",0},{"guaranteed_salaries",{0,0,0,0,0,0,0}}};
            fixture["result"]["offer_context"]["preview"]={{"contract_charges",{1000000,1000000,1000000,1000000,1000000,1000000,1000000}},{"room_after",10000000}};
            capture("long-contract-top");for(int i=0;i<20;++i)press(-1,2);capture("long-contract-bottom");
            // One reviewed submission, no held-button retries, recoverable service
            // error, read-only recheck, then an actual attributed reply.
            fixture=negotiation_screen_fixture();fixture["request_id"]="send-reviewed-"+std::to_string(height);
            _putenv_s("NFL2K5_FRANCHISE_SCREEN_EDIT","1");
            _putenv_s("NFL2K5_FRANCHISE_SCREEN_SUBMIT","1");
            _putenv_s("NFL2K5_FRANCHISE_NEGOTIATION","1");
            editing=submitting=true;capture("send-reviewed");
            const auto sends=submit_calls;press(3);capture("agent-waiting");
            require(submit_calls==sends+1,"Reviewed Y submission was not queued once");
            press(3);require(submit_calls==sends+1,"Pending agent submission repeated");
            checking=agent_waiting=submitting=false;notice="Request failed. No contract applied. Check the draft before retrying.";++preview_epoch;
            capture("agent-error-retained-draft");
            press(6);press(6);press(6);capture("error-contract-retained");
            const auto checks=preview_calls;press(2);capture("error-readonly-recheck");
            require(preview_calls==checks+1 && submit_calls==sends+1,"Error retry bypassed fresh draft check");
            notice.clear();checking=false;submitting=true;++preview_epoch;
            fixture["request_id"]="rechecked-send-"+std::to_string(height);capture("rechecked-send");
            press(3);require(submit_calls==sends+2,"Rechecked offer could not be sent");
            checking=agent_waiting=submitting=false;++preview_epoch;
            const auto agent_checkpoint=fixture.at("result");
            fixture["result"]={{"signing_checkpoint",agent_checkpoint},{"offer",agent_checkpoint.at("offer_context").at("offer")},
                {"counter",nullptr},{"reason","We need more guaranteed money before discussing an extension."}};
            capture("agent-reply-after-send");
            _putenv_s("NFL2K5_FRANCHISE_SCREEN_SUBMIT","0");_putenv_s("NFL2K5_FRANCHISE_NEGOTIATION","0");
            editing=false;
            // A failed paint cannot keep invisible input ownership.
            NFL2K5AddonDraw bad{1280,static_cast<uint32_t>(height),1,0,nullptr,1,0};
            require(!franchise_negotiation_screen_event(NFL2K5_ADDON_UI_DRAW,&bad,sizeof(bad)),"Malformed surface accepted");
        }
        std::puts("Real addon rendering, cached pixels, full response scrolling, Back and missing data passed; no game or inference");
        return 0;
    } catch(const std::exception& error){std::fprintf(stderr,"%s\n",error.what());return 2;}
}
