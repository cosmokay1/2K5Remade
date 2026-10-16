#include "scene.h"
#include <algorithm>
#include <iostream>
int main(int argc,char** argv) {
    try {
        using namespace shadow_proof;
        const Vec left{-2,6,-2},right{2,6,-2};
        const auto a=reference(left),b=reference(right),clear=reference(left,false);
        const auto count=std::count(a.begin(),a.end(),1u);
        if(count<100 || count>size*size/4 || a==b || std::count(clear.begin(),clear.end(),1u))
            throw std::runtime_error("Missing shadow, unmoving shadow or failed unoccluded control");
        // Independently known rays: through the plate, away, parallel and beyond the light.
        if(!plate_hit({0,0,0},{0,1,0},2) || plate_hit({2,0,0},{0,1,0},2) ||
           plate_hit({0,0,0},{1,0,0},2) || plate_hit({0,0,0},{0,1,0},.5f))
            throw std::runtime_error("Ray/rectangle segment regression");
        for(unsigned y=0;y<size;++y) for(unsigned x=0;x<size;++x)
            if(a[y*size+x]!=b[y*size+(size-1-x)]) throw std::runtime_error("Symmetric lights must mirror their shadows");
        if(argc==2) {
            std::filesystem::create_directories(argv[1]);
            image(std::filesystem::path(argv[1])/"cpu-left.ppm",a);
            image(std::filesystem::path(argv[1])/"cpu-right.ppm",b);
            image(std::filesystem::path(argv[1])/"cpu-unoccluded.ppm",clear);
        }
        std::cout<<"CPU reference only: moved-light, finite-ray, symmetry and clear controls passed; shadow pixels="<<count<<"\n";
        return 0;
    } catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}
