// Standalone, asset-free GPU correctness proof. No game hooks or software fallback.
#include "scene.h"
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
    if(argc!=3){std::cerr<<"Usage: shadow_dxr shadow.cso output-directory\n";return 1;}
    try {
        const std::filesystem::path directory=argv[2];std::filesystem::create_directories(directory);
        // A skipped/failed attempt must never leave an earlier success receipt.
        std::filesystem::remove(directory/"passed.txt");
        Gpu gpu;
        if(!gpu.open()){std::cout<<"UNSUPPORTED: no hardware adapter exposes DXR 1.1 + Shader Model 6.5. GPU proof NOT run.\n";return 77;}
        std::ifstream shader_file(argv[1],std::ios::binary);
        const std::vector<char> shader((std::istreambuf_iterator<char>(shader_file)),{});
        if(shader.empty()) throw std::runtime_error("Missing compiled DXR compute shader");
        auto mesh=gpu.upload(vertices.data(),sizeof(vertices));
        D3D12_RAYTRACING_GEOMETRY_DESC geometry{};geometry.Type=D3D12_RAYTRACING_GEOMETRY_TYPE_TRIANGLES;
        geometry.Flags=D3D12_RAYTRACING_GEOMETRY_FLAG_OPAQUE;
        geometry.Triangles.VertexBuffer={mesh->GetGPUVirtualAddress(),sizeof(Vec)};
        geometry.Triangles.VertexCount=static_cast<UINT>(vertices.size());geometry.Triangles.VertexFormat=DXGI_FORMAT_R32G32B32_FLOAT;
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
        for(unsigned test=0;test<3;++test) {
            gpu.commands->SetPipelineState(state.Get());gpu.commands->SetComputeRootSignature(root.Get());
            gpu.commands->SetComputeRootShaderResourceView(0,tlas->GetGPUVirtualAddress());
            gpu.commands->SetComputeRootUnorderedAccessView(1,output->GetGPUVirtualAddress());
            gpu.commands->SetComputeRoot32BitConstants(2,4,&cases[test],0);
            gpu.commands->Dispatch(size/8,size/8,1);
            gpu.transition(output.Get(),D3D12_RESOURCE_STATE_UNORDERED_ACCESS,D3D12_RESOURCE_STATE_COPY_SOURCE);
            gpu.commands->CopyResource(readback.Get(),output.Get());
            gpu.transition(output.Get(),D3D12_RESOURCE_STATE_COPY_SOURCE,D3D12_RESOURCE_STATE_UNORDERED_ACCESS);
            gpu.finish();
            void* mapped=nullptr;D3D12_RANGE range{0,bytes};check(readback->Map(0,&range,&mapped),"Readback map");
            std::vector<uint32_t> actual(size*size);std::memcpy(actual.data(),mapped,bytes);
            D3D12_RANGE no_write{0,0};readback->Unmap(0,&no_write);
            const auto expected=reference(cases[test].light,cases[test].mask!=0);
            image(directory/(std::string("gpu-")+names[test]+".ppm"),actual);
            unsigned mismatches=0;for(size_t pixel=0;pixel<actual.size();++pixel) mismatches+=actual[pixel]!=expected[pixel];
            std::cout<<names[test]<<": "<<mismatches<<" mismatched pixels of "<<actual.size()<<"\n";
            if(mismatches) throw std::runtime_error("GPU/reference disagreement; proof failed");
        }
        std::ofstream receipt(directory/"passed.txt");receipt<<"DXR 1.1: all three shadow masks match the CPU reference exactly.\n";
        if(!receipt) throw std::runtime_error("Could not write completion receipt");
        return 0;
    } catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}
