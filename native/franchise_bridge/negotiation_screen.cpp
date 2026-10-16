/* Read-only native replacement view. UI rendering/navigation live in the addon;
 * the game's two optional UI hooks know no franchise rules. */
#include "negotiation_screen.h"
#include "contract_draft.h"
#include "../../src/nfl2k5_franchise_host.h"
#include <windows.h>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <vector>
namespace {
std::mutex screen_lock;
franchise::NegotiationNavigation navigation;
franchise::ContractDraft draft;
unsigned long long preview_epoch;
bool preview_enabled=false,preview_pending=false;
bool current_contract=false,previous_y=false;
std::string body,title,status,closed_body,paint_key,presented_body;
std::array<std::string,4> pages;
nlohmann::json screen_reply={{"result",nlohmann::json::object()}};
std::vector<unsigned char> pixels;
int width,height;
bool paint_failed=false;
ULONGLONG opened_tick;
bool enabled(int& port) {
    const char *mode=std::getenv("NFL2K5_FRANCHISE_SCREEN_PREVIEW");
    const char *configured=std::getenv("NFL2K5_FRANCHISE_SCREEN_PORT");
    if(!mode || std::strcmp(mode,"1") || !configured || std::strlen(configured)!=1 || *configured<'0' || *configured>'3') return false;
    for(const char *key:{"NFL2K5_FRANCHISE_NEGOTIATION","NFL2K5_FRANCHISE_GUEST_SIGNING"}) {
        const char *value=std::getenv(key);
        if(value && std::strcmp(value,"0") && *value) return false;
    }
    port=*configured-'0';return true;
}
bool refresh() {
    static thread_local FranchiseNegotiationView view;
    if(!nfl2k5_franchise_negotiation_view(&view)) {
        body.clear();closed_body.clear();presented_body.clear();opened_tick=0;navigation.reset();draft.reset();current_contract=previous_y=false;return false;
    }
    if(!std::memchr(view.response,0,sizeof(view.response)) || !std::memchr(view.summary.title,0,sizeof(view.summary.title)) ||
       !std::memchr(view.summary.offer,0,sizeof(view.summary.offer))) return false;
    const std::string next=view.response[0]?view.response:"loading";
    if(next==closed_body) return false;
    if(next!=body || title!=view.summary.title) {
        bool completed_check=false;
        if(!opened_tick) opened_tick=GetTickCount64();
        if(!view.response[0]) {
            pages.fill("Loading verified franchise context...\n\nContract terms and performance will appear when the saved context is ready.");
            screen_reply={{"result",nlohmann::json::object()}};
        } else {
            auto parsed=franchise::parse_frame(next);
            const auto& result=parsed.at("result");
            const auto& prior=screen_reply.at("result");
            completed_check=draft.waiting && result.contains("player_id") && prior.contains("player_id") &&
                result.at("player_id")==prior.at("player_id") && title==view.summary.title;
            pages=franchise::negotiation_pages(parsed);screen_reply=std::move(parsed);
        }
        body=next;title=view.summary.title;
        if(!completed_check){navigation.reset();current_contract=previous_y=false;}
        draft.reset();presented_body.clear();paint_key.clear();paint_failed=false;
    }
    // An identical checked response still completes the mailbox round trip.
    if(draft.waiting && !view.preview_pending && view.preview_epoch!=preview_epoch) draft.reset();
    preview_epoch=view.preview_epoch;preview_enabled=view.preview_enabled!=0;preview_pending=view.preview_pending!=0;
    status=view.summary.offer;return true;
}
std::wstring wide(const std::string& text) {
    const int count=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,text.data(),static_cast<int>(text.size()),nullptr,0);
    if(!count && !text.empty()) throw std::runtime_error("Invalid screen UTF-8");
    std::wstring result(count,0);
    if(count) MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,text.data(),static_cast<int>(text.size()),result.data(),count);
    return result;
}
bool paint(NFL2K5AddonDraw& draw) {
    if(draw.width<320 || draw.height<240 || draw.width>2048 || draw.height>2048 || draw.stride!=draw.width*4 ||
       draw.capacity!=static_cast<size_t>(draw.stride)*draw.height || !draw.pixels) return false;
    const auto key=body+"\n"+title+"\n"+status+"\n"+std::to_string(navigation.page)+":"+std::to_string(navigation.scroll[navigation.page])+":"+
        std::to_string(draft.active)+":"+std::to_string(draft.amount)+":"+std::to_string(draft.flags)+":"+std::to_string(draft.field)+":"+std::to_string(draft.waiting)+draft.message+":"+std::to_string(preview_enabled)+":"+std::to_string(current_contract);
    if(key!=paint_key || width!=static_cast<int>(draw.width) || height!=static_cast<int>(draw.height)) {
        HDC dc=CreateCompatibleDC(nullptr);if(!dc) return false;
        BITMAPINFO info{};info.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);
        info.bmiHeader.biWidth=draw.width;info.bmiHeader.biHeight=-static_cast<int>(draw.height);
        info.bmiHeader.biPlanes=1;info.bmiHeader.biBitCount=32;info.bmiHeader.biCompression=BI_RGB;
        void *bits=nullptr;HBITMAP bitmap=CreateDIBSection(dc,&info,DIB_RGB_COLORS,&bits,nullptr,0);
        if(!bitmap){DeleteDC(dc);return false;}
        const auto old_bitmap=SelectObject(dc,bitmap);
        const float u=std::min(draw.width/1100.0f,draw.height/700.0f);
        auto px=[&](float value){return static_cast<int>(std::lround(value*u));};
        const COLORREF white=RGB(247,249,253),secondary=RGB(184,205,229),accent=RGB(178,35,57);
        auto fill=[&](int left,int top,int right,int bottom,COLORREF color) {
            RECT rect{left,top,right,bottom};HBRUSH brush=CreateSolidBrush(color);
            FillRect(dc,&rect,brush);DeleteObject(brush);
        };
        fill(0,0,draw.width,draw.height,RGB(9,16,27));
        fill(0,0,draw.width,px(7),accent);
        fill(0,px(7),draw.width,px(122),RGB(17,29,46));
        fill(0,px(122),px(222),draw.height-px(54),RGB(13,23,38));
        fill(px(222),px(122),px(223),draw.height-px(54),RGB(42,61,84));
        SetBkMode(dc,TRANSPARENT);
        auto text=[&](const std::string& value,int left,int top,int max_right,int bottom,int size,int weight,COLORREF color,UINT flags) {
            HFONT font=CreateFontW(-px(static_cast<float>(size)),0,0,0,weight,FALSE,FALSE,FALSE,DEFAULT_CHARSET,
                OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,CLEARTYPE_QUALITY,DEFAULT_PITCH,L"Bahnschrift");
            const auto old=SelectObject(dc,font);SetTextColor(dc,color);
            RECT rect{left,top,max_right,bottom};const auto content=wide(value);
            DrawTextW(dc,content.c_str(),static_cast<int>(content.size()),&rect,flags|DT_NOPREFIX);
            SelectObject(dc,old);DeleteObject(font);return rect;
        };
        text(title,px(30),px(15),draw.width-px(30),px(61),36,FW_BOLD,white,DT_SINGLELINE|DT_END_ELLIPSIS);
        const auto& result=screen_reply.at("result");
        const auto& checkpoint=result.contains("signing_checkpoint")?result.at("signing_checkpoint"):result;
        const auto profile=checkpoint.value("performance_context",nlohmann::json::object());
        const auto traits=franchise::screen_personalities(checkpoint);
        auto trait_icon=[&](const std::string& key,int x,int y) {
            HPEN pen=CreatePen(PS_SOLID,std::max(1,px(2)),secondary);
            const auto old_pen=SelectObject(dc,pen);const auto old_brush=SelectObject(dc,GetStockObject(NULL_BRUSH));
            auto line=[&](std::initializer_list<POINT> points) {
                std::vector<POINT> scaled;for(const auto& point:points) scaled.push_back({x+px(point.x),y+px(point.y)});
                Polyline(dc,scaled.data(),static_cast<int>(scaled.size()));
            };
            if(key=="security") line({{1,1},{17,1},{17,10},{14,15},{9,19},{4,15},{1,10},{1,1}});
            else if(key=="playing time") {
                Ellipse(dc,x+px(1),y+px(3),x+px(18),y+px(20));line({{9,6},{9,12},{13,12}});
                line({{6,0},{12,0}});line({{9,0},{9,3}});
            }
            else if(key=="loyalty") {
                Ellipse(dc,x,y+px(3),x+px(12),y+px(16));Ellipse(dc,x+px(7),y+px(3),x+px(19),y+px(16));
            } else if(key=="pay") {
                Ellipse(dc,x,y,x+px(19),y+px(19));line({{9,4},{9,15}});line({{5,6},{13,6}});line({{5,12},{13,12}});
            } else {line({{4,1},{15,1},{15,8},{12,12},{7,12},{4,8},{4,1}});
                line({{4,3},{0,3},{0,7},{4,9}});line({{15,3},{19,3},{19,7},{15,9}});
                line({{9,12},{9,18}});line({{4,18},{15,18}});}
            SelectObject(dc,old_brush);SelectObject(dc,old_pen);DeleteObject(pen);
        };
        const auto physical=franchise::screen_profile(profile);
        const auto physical_size=text(physical,0,0,draw.width,0,19,FW_NORMAL,secondary,DT_CALCRECT|DT_SINGLELINE);
        const int icons_left=px(32)+physical_size.right+px(28),row_y=px(80);
        text(physical,px(32),row_y,draw.width-px(32),row_y+px(28),19,FW_NORMAL,secondary,DT_SINGLELINE);
        for(size_t trait=0;trait<traits.size();++trait)
            trait_icon(traits[trait].key,icons_left+px(34.0f*trait),row_y+px(2));
        const char *tabs[]={"Contract","Performance","Personality","Agent"};
        for(unsigned i=0;i<4;++i) {
            const int top=px(147+48.0f*i);
            if(i==navigation.page) fill(px(17),top,px(205),top+px(42),accent);
            text(tabs[i],px(33),top+px(9),px(197),top+px(35),22,
                i==navigation.page?FW_BOLD:FW_NORMAL,i==navigation.page?white:secondary,DT_SINGLELINE);
        }
        text("INJURY TENDENCY",px(31),px(362),px(204),px(387),15,FW_BOLD,secondary,DT_SINGLELINE);
        text("Insufficient recorded history",px(31),px(394),px(202),px(467),18,FW_NORMAL,white,DT_WORDBREAK);
        text("READ-ONLY",px(31),draw.height-px(164),px(201),draw.height-px(139),17,FW_BOLD,secondary,DT_SINGLELINE);
        text("Offer submission is off.\nNo contract is signed.",px(31),draw.height-px(129),px(201),draw.height-px(67),17,FW_NORMAL,secondary,DT_WORDBREAK);
        const int left=px(255),right=draw.width-px(32),bottom=draw.height-px(76);
        const auto context=checkpoint.value("offer_context",nlohmann::json::object());
        const char *headings[]={"Your offer","Player stats","Personality","Agent response"};
        if(navigation.page==0) {
            const char *choices[]={"Your offer","Current contract"};
            for(unsigned i=0;i<2;++i) {
                const int x=left+px(i*225.0f);
                fill(x,px(145),x+px(212),px(185),current_contract==(i==1)?RGB(45,65,91):RGB(17,29,46));
                text(choices[i],x+px(12),px(153),x+px(202),px(180),22,current_contract==(i==1)?FW_BOLD:FW_NORMAL,white,DT_SINGLELINE);
            }
            text("Y  Switch",left+px(470),px(155),right,px(182),18,FW_NORMAL,secondary,DT_SINGLELINE|DT_RIGHT);
        } else text(headings[navigation.page],left,px(149),right,px(185),27,FW_BOLD,white,DT_SINGLELINE);
        const bool drafting=navigation.page==0 && !current_contract && (draft.active || draft.dirty());
        int overflow=0,offset=0;
        if(navigation.page<2 && body!="loading") {
            std::vector<franchise::ScreenTable> tables;
            std::string summary,note;
            if(navigation.page==0 && current_contract) {
                auto current=franchise::current_contract_table(checkpoint);
                note=current.rows.empty()?"Current contract information is unavailable.":
                    "Saved cap schedule. Original signing bonus cash and guarantees may be unavailable. Your offer stays separate.";
                if(!current.rows.empty()) tables.push_back(std::move(current));
            } else if(drafting) {
                tables.push_back(draft.table());
                note=draft.waiting?"Checking exact annual amounts and eligibility...":
                    draft.active?"Change terms, then check the exact annual breakdown. No offer is sent to the player.":
                    "Draft retained. Check its exact annual breakdown before negotiating. No offer is sent to the player.";
                if(!draft.message.empty()) note+="\n"+draft.message;
            } else if(navigation.page==0) {
                auto annual=franchise::contract_table(context);
                if(!annual.rows.empty()) {
                    const auto& offer=context.at("offer");
                    int64_t total=offer.at("signing_bonus").get<int64_t>();
                    for(const auto& value:offer.at("salaries")) total+=value.get<int64_t>();
                    summary=std::to_string(annual.rows.size())+" years  /  "+franchise::screen_money(total)+" total";
                    tables.push_back(context.contains("amendment")?
                        franchise::amendment_table(context,checkpoint.value("performance_context",nlohmann::json::object())):std::move(annual));
                }
                note=context.contains("preview") && !context.at("preview").is_null()?
                    "Proposed terms only. Opening liabilities remain unverified.":
                    "Starts from the game's offer, not a recommendation. New bonus excludes existing bonus obligations. A dash means cap impact is not validated.";
                if(context.contains("amendment"))
                    note="Conditional on player agreement: remaining base changes; every old bonus charge stays in its original year. Full-year comparison only; earned pay, cash and save application are not validated. Submission is off.";
                if(context.contains("reason") && context.at("reason").is_string()) note+="\n"+context.at("reason").get<std::string>();
            } else {
                if(checkpoint.contains("performance_context")) tables=franchise::performance_tables(checkpoint.at("performance_context"));
                note=u8"Saved history. \u2014 means not recorded. Separate entries are not combined.";
            }
            const int top=px(202),row_height=px(34),gap=px(22),header=px(30),section=px(30);
            const bool amendment=context.contains("amendment");
            const bool preview=!drafting && !current_contract && navigation.page==0 &&
                (amendment || (context.contains("preview") && !context.at("preview").is_null()));
            const auto measured_note=text(note,left,0,right-px(12),0,17,FW_NORMAL,secondary,DT_CALCRECT|DT_WORDBREAK);
            int content=summary.empty()?0:px(67);
            for(const auto& table:tables) content+=section+header+static_cast<int>(table.rows.size())*row_height+gap;
            if(preview) content+=px(62);
            content+=static_cast<int>(measured_note.bottom)+px(14);
            if(tables.empty()) content+=px(64);
            overflow=std::max(0,content-(bottom-top));
            navigation.scroll[navigation.page]=std::min(navigation.scroll[navigation.page],static_cast<int>(std::ceil(overflow/u)));
            offset=std::min(px(static_cast<float>(navigation.scroll[navigation.page])),overflow);
            SaveDC(dc);IntersectClipRect(dc,left,top,right,bottom);
            int y=top-offset;
            if(!summary.empty()) {
                text(summary,left,y,right,y+px(30),25,FW_BOLD,white,DT_SINGLELINE);
                text("Signing bonus  "+franchise::screen_money(context.at("offer").at("signing_bonus")),left,y+px(35),right,y+px(60),19,FW_NORMAL,secondary,DT_SINGLELINE);
                y+=px(67);
            }
            if(tables.empty()) {
                text(navigation.page==0?"Contract details unavailable":"No saved stats available",left,y,right,y+px(35),24,FW_BOLD,white,DT_SINGLELINE);
                y+=px(64);
            }
            for(const auto& table:tables) {
                text(table.title,left,y,right,y+px(26),22,FW_BOLD,white,DT_SINGLELINE);y+=section;
                const int span=right-left-px(12),first=span*(drafting?52:navigation.page==0?15:24)/100;
                const int cells=static_cast<int>(table.columns.size())-1;
                std::vector<int> columns{left,left+first};
                for(int col=1;col<=cells;++col) columns.push_back(left+first+(span-first)*col/cells);
                fill(left,y,right-px(12),y+header,RGB(30,47,69));
                for(size_t col=0;col<table.columns.size();++col)
                    text(table.columns[col],columns[col]+px(10),y+px(7),columns[col+1]-px(10),y+header-px(3),15,FW_BOLD,secondary,DT_SINGLELINE|(col?DT_RIGHT:DT_LEFT));
                y+=header;
                for(size_t row=0;row<table.rows.size();++row) {
                    fill(left,y,right-px(12),y+row_height,drafting && draft.active && row==draft.field?RGB(57,47,70):row%2?RGB(19,33,51):RGB(16,28,44));
                    fill(left,y+row_height-1,right-px(12),y+row_height,RGB(37,55,77));
                    const auto& values=table.rows[row];
                    text(values.label,columns[0]+px(10),y+px(7),columns[1]-px(10),y+row_height-px(3),19,FW_NORMAL,secondary,DT_SINGLELINE);
                    for(size_t col=0;col<values.values.size();++col)
                        text(values.values[col],columns[col+1]+px(10),y+px(7),columns[col+2]-px(10),y+row_height-px(3),navigation.page==0?18:22,FW_NORMAL,white,DT_SINGLELINE|DT_RIGHT);
                    y+=row_height;
                }
                y+=gap;
            }
            if(preview) {
                fill(left,y,right-px(12),y+px(48),RGB(24,44,65));
                text(amendment?"Modeled room if agreed":"Cap room after offer",left+px(12),y+px(13),right-px(245),y+px(40),20,FW_NORMAL,secondary,DT_SINGLELINE);
                text(franchise::screen_money(context.at(amendment?"amendment":"preview").at("room_after")),right-px(245),y+px(10),right-px(26),y+px(42),25,FW_BOLD,white,DT_SINGLELINE|DT_RIGHT);
                y+=px(62);
            }
            text(note,left,y,right-px(12),y+measured_note.bottom+px(8),17,FW_NORMAL,secondary,DT_WORDBREAK);
            RestoreDC(dc,-1);
            if(overflow) {
                const int track=right-px(3),height=bottom-top;
                fill(track,top,right,bottom,RGB(48,66,89));
                const int thumb=std::max(px(24),height*height/content);
                const int position=top+static_cast<int>((height-thumb)*static_cast<double>(offset)/overflow);
                fill(track,position,right,position+thumb,secondary);
            }
        } else if(navigation.page==3 && body!="loading") {
            const int top=px(205),message_left=left+px(20),message_right=right-px(20);
            const int bubble_width=(message_right-message_left)*86/100;
            const auto messages=franchise::screen_conversation(screen_reply,pages[3]);
            std::vector<int> heights;
            int content=0;
            for(const auto& message:messages) {
                const auto measured=text(message.body,0,0,bubble_width-px(32),0,21,FW_NORMAL,white,DT_CALCRECT|DT_WORDBREAK);
                const int height=px(52)+measured.bottom;
                heights.push_back(height);content+=height+px(18);
            }
            if(!messages.empty()) content-=px(18);
            const int viewport=bottom-top;
            overflow=std::max(0,content-viewport);
            navigation.scroll[3]=std::min(navigation.scroll[3],static_cast<int>(std::ceil(overflow/u)));
            offset=std::min(px(static_cast<float>(navigation.scroll[3])),overflow);
            int y=top+std::max(0,viewport-content)-offset;
            SaveDC(dc);IntersectClipRect(dc,left,top,right,bottom);
            if(messages.empty()) text("No conversation yet.\nOffer submission is currently off.",message_left,bottom-px(78),message_right,bottom,21,FW_NORMAL,secondary,DT_WORDBREAK);
            for(size_t i=0;i<messages.size();++i) {
                const auto& message=messages[i];
                const int x=message.outgoing?message_right-bubble_width:message_left;
                fill(x,y,x+bubble_width,y+heights[i],message.outgoing?RGB(35,57,81):RGB(18,32,50));
                text(message.sender,x+px(16),y+px(12),x+bubble_width-px(16),y+px(36),17,FW_BOLD,secondary,DT_SINGLELINE);
                text(message.body,x+px(16),y+px(39),x+bubble_width-px(16),y+heights[i]-px(10),21,FW_NORMAL,white,DT_WORDBREAK);
                y+=heights[i]+px(18);
            }
            RestoreDC(dc,-1);
            if(overflow) {
                fill(right-px(3),top,right,bottom,RGB(48,66,89));
                const int thumb=std::max(px(24),viewport*viewport/std::max(1,content));
                const int position=top+static_cast<int>((viewport-thumb)*static_cast<double>(offset)/overflow);
                fill(right-px(3),position,right,position+thumb,secondary);
            }
        } else {
            const int panel_top=px(205),body_top=panel_top+px(24),body_bottom=bottom-px(18);
            fill(left,panel_top,right,bottom,RGB(18,32,50));
            const int body_left=left+px(24),body_right=right-px(26);
            const auto measured=text(pages[navigation.page],body_left,0,body_right,0,22,FW_NORMAL,white,DT_CALCRECT|DT_WORDBREAK);
            const int line_height=std::max(1,static_cast<int>(text("M",body_left,0,body_right,0,22,FW_NORMAL,white,DT_CALCRECT|DT_SINGLELINE).bottom));
            const auto relationships=navigation.page==2 && body!="loading"?franchise::screen_relationships(checkpoint):std::vector<franchise::ScreenRelationship>{};
            const int traits_height=navigation.page==2?px(74.0f*traits.size()):0;
            const int bars_height=relationships.empty()?0:px(197);
            const int prose_height=navigation.page==2 && !traits.empty()?0:static_cast<int>(measured.bottom);
            const int content_height=traits_height+bars_height+prose_height;
            const int raw_overflow=std::max(0,content_height-body_bottom+body_top);
            overflow=((raw_overflow+line_height-1)/line_height)*line_height;
            navigation.scroll[navigation.page]=std::min(navigation.scroll[navigation.page],static_cast<int>(std::ceil(overflow/u)));
            offset=std::min((px(static_cast<float>(navigation.scroll[navigation.page]))/line_height)*line_height,overflow);
            SaveDC(dc);IntersectClipRect(dc,body_left,body_top,body_right,body_bottom);
            if(navigation.page==2) for(size_t i=0;i<traits.size();++i) {
                const int y=body_top-offset+px(74.0f*i);
                trait_icon(traits[i].key,body_left,y+px(3));
                text(traits[i].label,body_left+px(32),y,body_right,y+px(28),22,FW_BOLD,white,DT_SINGLELINE);
                text(franchise::screen_trait_description(traits[i].key),body_left+px(32),y+px(29),body_right,y+px(70),18,FW_NORMAL,secondary,DT_WORDBREAK);
            }
            if(!relationships.empty()) {
                int y=body_top+traits_height-offset;
                text("Relationship with your team",body_left,y,body_right,y+px(30),22,FW_BOLD,white,DT_SINGLELINE);
                y+=px(42);
                for(const auto& relationship:relationships) {
                    text(relationship.label,body_left,y,body_left+px(180),y+px(25),19,FW_NORMAL,secondary,DT_SINGLELINE);
                    const int track_left=body_left+px(185),track_right=body_right-px(90),top=y+px(6),height=px(12);
                    fill(track_left,top,track_right,top+height,RGB(42,61,84));
                    if(relationship.known) {
                        const int end=track_left+static_cast<int>(std::lround((track_right-track_left)*relationship.value));
                        if(end>track_left) fill(track_left,top,end,top+height,RGB(133,178,218));
                        fill(track_left+(track_right-track_left)/2,top,track_left+(track_right-track_left)/2+1,top+height,RGB(184,205,229));
                    } else text("Unknown",track_right+px(12),y,body_right,y+px(25),16,FW_NORMAL,secondary,DT_SINGLELINE);
                    y+=px(43);
                }
            }
            const int prose_top=body_top+traits_height+bars_height-offset;
            if(prose_height) text(pages[navigation.page],body_left,prose_top,body_right,prose_top+measured.bottom+px(28),22,FW_NORMAL,white,DT_WORDBREAK);
            RestoreDC(dc,-1);
            if(overflow) {
                const int track_top=body_top,track_bottom=body_bottom,track_x=right-px(9);
                fill(track_x,track_top,track_x+px(3),track_bottom,RGB(48,66,89));
                const int thumb=std::max(px(24),(track_bottom-track_top)*(track_bottom-track_top)/std::max(1,content_height));
                const int y=track_top+static_cast<int>((track_bottom-track_top-thumb)*static_cast<double>(offset)/overflow);
                fill(track_x,y,track_x+px(3),y+thumb,secondary);
            }
        }
        fill(0,draw.height-px(53),draw.width,draw.height,RGB(15,27,43));
        fill(0,draw.height-px(54),draw.width,draw.height-px(53),RGB(42,61,84));
        const bool editing=draft.active && navigation.page==0 && !current_contract;
        text(editing?"Up/down  Field    Left/right  Adjust":"D-pad / LS  Section",px(31),draw.height-px(34),px(465),draw.height-px(9),18,FW_NORMAL,secondary,DT_SINGLELINE);
        text(editing?"X  Check    RT  Larger steps":preview_enabled && navigation.page==0 && !current_contract?
            draft.dirty()?"A  Edit    X  Check draft":"A  Edit offer    RS  Scroll":"RS  Scroll    LT / RT  Section",px(485),draw.height-px(34),draw.width-px(180),draw.height-px(9),18,FW_NORMAL,secondary,DT_SINGLELINE);
        text(editing?"B  Review":navigation.page==0 && current_contract?"B  Your offer":"B  Back",draw.width-px(175),draw.height-px(34),draw.width-px(20),draw.height-px(9),18,FW_BOLD,white,DT_SINGLELINE|DT_RIGHT);
        auto *bytes=static_cast<unsigned char*>(bits);
        // GDI text does not maintain alpha; this full-screen surface is opaque.
        for(size_t i=3;i<draw.capacity;i+=4) bytes[i]=255;
        pixels.assign(bytes,bytes+draw.capacity);
        SelectObject(dc,old_bitmap);DeleteObject(bitmap);DeleteDC(dc);
        width=draw.width;height=draw.height;paint_key=key;draw.changed=1;
    }
    if(draw.changed || draw.redraw){std::memcpy(draw.pixels,pixels.data(),pixels.size());draw.changed=1;}
    if(presented_body!=body) std::fprintf(stderr,"[FRANCHISE-UI] first_paint state=%s elapsed_ms=%llu\n",
        body=="loading"?"loading":"context",static_cast<unsigned long long>(GetTickCount64()-opened_tick));
    presented_body=body;return true;
}
}
extern "C" int franchise_negotiation_screen_event(const char *name,const void *data,size_t size) {
    if(!name || !data) return 0;
    const bool drawing=!std::strcmp(name,NFL2K5_ADDON_UI_DRAW) && size==sizeof(NFL2K5AddonDraw);
    const bool input=!std::strcmp(name,NFL2K5_ADDON_UI_INPUT) && size==sizeof(NFL2K5AddonInput);
    if(!drawing && !input) return 0;
    std::lock_guard<std::mutex> lock(screen_lock);
    try {
        int port=0;if(!enabled(port) || !refresh()) {presented_body.clear();return 0;}
        if(drawing) {
            if(paint(*const_cast<NFL2K5AddonDraw*>(static_cast<const NFL2K5AddonDraw*>(data)))) {paint_failed=false;return 1;}
            paint_failed=true;presented_body.clear();return 0;
        }
        // Swallow the transition into a fresh view; a prior page's held button
        // must not reach the covered native menu. A failed paint releases UI
        // ownership, with the host quarantining already-held buttons.
        if(presented_body!=body) return paint_failed?0:NFL2K5_ADDON_UI_CONSUMED;
        const auto& event=*static_cast<const NFL2K5AddonInput*>(data);
        if(event.port>=4) return 0;
        if(event.port!=static_cast<unsigned>(port)) return NFL2K5_ADDON_UI_CONSUMED;
        const bool editing=draft.active && navigation.page==0 && !current_contract;
        const bool y=event.analog[3]>30,toggle=y && !previous_y;
        previous_y=y;
        if(navigation.page==0 && toggle && (editing?draft.armed:navigation.armed)) {
            current_contract=!current_contract;navigation.reset();draft.rearm();return NFL2K5_ADDON_UI_CONSUMED;
        }
        auto check=[&](){
            if(nfl2k5_franchise_preview_offer(draft.epoch,draft.amount,draft.flags)) draft.waiting=true;
            else draft.message="Context changed or terms unavailable. Review your offer and retry.";
        };
        if(editing) {
            const int action=draft.input(event,GetTickCount64());
            if(action==1){draft.review();navigation.reset();}
            if(action==2) check();
            return NFL2K5_ADDON_UI_CONSUMED;
        }
        if(preview_enabled && !preview_pending && navigation.page==0 && !current_contract && navigation.armed && body!="loading") {
            if(event.analog[0]>30 && navigation.previous_analog[0]<=30) {
                const auto& result=screen_reply.at("result");
                const auto& checkpoint=result.contains("signing_checkpoint")?result.at("signing_checkpoint"):result;
                if(draft.present) {draft.resume();navigation.reset();return NFL2K5_ADDON_UI_CONSUMED;}
                if(checkpoint.contains("offer_context") && draft.begin(checkpoint.at("offer_context"),preview_epoch)) {
                    navigation.reset();return NFL2K5_ADDON_UI_CONSUMED;
                }
            }
            if(draft.dirty() && event.analog[2]>30 && navigation.previous_analog[2]<=30) check();
        }
        const int result=navigation.input(event);
        if(result==NFL2K5_ADDON_UI_BACK) {
            if(navigation.page==0 && current_contract){current_contract=false;navigation.reset();draft.rearm();return NFL2K5_ADDON_UI_CONSUMED;}
            closed_body=body;presented_body.clear();
        }
        return result;
    } catch(...) {paint_failed=true;presented_body.clear();paint_key.clear();return 0;}
}
