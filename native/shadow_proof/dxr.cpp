// Standalone, asset-free GPU correctness proof. No game hooks or software fallback.
#include "scene.h"
#include "../../external/xboxrecomp/src/kernel/nv2a_shadow_live.h"
#include <windows.h>
#include <d3d12.h>
#include <dxgi1_6.h>
#include <wrl/client.h>
#include <algorithm>
#include <cstring>
#include <iostream>
#include <iterator>
#include <string>
using Microsoft::WRL::ComPtr;
using namespace shadow_proof;
static void check(HRESULT hr,const char* operation) {
    if(FAILED(hr)) throw std::runtime_error(std::string(operation)+" failed HRESULT="+std::to_string(static_cast<unsigned long>(hr)));
}
struct Gpu {
    ComPtr<ID3D12Device5> device;
    ComPtr<ID3D12CommandQueue> queue;
    ComPtr<ID3D12CommandAllocator> allocator;
    ComPtr<ID3D12GraphicsCommandList4> commands;
    ComPtr<ID3D12Fence> fence;
    UINT64 sequence=0;
    HANDLE event=nullptr;
    ~Gpu(){if(event) CloseHandle(event);}
    bool open() {
        ComPtr<IDXGIFactory6> factory;check(CreateDXGIFactory2(0,IID_PPV_ARGS(&factory)),"DXGI factory");
        for(UINT index=0;;++index) {
            ComPtr<IDXGIAdapter1> adapter;
            const auto status=factory->EnumAdapters1(index,&adapter);
            if(status==DXGI_ERROR_NOT_FOUND) break;
            check(status,"Adapter enumeration");
            DXGI_ADAPTER_DESC1 desc{};check(adapter->GetDesc1(&desc),"Adapter description");
            if(desc.Flags&DXGI_ADAPTER_FLAG_SOFTWARE) continue;
            ComPtr<ID3D12Device5> candidate;
            if(FAILED(D3D12CreateDevice(adapter.Get(),D3D_FEATURE_LEVEL_12_0,IID_PPV_ARGS(&candidate)))) continue;
            D3D12_FEATURE_DATA_D3D12_OPTIONS5 options{};
            D3D12_FEATURE_DATA_SHADER_MODEL shader{D3D_SHADER_MODEL_6_5};
            if(FAILED(candidate->CheckFeatureSupport(D3D12_FEATURE_D3D12_OPTIONS5,&options,sizeof(options))) ||
               options.RaytracingTier<D3D12_RAYTRACING_TIER_1_1 ||
               FAILED(candidate->CheckFeatureSupport(D3D12_FEATURE_SHADER_MODEL,&shader,sizeof(shader))) ||
               shader.HighestShaderModel<D3D_SHADER_MODEL_6_5) continue;
            device=candidate;std::wcout<<L"GPU: "<<desc.Description<<L"; DXR 1.1 and SM 6.5 supported\n";break;
        }
        if(!device) return false;
        D3D12_COMMAND_QUEUE_DESC description{};description.Type=D3D12_COMMAND_LIST_TYPE_DIRECT;
        check(device->CreateCommandQueue(&description,IID_PPV_ARGS(&queue)),"Queue");
        check(device->CreateCommandAllocator(description.Type,IID_PPV_ARGS(&allocator)),"Allocator");
        check(device->CreateCommandList(0,description.Type,allocator.Get(),nullptr,IID_PPV_ARGS(&commands)),"Command list");
        check(device->CreateFence(0,D3D12_FENCE_FLAG_NONE,IID_PPV_ARGS(&fence)),"Fence");
        event=CreateEventW(nullptr,FALSE,FALSE,nullptr);
        if(!event) throw std::runtime_error("Fence event creation failed");
        return true;
    }
    ComPtr<ID3D12Resource> buffer(UINT64 bytes,D3D12_HEAP_TYPE heap,D3D12_RESOURCE_STATES state,
                                D3D12_RESOURCE_FLAGS flags=D3D12_RESOURCE_FLAG_NONE) {
        if(!bytes) throw std::runtime_error("Empty GPU allocation");
        D3D12_HEAP_PROPERTIES properties{};properties.Type=heap;properties.CreationNodeMask=properties.VisibleNodeMask=1;
        D3D12_RESOURCE_DESC desc{};desc.Dimension=D3D12_RESOURCE_DIMENSION_BUFFER;desc.Width=bytes;
        desc.Height=1;desc.DepthOrArraySize=1;desc.MipLevels=1;desc.SampleDesc.Count=1;
        desc.Layout=D3D12_TEXTURE_LAYOUT_ROW_MAJOR;desc.Flags=flags;
        ComPtr<ID3D12Resource> resource;
        check(device->CreateCommittedResource(&properties,D3D12_HEAP_FLAG_NONE,&desc,state,nullptr,IID_PPV_ARGS(&resource)),"Buffer");
        return resource;
    }
    ComPtr<ID3D12Resource> upload(const void* data,size_t bytes) {
        auto resource=buffer(bytes,D3D12_HEAP_TYPE_UPLOAD,D3D12_RESOURCE_STATE_GENERIC_READ);
        void* mapped=nullptr;D3D12_RANGE no_read{0,0};check(resource->Map(0,&no_read,&mapped),"Upload map");
        std::memcpy(mapped,data,bytes);resource->Unmap(0,nullptr);return resource;
    }
    void uav(ID3D12Resource* resource) {
        D3D12_RESOURCE_BARRIER barrier{};barrier.Type=D3D12_RESOURCE_BARRIER_TYPE_UAV;barrier.UAV.pResource=resource;
        commands->ResourceBarrier(1,&barrier);
    }
    void transition(ID3D12Resource* resource,D3D12_RESOURCE_STATES before,D3D12_RESOURCE_STATES after) {
        D3D12_RESOURCE_BARRIER barrier{};barrier.Type=D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;
        barrier.Transition={resource,D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES,before,after};commands->ResourceBarrier(1,&barrier);
    }
    void finish() {
        check(commands->Close(),"Close commands");ID3D12CommandList* lists[]={commands.Get()};queue->ExecuteCommandLists(1,lists);
        check(queue->Signal(fence.Get(),++sequence),"Signal fence");
        check(fence->SetEventOnCompletion(sequence,event),"Fence completion");
        if(WaitForSingleObject(event,15000)!=WAIT_OBJECT_0) throw std::runtime_error("GPU completion timed out; no proof result");
        check(device->GetDeviceRemovedReason(),"GPU completion");
        check(allocator->Reset(),"Reset allocator");check(commands->Reset(allocator.Get(),nullptr),"Reset commands");
    }
};
int main(int argc,char** argv) {
    if(argc==3 && std::string(argv[1])=="--stop") {
        const std::string name=std::string(argv[2])+"-stop";
        HANDLE stop=OpenEventA(EVENT_MODIFY_STATE,FALSE,name.c_str());
        if(!stop)return 1;const bool ok=SetEvent(stop)!=0;CloseHandle(stop);return ok?0:1;
    }
    const bool resume=argc==6 && std::string(argv[3])=="--resume-live";
    const bool live=resume || (argc==6 && (std::string(argv[3])=="--live" || std::string(argv[3])=="--live-check"));
    if(argc!=3 && !(argc==4 && std::string(argv[3])=="--box") && !live){std::cerr<<"Usage: shadow_dxr shadow.cso output-directory [--box | --live[-check] mapping-name seconds]\n";return 1;}
    try {
        const std::filesystem::path directory=argv[2];std::filesystem::create_directories(directory);
        // A skipped/failed attempt must never leave an earlier success receipt.
        std::filesystem::remove(directory/"passed.txt");
        if(live)std::filesystem::remove(directory/"live-passed.txt");
        Gpu gpu;
        if(!gpu.open()){std::cout<<"UNSUPPORTED: no hardware adapter exposes DXR 1.1 + Shader Model 6.5. GPU proof NOT run.\n";return 77;}
        std::ifstream shader_file(argv[1],std::ios::binary);
        const std::vector<char> shader((std::istreambuf_iterator<char>(shader_file)),{});
        if(shader.empty()) throw std::runtime_error("Missing compiled DXR compute shader");
        const bool box=argc>=4;
        const std::vector<Vec> mesh_vertices=box?box_vertices():std::vector<Vec>(vertices.begin(),vertices.end());
        auto mesh=gpu.upload(mesh_vertices.data(),mesh_vertices.size()*sizeof(Vec));
        D3D12_RAYTRACING_GEOMETRY_DESC geometry{};geometry.Type=D3D12_RAYTRACING_GEOMETRY_TYPE_TRIANGLES;
        geometry.Flags=D3D12_RAYTRACING_GEOMETRY_FLAG_OPAQUE;
        geometry.Triangles.VertexBuffer={mesh->GetGPUVirtualAddress(),sizeof(Vec)};
        geometry.Triangles.VertexCount=static_cast<UINT>(mesh_vertices.size());geometry.Triangles.VertexFormat=DXGI_FORMAT_R32G32B32_FLOAT;
        D3D12_BUILD_RAYTRACING_ACCELERATION_STRUCTURE_INPUTS bottom{};
        bottom.Type=D3D12_RAYTRACING_ACCELERATION_STRUCTURE_TYPE_BOTTOM_LEVEL;
        bottom.DescsLayout=D3D12_ELEMENTS_LAYOUT_ARRAY;bottom.NumDescs=1;bottom.pGeometryDescs=&geometry;
        bottom.Flags=D3D12_RAYTRACING_ACCELERATION_STRUCTURE_BUILD_FLAG_PREFER_FAST_TRACE;
        D3D12_RAYTRACING_ACCELERATION_STRUCTURE_PREBUILD_INFO bottom_size{};
        gpu.device->GetRaytracingAccelerationStructurePrebuildInfo(&bottom,&bottom_size);
        auto blas=gpu.buffer(bottom_size.ResultDataMaxSizeInBytes,D3D12_HEAP_TYPE_DEFAULT,
            D3D12_RESOURCE_STATE_RAYTRACING_ACCELERATION_STRUCTURE,D3D12_RESOURCE_FLAG_ALLOW_UNORDERED_ACCESS);
        D3D12_RAYTRACING_INSTANCE_DESC instance{};
        instance.Transform[0][0]=instance.Transform[1][1]=instance.Transform[2][2]=1;
        instance.InstanceMask=1;instance.AccelerationStructure=blas->GetGPUVirtualAddress();
        auto instances=gpu.upload(&instance,sizeof(instance));
        D3D12_BUILD_RAYTRACING_ACCELERATION_STRUCTURE_INPUTS top{};
        top.Type=D3D12_RAYTRACING_ACCELERATION_STRUCTURE_TYPE_TOP_LEVEL;top.DescsLayout=D3D12_ELEMENTS_LAYOUT_ARRAY;
        top.NumDescs=1;top.InstanceDescs=instances->GetGPUVirtualAddress();top.Flags=bottom.Flags;
        D3D12_RAYTRACING_ACCELERATION_STRUCTURE_PREBUILD_INFO top_size{};
        gpu.device->GetRaytracingAccelerationStructurePrebuildInfo(&top,&top_size);
        auto tlas=gpu.buffer(top_size.ResultDataMaxSizeInBytes,D3D12_HEAP_TYPE_DEFAULT,
            D3D12_RESOURCE_STATE_RAYTRACING_ACCELERATION_STRUCTURE,D3D12_RESOURCE_FLAG_ALLOW_UNORDERED_ACCESS);
        auto scratch=gpu.buffer(std::max(bottom_size.ScratchDataSizeInBytes,top_size.ScratchDataSizeInBytes),
            D3D12_HEAP_TYPE_DEFAULT,D3D12_RESOURCE_STATE_UNORDERED_ACCESS,D3D12_RESOURCE_FLAG_ALLOW_UNORDERED_ACCESS);
        D3D12_BUILD_RAYTRACING_ACCELERATION_STRUCTURE_DESC build{};
        build.Inputs=bottom;build.DestAccelerationStructureData=blas->GetGPUVirtualAddress();build.ScratchAccelerationStructureData=scratch->GetGPUVirtualAddress();
        gpu.commands->BuildRaytracingAccelerationStructure(&build,0,nullptr);gpu.uav(blas.Get());gpu.uav(scratch.Get());
        build.Inputs=top;build.DestAccelerationStructureData=tlas->GetGPUVirtualAddress();
        gpu.commands->BuildRaytracingAccelerationStructure(&build,0,nullptr);gpu.uav(tlas.Get());
        gpu.finish();
        D3D12_ROOT_PARAMETER parameters[3]{};
        parameters[0].ParameterType=D3D12_ROOT_PARAMETER_TYPE_SRV;parameters[0].Descriptor.ShaderRegister=0;
        parameters[1].ParameterType=D3D12_ROOT_PARAMETER_TYPE_UAV;parameters[1].Descriptor.ShaderRegister=0;
        parameters[2].ParameterType=D3D12_ROOT_PARAMETER_TYPE_32BIT_CONSTANTS;parameters[2].Constants={0,0,4};
        D3D12_ROOT_SIGNATURE_DESC root_desc{};root_desc.NumParameters=3;root_desc.pParameters=parameters;
        ComPtr<ID3DBlob> serialized,error;
        check(D3D12SerializeRootSignature(&root_desc,D3D_ROOT_SIGNATURE_VERSION_1,&serialized,&error),"Serialize root signature");
        ComPtr<ID3D12RootSignature> root;
        check(gpu.device->CreateRootSignature(0,serialized->GetBufferPointer(),serialized->GetBufferSize(),IID_PPV_ARGS(&root)),"Root signature");
        D3D12_COMPUTE_PIPELINE_STATE_DESC pipeline{};pipeline.pRootSignature=root.Get();pipeline.CS={shader.data(),shader.size()};
        ComPtr<ID3D12PipelineState> state;check(gpu.device->CreateComputePipelineState(&pipeline,IID_PPV_ARGS(&state)),"Ray-query pipeline");
        const auto bytes=size*size*sizeof(uint32_t);
        auto output=gpu.buffer(bytes,D3D12_HEAP_TYPE_DEFAULT,D3D12_RESOURCE_STATE_UNORDERED_ACCESS,D3D12_RESOURCE_FLAG_ALLOW_UNORDERED_ACCESS);
        auto readback=gpu.buffer(bytes,D3D12_HEAP_TYPE_READBACK,D3D12_RESOURCE_STATE_COPY_DEST);
        struct Settings {Vec light;uint32_t mask;};
        const Settings cases[]={{{-2,6,-2},1},{{2,6,-2},1},{{-2,6,-2},0}};
        const char* names[]={"left","right","unoccluded"};
        HANDLE mapping=nullptr,mutex=nullptr,stop=nullptr,producer=nullptr;
        ShadowLiveFrame* shared=nullptr;
        unsigned duration=0,published=0,checked=0;
        ULONGLONG started=GetTickCount64(),next=started;
        if(live) {
            duration=static_cast<unsigned>(std::stoul(argv[5]));
            if(duration<1 || duration>600 || std::strlen(argv[4])>120)throw std::runtime_error("Live test limited to 1..600 seconds");
            const std::string name=argv[4];
            producer=CreateMutexA(nullptr,FALSE,(name+"-producer").c_str());
            if(!producer)throw std::runtime_error("Producer lease creation failed");
            const auto ownership=WaitForSingleObject(producer,0);
            if(ownership!=WAIT_OBJECT_0 && ownership!=WAIT_ABANDONED)throw std::runtime_error("Producer already active");
            mapping=CreateFileMappingA(INVALID_HANDLE_VALUE,nullptr,PAGE_READWRITE,0,sizeof(ShadowLiveFrame),name.c_str());
            if(!mapping || (GetLastError()==ERROR_ALREADY_EXISTS && !resume))throw std::runtime_error("Fresh local mapping required");
            shared=static_cast<ShadowLiveFrame*>(MapViewOfFile(mapping,FILE_MAP_ALL_ACCESS,0,0,sizeof(ShadowLiveFrame)));
            mutex=CreateMutexA(nullptr,FALSE,(name+"-mutex").c_str());stop=CreateEventA(nullptr,TRUE,FALSE,(name+"-stop").c_str());
            if(!shared || !mutex || !stop)throw std::runtime_error("Live transport creation failed");
            if(resume) {
                if(WaitForSingleObject(mutex,0)!=WAIT_OBJECT_0)throw std::runtime_error("Resume requires idle transport");
                const bool stale=shared->magic==SHADOW_LIVE_MAGIC && GetTickCount64()>shared->tick+2000;
                published=shared->sequence;ReleaseMutex(mutex);
                if(!stale)throw std::runtime_error("Resume requires a stale, stopped producer");
                ResetEvent(stop);
            } else std::memset(shared,0,sizeof(*shared));
            std::cout<<std::unitbuf<<"LIVE ready; 15Hz target; bounded "<<duration<<" seconds\n";
        }
        for(unsigned test=0;live || test<3;++test) {
            Settings settings=cases[live?0:test];
            if(live) {
                if(WaitForSingleObject(stop,0)==WAIT_OBJECT_0 || GetTickCount64()-started>=duration*1000ull)break;
                const auto now=GetTickCount64();if(now<next)Sleep(static_cast<DWORD>(next-now));
                const float phase=static_cast<float>(GetTickCount64()-started)*.0008f;
                settings.light={2.2f*std::sin(phase),6,-2};settings.mask=1;
            }
            gpu.commands->SetPipelineState(state.Get());gpu.commands->SetComputeRootSignature(root.Get());
            gpu.commands->SetComputeRootShaderResourceView(0,tlas->GetGPUVirtualAddress());
            gpu.commands->SetComputeRootUnorderedAccessView(1,output->GetGPUVirtualAddress());
            gpu.commands->SetComputeRoot32BitConstants(2,4,&settings,0);
            gpu.commands->Dispatch(size/8,size/8,1);
            gpu.transition(output.Get(),D3D12_RESOURCE_STATE_UNORDERED_ACCESS,D3D12_RESOURCE_STATE_COPY_SOURCE);
            gpu.commands->CopyResource(readback.Get(),output.Get());
            gpu.transition(output.Get(),D3D12_RESOURCE_STATE_COPY_SOURCE,D3D12_RESOURCE_STATE_UNORDERED_ACCESS);
            gpu.finish();
            void* mapped=nullptr;D3D12_RANGE range{0,bytes};check(readback->Map(0,&range,&mapped),"Readback map");
            std::vector<uint32_t> actual(size*size);std::memcpy(actual.data(),mapped,bytes);
            D3D12_RANGE no_write{0,0};readback->Unmap(0,&no_write);
            const bool verify=!live || std::string(argv[3])=="--live-check";
            if(verify) {
                const auto expected=reference(settings.light,settings.mask!=0,box);
                unsigned mismatches=0;for(size_t pixel=0;pixel<actual.size();++pixel)mismatches+=actual[pixel]!=expected[pixel];
                if(mismatches)throw std::runtime_error("GPU/reference disagreement: "+std::to_string(mismatches)+" pixels; proof failed");
                ++checked;
                if(!live)std::cout<<names[test]<<": 0 mismatched pixels of "<<actual.size()<<"\n";
            }
            if(live) {
                if(WaitForSingleObject(mutex,0)==WAIT_OBJECT_0) {
                    std::memcpy(shared->mask,actual.data(),bytes);shared->light[0]=settings.light.x;shared->light[1]=settings.light.y;shared->light[2]=settings.light.z;
                    shared->tick=GetTickCount64();shared->sequence=++published;shared->magic=SHADOW_LIVE_MAGIC;ReleaseMutex(mutex);
                }
                if(published && published%15==0)std::cout<<"LIVE frame="<<published<<" light_x="<<settings.light.x<<" elapsed_ms="<<GetTickCount64()-started<<"\n";
                next=std::max(next+67,GetTickCount64());
            } else {
                image(directory/(std::string("gpu-")+names[test]+".ppm"),actual);
                if(box) {std::ofstream raw(directory/(std::string("box-")+names[test]+".mask"),std::ios::binary);
                    raw.write(reinterpret_cast<const char*>(actual.data()),bytes);if(!raw)throw std::runtime_error("Mask export failed");}
            }
        }
        if(live) {
            if(!published || (std::string(argv[3])=="--live-check" && !checked))throw std::runtime_error("No live frames completed");
            std::cout<<"LIVE completed; published="<<published<<" checked="<<checked<<" elapsed_ms="<<GetTickCount64()-started<<"\n";
            UnmapViewOfFile(shared);CloseHandle(mapping);CloseHandle(mutex);CloseHandle(stop);ReleaseMutex(producer);CloseHandle(producer);
            std::ofstream receipt(directory/"live-passed.txt");receipt<<"published="<<published<<" checked="<<checked<<"\n";
            if(!receipt)throw std::runtime_error("Live receipt failed");return 0;
        }
        std::ofstream receipt(directory/"passed.txt");receipt<<"DXR 1.1: all three shadow masks match the CPU reference exactly.\n";
        if(!receipt) throw std::runtime_error("Could not write completion receipt");
        return 0;
    } catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}
