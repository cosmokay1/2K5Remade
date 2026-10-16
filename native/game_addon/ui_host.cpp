#include "ui.h"
extern "C" {
#include "loader.h"
}
#include <algorithm>
#include <cstring>
#include <vector>
/* Input owner only. An addon failure must not release a held UI button into the
 * original menu. Other presses work normally after a neutral packet. */
static bool captured[4];
static bool neutral(const NFL2K5AddonInput& input) {
    if(input.buttons) return false;
    for(auto value:input.analog) if(value>30) return false;
    for(auto value:input.axes) if(value>8000 || value<-8000) return false;
    return true;
}
extern "C" void nfl2k5_addon_ui_input(NFL2K5AddonInput *input) {
    if(!input || input->port>=4) return;
    const auto port=input->port;
    const int result=nfl2k5_addon_event(NFL2K5_ADDON_UI_INPUT,input,sizeof(*input));
    const bool held=neutral(*input)==false;
    if(!result && !captured[port]) return;
    captured[port]=result!=0 || held;
    *input={};input->port=port;
    if(result==NFL2K5_ADDON_UI_BACK) input->analog[1]=255;
}
extern "C" int nfl2k5_addon_ui_draw(int width,int height,const void **pixels,int *changed) {
    // One presentation owner, matching the existing native HUD callback.
    static std::vector<unsigned char> surface;
    static int old_width,old_height;
    if(!pixels || !changed) return 0;
    *pixels=nullptr;*changed=0;
    if(width<320 || height<240 || width>2048 || height>2048) return 0;
    const size_t capacity=static_cast<size_t>(width)*height*4;
    try {surface.resize(capacity);} catch(...) {return 0;}
    NFL2K5AddonDraw draw{static_cast<uint32_t>(width),static_cast<uint32_t>(height),
        static_cast<uint32_t>(width*4),capacity,surface.data(),width!=old_width || height!=old_height,0};
    const int result=nfl2k5_addon_event(NFL2K5_ADDON_UI_DRAW,&draw,sizeof(draw));
    if(result!=1 || draw.width!=static_cast<uint32_t>(width) || draw.height!=static_cast<uint32_t>(height) ||
       draw.stride!=static_cast<uint32_t>(width*4) || draw.capacity!=capacity || draw.pixels!=surface.data()) {
        old_width=old_height=0;return 0;
    }
    // A resize needs complete pixels, even if an addon mistakenly says cached.
    if((width!=old_width || height!=old_height) && !draw.changed) {old_width=old_height=0;return 0;}
    old_width=width;old_height=height;
    *pixels=surface.data();*changed=draw.changed!=0;return 1;
}
