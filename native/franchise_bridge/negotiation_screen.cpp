/* Read-only native replacement view. UI rendering/navigation live in the addon;
 * the game's two optional UI hooks know no franchise rules. */
#include "negotiation_screen.h"
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
std::string body,title,status,closed_body,paint_key,presented_body;
std::array<std::string,3> pages;
nlohmann::json screen_reply;
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
        body.clear();closed_body.clear();presented_body.clear();opened_tick=0;navigation.reset();return false;
    }
    if(!std::memchr(view.response,0,sizeof(view.response)) || !std::memchr(view.summary.title,0,sizeof(view.summary.title)) ||
       !std::memchr(view.summary.offer,0,sizeof(view.summary.offer))) return false;
    const std::string next=view.response[0]?view.response:"loading";
    if(next==closed_body) return false;
    if(next!=body || title!=view.summary.title) {
        if(!opened_tick) opened_tick=GetTickCount64();
        if(!view.response[0]) {
            pages.fill("Loading verified franchise context...\n\nContract terms and performance will appear when the saved context is ready.");
            screen_reply={{"result",nlohmann::json::object()}};
        } else {
            auto parsed=franchise::parse_frame(next);
            pages=franchise::negotiation_pages(parsed);screen_reply=std::move(parsed);
        }
        body=next;title=view.summary.title;navigation.reset();presented_body.clear();paint_key.clear();paint_failed=false;
    }
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
    const auto key=body+"\n"+title+"\n"+status+"\n"+std::to_string(navigation.page)+":"+std::to_string(navigation.scroll[navigation.page]);
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
        text(title,px(30),px(25),draw.width-px(30),px(75),36,FW_BOLD,white,DT_SINGLELINE|DT_END_ELLIPSIS);
        text("Contract negotiation",px(32),px(80),draw.width-px(32),px(108),19,FW_NORMAL,secondary,DT_SINGLELINE);
        const char *tabs[]={"Contract","Performance","Agent"};
        for(unsigned i=0;i<3;++i) {
            const int top=px(153+62.0f*i);
            if(i==navigation.page) fill(px(17),top,px(205),top+px(48),accent);
            text(tabs[i],px(33),top+px(12),px(197),top+px(40),23,
                i==navigation.page?FW_BOLD:FW_NORMAL,i==navigation.page?white:secondary,DT_SINGLELINE);
        }
        text("READ-ONLY",px(31),draw.height-px(164),px(201),draw.height-px(139),17,FW_BOLD,secondary,DT_SINGLELINE);
        text("Offer submission is off.\nNo contract is signed.",px(31),draw.height-px(129),px(201),draw.height-px(67),17,FW_NORMAL,secondary,DT_WORDBREAK);
        const int left=px(255),right=draw.width-px(32),bottom=draw.height-px(76);
        const auto& result=screen_reply.at("result");
        const auto& checkpoint=result.contains("signing_checkpoint")?result.at("signing_checkpoint"):result;
        const auto context=checkpoint.value("offer_context",nlohmann::json::object());
        const bool table=navigation.page==0 && context.contains("offer") && !context.at("offer").is_null()
            && context.at("offer").at("salaries").size()<=5
            && context.contains("preview") && !context.at("preview").is_null();
        const char *headings[]={"Your offer","Performance evidence","Agent response"};
        text(headings[navigation.page],left,px(149),right,px(185),27,FW_BOLD,white,DT_SINGLELINE);
        int overflow=0,offset=0;
        if(table) {
            const auto& offer=context.at("offer");const auto& salaries=offer.at("salaries");
            int64_t total=offer.at("signing_bonus").get<int64_t>();
            for(const auto& salary:salaries) total+=salary.get<int64_t>(); // already bounded by negotiation_pages
            text(std::to_string(salaries.size())+" years  /  "+franchise::screen_money(total)+" total",left,px(195),right,px(227),25,FW_BOLD,white,DT_SINGLELINE);
            text("Signing bonus  "+franchise::screen_money(offer.at("signing_bonus")),left,px(237),right,px(264),19,FW_NORMAL,secondary,DT_SINGLELINE);
            const int top=px(286),row=px(35);
            const int span=right-left;
            const int columns[]={left,left+span*13/100,left+span*43/100,left+span*71/100,right};
            const char *labels[]={"YEAR","BASE SALARY","PROTECTED BASE","CAP CHARGE"};
            fill(left,top,right,top+px(33),RGB(30,47,69));
            for(int i=0;i<4;++i) text(labels[i],columns[i]+px(11),top+px(8),columns[i+1]-px(10),top+px(29),15,FW_BOLD,secondary,DT_SINGLELINE|(i?DT_RIGHT:DT_LEFT));
            const auto preview=context.value("preview",nlohmann::json());
            for(size_t i=0;i<salaries.size();++i) {
                const int y=top+px(33)+static_cast<int>(i)*row;
                fill(left,y,right,y+row,i%2?RGB(19,33,51):RGB(16,28,44));
                fill(left,y+row-1,right,y+row,RGB(37,55,77));
                const std::string values[]={std::to_string(i+1),franchise::screen_money(salaries[i]),
                    offer.contains("guaranteed_salaries")?franchise::screen_money(offer.at("guaranteed_salaries").at(i)):"Not specified",
                    !preview.is_null()?franchise::screen_money(preview.at("contract_charges").at(i)):"Unavailable"};
                for(int col=0;col<4;++col) text(values[col],columns[col]+px(11),y+px(8),columns[col+1]-px(10),y+row-px(3),20,col==3?FW_BOLD:FW_NORMAL,white,DT_SINGLELINE|(col?DT_RIGHT:DT_LEFT));
            }
            const int cap_top=std::max(top+px(33)+static_cast<int>(salaries.size())*row+px(26),bottom-px(98));
            fill(left,cap_top,right,cap_top+px(56),RGB(24,44,65));
            text("Cap room after offer",left+px(16),cap_top+px(16),right-px(245),cap_top+px(44),20,FW_NORMAL,secondary,DT_SINGLELINE);
            text(!preview.is_null()?franchise::screen_money(preview.at("room_after")):"Unavailable",right-px(245),cap_top+px(13),right-px(16),cap_top+px(46),25,FW_BOLD,white,DT_SINGLELINE|DT_RIGHT);
            text("Accounting preview. Opening liabilities are still being verified.",left,cap_top+px(68),right,bottom+px(15),17,FW_NORMAL,secondary,DT_WORDBREAK);
            if(context.contains("reason") && context.at("reason").is_string())
                text(context.at("reason").get<std::string>(),left,px(266),right,px(287),16,FW_NORMAL,secondary,DT_SINGLELINE|DT_END_ELLIPSIS);
        } else {
            const int panel_top=px(205),body_top=panel_top+px(24),body_bottom=bottom-px(18);
            fill(left,panel_top,right,bottom,RGB(18,32,50));
            const int body_left=left+px(24),body_right=right-px(26);
            const auto measured=text(pages[navigation.page],body_left,0,body_right,0,22,FW_NORMAL,white,DT_CALCRECT|DT_WORDBREAK);
            const int line_height=std::max(1,static_cast<int>(text("M",body_left,0,body_right,0,22,FW_NORMAL,white,DT_CALCRECT|DT_SINGLELINE).bottom));
            const int raw_overflow=std::max(0,static_cast<int>(measured.bottom)-body_bottom+body_top);
            overflow=((raw_overflow+line_height-1)/line_height)*line_height;
            navigation.scroll[navigation.page]=std::min(navigation.scroll[navigation.page],static_cast<int>(std::ceil(overflow/u)));
            offset=std::min((px(static_cast<float>(navigation.scroll[navigation.page]))/line_height)*line_height,overflow);
            SaveDC(dc);IntersectClipRect(dc,body_left,body_top,body_right,body_bottom);
            text(pages[navigation.page],body_left,body_top-offset,body_right,body_top-offset+measured.bottom+px(28),22,FW_NORMAL,white,DT_WORDBREAK);
            RestoreDC(dc,-1);
            if(overflow) {
                const int track_top=body_top,track_bottom=body_bottom,track_x=right-px(9);
                fill(track_x,track_top,track_x+px(3),track_bottom,RGB(48,66,89));
                const int thumb=std::max(px(24),(track_bottom-track_top)*(track_bottom-track_top)/std::max(1,static_cast<int>(measured.bottom)));
                const int y=track_top+static_cast<int>((track_bottom-track_top-thumb)*static_cast<double>(offset)/overflow);
                fill(track_x,y,track_x+px(3),y+thumb,secondary);
            }
        }
        fill(0,draw.height-px(53),draw.width,draw.height,RGB(15,27,43));
        fill(0,draw.height-px(54),draw.width,draw.height-px(53),RGB(42,61,84));
        text("D-pad / LS  Section",px(31),draw.height-px(34),px(302),draw.height-px(9),18,FW_NORMAL,secondary,DT_SINGLELINE);
        text("RS  Scroll    LT / RT  Section",px(323),draw.height-px(34),px(800),draw.height-px(9),18,FW_NORMAL,secondary,DT_SINGLELINE);
        text("B  Back",draw.width-px(138),draw.height-px(34),draw.width-px(31),draw.height-px(9),18,FW_BOLD,white,DT_SINGLELINE|DT_RIGHT);
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
        const int result=navigation.input(event);
        if(result==NFL2K5_ADDON_UI_BACK){closed_body=body;presented_body.clear();}
        return result;
    } catch(...) {paint_failed=true;presented_body.clear();paint_key.clear();return 0;}
}
