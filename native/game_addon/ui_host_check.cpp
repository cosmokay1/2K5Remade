#include "ui.h"
#include <cstdio>
#include <cstring>
#include <stdexcept>
static int reply;
static bool draw_enabled,draw_changed,malformed;
extern "C" int nfl2k5_addon_event(const char *name,const void *data,size_t size) {
    if(!strcmp(name,NFL2K5_ADDON_UI_INPUT) && size==sizeof(NFL2K5AddonInput)) return reply;
    if(strcmp(name,NFL2K5_ADDON_UI_DRAW) || size!=sizeof(NFL2K5AddonDraw) || !draw_enabled) return 0;
    auto& draw=*const_cast<NFL2K5AddonDraw*>(static_cast<const NFL2K5AddonDraw*>(data));
    if(draw_changed) std::memset(draw.pixels,0x51,draw.capacity);
    draw.changed=draw_changed;
    if(malformed) ++draw.stride;
    return 1;
}
static void require(bool ok){if(!ok) throw std::runtime_error("Addon UI host boundary failed");}
int main() {
    try {
        NFL2K5AddonInput input{};input.port=2;input.buttons=0x1f;input.analog[0]=255;input.axes[0]=32000;
        const auto original=input;nfl2k5_addon_ui_input(&input);require(!memcmp(&input,&original,sizeof(input)));
        reply=1;nfl2k5_addon_ui_input(&input);require(input.port==2 && !input.buttons && !input.analog[0] && !input.axes[0]);
        reply=0;input=original;nfl2k5_addon_ui_input(&input);require(!input.buttons && !input.analog[0]);
        input={};input.port=2;nfl2k5_addon_ui_input(&input); // neutral releases quarantine
        input=original;nfl2k5_addon_ui_input(&input);require(!memcmp(&input,&original,sizeof(input)));
        reply=2;nfl2k5_addon_ui_input(&input);require(input.analog[1]==255 && !input.buttons && !input.analog[0] && !input.axes[0]);
        reply=17;input=original;nfl2k5_addon_ui_input(&input);require(!input.analog[1] && !input.buttons); // no invented forwarding mode
        input.port=9;input.buttons=1;nfl2k5_addon_ui_input(&input);require(input.buttons==1);
        const void *pixels=reinterpret_cast<void*>(1);int changed=1;
        require(!nfl2k5_addon_ui_draw(1280,800,&pixels,&changed) && !pixels && !changed);
        draw_enabled=true;require(!nfl2k5_addon_ui_draw(1280,800,&pixels,&changed)); // no initial pixels
        draw_changed=true;require(nfl2k5_addon_ui_draw(1280,800,&pixels,&changed) && changed);
        require(static_cast<const unsigned char*>(pixels)[1280*800*4-1]==0x51);
        draw_changed=false;require(nfl2k5_addon_ui_draw(1280,800,&pixels,&changed) && !changed);
        require(!nfl2k5_addon_ui_draw(1280,720,&pixels,&changed));
        draw_changed=true;require(nfl2k5_addon_ui_draw(1280,720,&pixels,&changed));
        malformed=true;require(!nfl2k5_addon_ui_draw(1280,720,&pixels,&changed) && !pixels);
        require(!nfl2k5_addon_ui_draw(100000,800,&pixels,&changed));
        require(!nfl2k5_addon_ui_draw(1280,800,nullptr,&changed));
        std::puts("Addon UI input quarantine, explicit Back, owned BGRA and bounds passed");return 0;
    } catch(const std::exception& error){std::fprintf(stderr,"%s\n",error.what());return 1;}
}
