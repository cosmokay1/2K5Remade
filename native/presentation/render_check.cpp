/* Execute the real native renderer with authored match state, no game assets,
 * windows, credentials or inference. No WebView implementation is linked. */
#include <windows.h>
#include <objbase.h>
#include "presentation/presentation_host.h"
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

extern "C" {
ptrdiff_t g_xbox_mem_offset;
int xbox_hud_shared_failed=0;
struct XboxHudFrame { int bb_w,bb_h; float game_x,game_y,game_w,game_h; };
struct XboxHudImage { const void* pixels; int w,h,stride,x,y,changed,dw,dh; void* shared; };
using Callback=int(*)(const XboxHudFrame*,XboxHudImage*);
static Callback render;
int (*xbox_present_in_match_fn)(void)=nullptr;
void xbox_PresentSetHudCallback(Callback callback) { render=callback; }
void xbox_AudioSetGameGain(float) {}
void xbox_AudioMuteGameMusic(int) {}
void xbox_AudioSetCommentaryGain(float) {}
void nfl2k5_input_press_a(unsigned) {}
float xbox_AudioGameLevel(void) { return 0; }
void xbox_AudioSetCaptureMix(void (*)(int16_t*,int)) {}
void xbox_PresentRecord(int) {}
const char* xbox_user_dir(void) { return ""; }
char* xbox_user_path(const char*,char* out,size_t size) { snprintf(out,size,"NUL");return out; }
void nfl2k5_presentation_init(void);
int nfl2k5_pres_package_count(void);
const char* nfl2k5_pres_package_name(int);
void nfl2k5_pres_set(int,int);
}
namespace nfl2k5 {
std::unique_ptr<PresentationHost> create_webview2_presentation_host() {
    throw std::runtime_error("Native scoreboard attempted to start a browser");
}
}
static void require(bool ok,const char* detail) { if(!ok) throw std::runtime_error(detail); }
int main(int argc,char** argv) {
    if(argc!=3) return 1;
    try {
        std::filesystem::current_path(argv[1]);
        const std::filesystem::path output=argv[2];
        std::filesystem::create_directories(output);
        CoInitializeEx(nullptr,COINIT_MULTITHREADED);
        void* memory=VirtualAlloc(nullptr,0x10000000,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
        require(memory!=nullptr,"Authored guest-memory allocation failed");
        g_xbox_mem_offset=reinterpret_cast<ptrdiff_t>(memory);
        auto word=[&](size_t at,uint32_t v){std::memcpy(static_cast<char*>(memory)+at,&v,4);};
        auto real=[&](size_t at,float v){std::memcpy(static_cast<char*>(memory)+at,&v,4);};
        word(0xE6028C,0x10000);real(0x10010,791);word(0xE602C4,1);word(0xE602B4,4);
        word(0xE5FC68,0x11000);word(0xE5FC28,0x12000);
        word(0xE60294,0x13000);real(0x13010,40);
        _putenv_s("NFL2K5_PRES_TEST","1");
        nfl2k5_presentation_init();require(render!=nullptr,"Missing real HUD callback");
        nfl2k5_pres_set(1,0);nfl2k5_pres_set(2,0);nfl2k5_pres_set(3,0);nfl2k5_pres_set(5,0);
        const char* names[]={"NFL on FOX","NFL on CBS","NBC Sunday Night Football"};
        for(int style=0;style<3;++style) {
            real(0x13010,40);
            int selected=-1;
            for(int i=0;i<nfl2k5_pres_package_count();++i) {
                const char* name=nfl2k5_pres_package_name(i);
                if(strcmp(name,names[style])==0) selected=i;
            }
            // NBC's private reference media is not distributed with this fixture.
            if(style==2 && !std::filesystem::exists("mods/presentations/NBC_SNF/assets/plates/pod.png"))continue;
            require(selected>0,"Expected existing native style missing");
            nfl2k5_pres_set(0,selected);nfl2k5_pres_set(1,0);nfl2k5_pres_set(2,0);
            XboxHudFrame frame{1280,720,0,0,1280,720};XboxHudImage image{};
            // Warm up font/renderer creation before waiting for the final
            // static frame. First-use initialization may exceed the fade time.
            int stable=0;
            for(int sample=0;sample<400 && stable<20;++sample) {
                image={};render(&frame,&image);
                stable=image.pixels && !image.changed ? stable+1 : 0;
                Sleep(10);
            }
            require(stable==20,"Native style did not settle after its fade");
            require(image.pixels && !image.shared && image.w>0 && image.h>0 && image.stride==image.w*4,
                    "Real renderer did not supply a CPU BGRA surface");
            const auto* pixels=static_cast<const unsigned char*>(image.pixels);
            size_t colored=0;
            for(int y=0;y<image.h;++y) for(int x=0;x<image.w;++x) {
                const auto* pixel=pixels+y*image.stride+x*4;
                if(pixel[3] && (pixel[0] || pixel[1] || pixel[2])) ++colored;
            }
            require(colored>500,"Empty native scoreboard render");
            const auto base=output/std::to_string(style);
            std::ofstream raw(base.string()+".bgra",std::ios::binary);
            raw.write(static_cast<const char*>(image.pixels),static_cast<std::streamsize>(image.stride)*image.h);
            require(raw.good(),"Failed to retain rendered pixels");
            std::ofstream metadata(base.string()+".txt");
            metadata<<image.w<<' '<<image.h<<' '<<image.stride<<' '<<image.x<<' '<<image.y<<' '<<image.dw<<' '<<image.dh<<'\n';
            std::printf("Rendered %s: %dx%d, %zu colored pixels, no browser\n",names[style],image.w,image.h,colored);
            std::vector<unsigned char> before(pixels,pixels+image.stride*image.h);
            real(0x13010,39);image={};render(&frame,&image);
            require(image.changed && image.pixels,"Stopped period clock prevented play-clock repaint");
            if(style!=1)require(std::memcmp(before.data(),image.pixels,before.size())!=0,"Play-clock text failed to change pixels");
            std::printf("Play clock updated independently: %s\n",names[style]);
        }
        return 0;
    } catch(const std::exception& error) { std::fprintf(stderr,"%s\n",error.what());return 2; }
}
