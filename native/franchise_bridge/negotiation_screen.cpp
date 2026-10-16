/* Read-only native replacement view. UI rendering/navigation live in the addon;
 * the game's two optional UI hooks know no franchise rules. */
#include "negotiation_screen.h"
#include "../../src/nfl2k5_franchise_host.h"
#include <windows.h>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <vector>
namespace {
std::mutex screen_lock;
franchise::NegotiationNavigation navigation;
std::string body,title,status,closed_body,paint_key,presented_body;
std::array<std::string,3> pages;
std::vector<unsigned char> pixels;
int width,height;
bool paint_failed=false;
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
        body.clear();closed_body.clear();presented_body.clear();navigation.reset();return false;
    }
    if(!std::memchr(view.response,0,sizeof(view.response)) || !std::memchr(view.summary.title,0,sizeof(view.summary.title)) ||
       !std::memchr(view.summary.offer,0,sizeof(view.summary.offer))) return false;
    const std::string next=view.response;
    if(next==closed_body) return false;
    if(next!=body || title!=view.summary.title) {
        pages=franchise::negotiation_pages(franchise::parse_frame(next));
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
        const int margin=px(32),right=draw.width-margin,body_top=px(164),body_bottom=draw.height-px(62);
        RECT background{0,0,static_cast<LONG>(draw.width),static_cast<LONG>(draw.height)};
        HBRUSH brush=CreateSolidBrush(RGB(9,14,23));FillRect(dc,&background,brush);DeleteObject(brush);
        SetBkMode(dc,TRANSPARENT);
        auto text=[&](const std::string& value,int left,int top,int max_right,int bottom,int size,int weight,COLORREF color,UINT flags) {
            HFONT font=CreateFontW(-px(static_cast<float>(size)),0,0,0,weight,FALSE,FALSE,FALSE,DEFAULT_CHARSET,
                OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,CLEARTYPE_QUALITY,DEFAULT_PITCH,L"Bahnschrift");
            const auto old=SelectObject(dc,font);SetTextColor(dc,color);
            RECT rect{left,top,max_right,bottom};const auto content=wide(value);
            DrawTextW(dc,content.c_str(),static_cast<int>(content.size()),&rect,flags|DT_NOPREFIX);
            SelectObject(dc,old);DeleteObject(font);return rect;
        };
        text(title,margin,px(22),right,px(65),32,FW_BOLD,RGB(255,255,255),DT_SINGLELINE);
        text(status,margin,px(70),right,px(116),18,FW_NORMAL,RGB(199,219,245),DT_WORDBREAK);
        const char *tabs[]={"Contract","Performance","Agent"};
        for(unsigned i=0;i<3;++i) {
            const int left=margin+px(195.0f*i);
            text(tabs[i],left,px(124),left+px(180),px(153),22,i==navigation.page?FW_BOLD:FW_NORMAL,
                i==navigation.page?RGB(255,255,255):RGB(199,219,245),DT_SINGLELINE);
            if(i==navigation.page){RECT line{left,px(155),left+px(175),px(157)};brush=CreateSolidBrush(RGB(199,219,245));FillRect(dc,&line,brush);DeleteObject(brush);}
        }
        const auto measured=text(pages[navigation.page],margin,0,right,0,22,FW_NORMAL,RGB(255,255,255),DT_CALCRECT|DT_WORDBREAK);
        const int overflow=std::max(0,static_cast<int>(measured.bottom)-body_bottom+body_top);
        navigation.scroll[navigation.page]=std::min(navigation.scroll[navigation.page],static_cast<int>(std::ceil(overflow/u)));
        const int offset=std::min(px(static_cast<float>(navigation.scroll[navigation.page])),overflow);
        SaveDC(dc);IntersectClipRect(dc,margin,body_top,right,body_bottom);
        text(pages[navigation.page],margin,body_top-offset,right,body_top-offset+measured.bottom+px(28),22,FW_NORMAL,RGB(255,255,255),DT_WORDBREAK);
        RestoreDC(dc,-1);
        std::string footer="LT / RT  Section     D-pad  Scroll     B  Back";
        if(overflow) footer+="     "+std::to_string(static_cast<int>(100LL*offset/overflow))+"%";
        text(footer,margin,draw.height-px(39),right,draw.height-px(10),18,FW_NORMAL,RGB(199,219,245),DT_SINGLELINE);
        auto *bytes=static_cast<unsigned char*>(bits);
        // GDI text does not maintain alpha; this full-screen surface is opaque.
        for(size_t i=3;i<draw.capacity;i+=4) bytes[i]=255;
        pixels.assign(bytes,bytes+draw.capacity);
        SelectObject(dc,old_bitmap);DeleteObject(bitmap);DeleteDC(dc);
        width=draw.width;height=draw.height;paint_key=key;draw.changed=1;
    }
    if(draw.changed || draw.redraw){std::memcpy(draw.pixels,pixels.data(),pixels.size());draw.changed=1;}
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
