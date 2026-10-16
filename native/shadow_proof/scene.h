#pragma once
#include <array>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <vector>

namespace shadow_proof {
constexpr unsigned size=256;
struct Vec {float x,y,z;};
inline Vec operator-(Vec a,Vec b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
inline float dot(Vec a,Vec b){return a.x*b.x+a.y*b.y+a.z*b.z;}
// Two opaque, double-sided triangles: a square one metre above the receiver.
constexpr std::array<Vec,6> vertices{{{-.75f,1,-.75f},{.75f,1,-.75f},{.75f,1,.75f},
                                    {-.75f,1,-.75f},{.75f,1,.75f},{-.75f,1,.75f}}};
// Closed box used only by the optional in-engine experiment (metres).
inline std::vector<Vec> box_vertices() {
    const Vec corners[]={{-.73f,.07f,-.73f},{.73f,.07f,-.73f},{.73f,1.47f,-.73f},{-.73f,1.47f,-.73f},
                         {-.73f,.07f,.73f},{.73f,.07f,.73f},{.73f,1.47f,.73f},{-.73f,1.47f,.73f}};
    const unsigned indices[]={0,1,2,0,2,3,4,6,5,4,7,6,0,4,5,0,5,1,3,2,6,3,6,7,0,3,7,0,7,4,1,5,6,1,6,2};
    std::vector<Vec> result;for(auto i:indices)result.push_back(corners[i]);return result;
}
inline bool box_hit(Vec o,Vec direction,float limit) {
    const double origin[]={o.x,o.y,o.z},d[]={direction.x,direction.y,direction.z};
    const double lower[]={-.73f,.07f,-.73f},upper[]={.73f,1.47f,.73f};
    double enter=.001,leave=limit;
    for(int axis=0;axis<3;axis++) {
        if(std::abs(d[axis])<1e-9) {if(origin[axis]<lower[axis] || origin[axis]>upper[axis])return false;}
        else {double a=(lower[axis]-origin[axis])/d[axis],b=(upper[axis]-origin[axis])/d[axis];
            if(a>b)std::swap(a,b);enter=std::max(enter,a);leave=std::min(leave,b);if(enter>leave)return false;}
    }
    return true;
}
inline Vec origin(unsigned x,unsigned y){return {(x+.5f)/size*8-4,.001f,(y+.5f)/size*8-4};}
inline bool plate_hit(Vec o,Vec direction,float limit) {
    // Analytic rectangle reference, independent of GPU triangle traversal and
    // its watertight shared diagonal. Use double precision at the intersection.
    if(std::abs(direction.y)<1e-7f) return false;
    const double distance=(1.0-o.y)/direction.y;
    if(distance<.001f || distance>limit) return false;
    return std::abs(o.x+distance*direction.x)<=.75 && std::abs(o.z+distance*direction.z)<=.75;
}
inline std::vector<uint32_t> reference(Vec light,bool blocker=true,bool box=false) {
    std::vector<uint32_t> result(size*size);
    for(unsigned y=0;y<size;++y) for(unsigned x=0;x<size;++x) {
        const auto o=origin(x,y),delta=light-o;
        const float distance=std::sqrt(dot(delta,delta));
        const Vec direction{delta.x/distance,delta.y/distance,delta.z/distance};
        result[y*size+x]=blocker && (box?box_hit(o,direction,distance-.001f):plate_hit(o,direction,distance-.001f));
    }
    return result;
}
inline void image(const std::filesystem::path& path,const std::vector<uint32_t>& mask) {
    if(mask.size()!=size*size) throw std::runtime_error("Wrong shadow image dimensions");
    std::ofstream out(path,std::ios::binary);out<<"P6\n"<<size<<" "<<size<<"\n255\n";
    for(unsigned y=0;y<size;++y) for(unsigned x=0;x<size;++x) {
        const bool stripe=(x/16+y/16)%2;
        const unsigned char color[3]={static_cast<unsigned char>(mask[y*size+x]?20:stripe?73:64),
            static_cast<unsigned char>(mask[y*size+x]?38:stripe?130:116),static_cast<unsigned char>(mask[y*size+x]?24:stripe?76:68)};
        out.write(reinterpret_cast<const char*>(color),3);
    }
    if(!out) throw std::runtime_error("Could not write shadow image");
}
}
