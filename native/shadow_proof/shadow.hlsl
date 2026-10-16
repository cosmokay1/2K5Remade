// DXR 1.1 inline shadow rays, one opaque blocker and one point light.
RaytracingAccelerationStructure scene : register(t0);
RWStructuredBuffer<uint> shadow : register(u0);
cbuffer Settings : register(b0) {float3 light; uint instanceMask;}
[numthreads(8,8,1)]
void main(uint3 pixel : SV_DispatchThreadID) {
    if(any(pixel.xy>=256)) return;
    float3 origin=float3((pixel.x+.5)/256*8-4,.001,(pixel.y+.5)/256*8-4);
    float3 delta=light-origin;
    RayDesc ray;
    ray.Origin=origin; ray.Direction=normalize(delta);
    ray.TMin=.001; ray.TMax=length(delta)-.001;
    RayQuery<RAY_FLAG_FORCE_OPAQUE | RAY_FLAG_ACCEPT_FIRST_HIT_AND_END_SEARCH |
             RAY_FLAG_SKIP_PROCEDURAL_PRIMITIVES> query;
    query.TraceRayInline(scene,0,instanceMask,ray);
    while(query.Proceed()) {}
    shadow[pixel.y*256+pixel.x]=query.CommittedStatus()==COMMITTED_TRIANGLE_HIT ? 1 : 0;
}
