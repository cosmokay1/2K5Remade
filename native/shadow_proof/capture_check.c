/* Execute the actual opt-in renderer capture helper against an authored D3D11
 * target. No game/retail inputs, guest state, model or save access. */
#define COBJMACROS
#include <windows.h>
#include <d3d11.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <assert.h>
#define GPU_MAX_SURFACES 1
typedef struct {float x,y,z,w,tc[4][4];int ok;} XfVert;
typedef struct {
    uint32_t guest,w,h,scale,ox;
    ID3D11Texture2D *tex;
} GpuSurface;
static struct {ID3D11Device *dev;ID3D11DeviceContext *ctx;uint32_t frame;GpuSurface surf[1];} s_gpu11;
static struct {uint32_t draws,color_offset;struct {int valid;uint32_t offset;} tex;int attr[1];} s_gpu;
static struct {uint32_t start,depth_test,depth_mask;float c[192][4];} s_vp;
static uint32_t dma_resolve(uint32_t address){return address;}
static const char *env_cached(const char *key){return getenv(key);}
static void fetch_attr(const int *attribute,uint32_t index,float out[4]) {
    (void)attribute;out[0]=(float)index;out[1]=0;out[2]=(float)(index%2);out[3]=1;
}
#include "../../external/xboxrecomp/src/kernel/nv2a_gpu_capture.inc.c"
static void request(const char *prefix){char path[800];FILE *f;snprintf(path,sizeof(path),"%s.request",prefix);f=fopen(path,"wb");assert(f);fclose(f);}
int main(void) {
    char temp[MAX_PATH],directory[MAX_PATH],prefix[768],path[800],line[8192];
    FILE *f;D3D_FEATURE_LEVEL level;D3D11_TEXTURE2D_DESC desc={0};ID3D11RenderTargetView *rtv=NULL;
    const float color[4]={1,0,0,1};XfVert vertex={0};unsigned triangles=0;int ended=0;
    HRESULT hr=D3D11CreateDevice(NULL,D3D_DRIVER_TYPE_HARDWARE,NULL,0,NULL,0,D3D11_SDK_VERSION,&s_gpu11.dev,&level,&s_gpu11.ctx);
    if(FAILED(hr)) {
        puts("D3D11 capture fixture using WARP; this is not the DXR hardware proof");
        hr=D3D11CreateDevice(NULL,D3D_DRIVER_TYPE_WARP,NULL,0,NULL,0,D3D11_SDK_VERSION,&s_gpu11.dev,&level,&s_gpu11.ctx);
    }
    assert(SUCCEEDED(hr));
    desc.Width=desc.Height=64;desc.MipLevels=desc.ArraySize=1;desc.Format=DXGI_FORMAT_B8G8R8A8_UNORM;
    desc.SampleDesc.Count=1;desc.BindFlags=D3D11_BIND_RENDER_TARGET;
    assert(SUCCEEDED(ID3D11Device_CreateTexture2D(s_gpu11.dev,&desc,NULL,&s_gpu11.surf[0].tex)));
    assert(SUCCEEDED(ID3D11Device_CreateRenderTargetView(s_gpu11.dev,(ID3D11Resource*)s_gpu11.surf[0].tex,NULL,&rtv)));
    ID3D11DeviceContext_ClearRenderTargetView(s_gpu11.ctx,rtv,color);
    s_gpu11.surf[0].w=s_gpu11.surf[0].h=64;s_gpu11.surf[0].scale=1;s_gpu11.surf[0].guest=1234;s_gpu.color_offset=1234;
    s_vp.depth_test=s_vp.depth_mask=1;s_gpu.tex.valid=1;s_gpu.tex.offset=5678;vertex.w=1;vertex.ok=1;
    _putenv_s("RECOMP_SHADOW_CAPTURE","");assert(!gpu_capture_begin(0,&s_gpu11.surf[0]));assert(s_capture.mode==1);
    memset(&s_capture,0,sizeof(s_capture));_putenv_s("RECOMP_SHADOW_CAPTURE","relative");assert(!gpu_capture_begin(0,&s_gpu11.surf[0]));assert(s_capture.mode==1);
    assert(GetTempPathA(sizeof(temp),temp));assert(GetTempFileNameA(temp,"shc",0,directory));
    assert(DeleteFileA(directory));assert(CreateDirectoryA(directory,NULL));snprintf(prefix,sizeof(prefix),"%s\\frame",directory);
    memset(&s_capture,0,sizeof(s_capture));_putenv_s("RECOMP_SHADOW_CAPTURE",prefix);
    assert(!gpu_capture_begin(0,&s_gpu11.surf[0]));request(prefix);s_gpu11.frame++;
    assert(!gpu_capture_begin(1,&s_gpu11.surf[0]));assert(gpu_capture_begin(0,&s_gpu11.surf[0]));
    for(unsigned i=0;i<8;i++)gpu_capture_triangle(&vertex,&vertex,&vertex,0,1,2);
    assert(s_capture.draws==1 && s_capture.triangles==4);
    assert(!gpu_capture_begin(1,&s_gpu11.surf[0]));
    gpu_capture_triangle(&vertex,&vertex,&vertex,0,1,2);assert(s_capture.triangles==4);
    s_gpu.draws++;assert(gpu_capture_begin(0,&s_gpu11.surf[0]));gpu_capture_triangle(&vertex,&vertex,&vertex,0,1,2);
    gpu_capture_finish();assert(s_capture.mode==4 && !s_capture.file && !s_capture.truncated);
    snprintf(path,sizeof(path),"%s.jsonl",prefix);f=fopen(path,"rb");assert(f);
    while(fgets(line,sizeof(line),f)) {if(strstr(line,"\"type\":\"triangle\""))triangles++;if(strstr(line,"\"type\":\"end\"")){assert(strstr(line,"\"truncated\":false"));ended++;}}
    fclose(f);assert(triangles==5 && ended==1);
    snprintf(path,sizeof(path),"%s.ppm",prefix);f=fopen(path,"rb");assert(f);
    assert(fgets(line,sizeof(line),f) && !strcmp(line,"P6\n"));assert(fgets(line,sizeof(line),f) && !strcmp(line,"64 64\n"));
    assert(fgets(line,sizeof(line),f) && !strcmp(line,"255\n"));
    assert(fgetc(f)==255 && fgetc(f)==0 && fgetc(f)==0);fclose(f);
    // Existing captures are immutable; a second process/session may not replace one.
    memset(&s_capture,0,sizeof(s_capture));request(prefix);s_gpu11.frame++;
    assert(!gpu_capture_begin(0,&s_gpu11.surf[0]) && s_capture.mode==4);
    snprintf(path,sizeof(path),"%s.jsonl",prefix);f=fopen(path,"rb");assert(f && fgetc(f)=='{');fclose(f);
    ID3D11RenderTargetView_Release(rtv);ID3D11Texture2D_Release(s_gpu11.surf[0].tex);
    ID3D11DeviceContext_Release(s_gpu11.ctx);ID3D11Device_Release(s_gpu11.dev);
    printf("Capture fixture: %s\n",prefix);
    puts("Actual D3D11 capture: opt-in, trigger, bounded samples, PPM readback, end marker and overwrite refusal passed");return 0;
}
