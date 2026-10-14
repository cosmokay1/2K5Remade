cmake_minimum_required(VERSION 3.20)
project(FranchiseBridgeCheck LANGUAGES C CXX)
# Exact public release header; license notice retained in docs/third-party.
file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/include/nlohmann")
file(DOWNLOAD
  "https://github.com/nlohmann/json/releases/download/v3.12.0/json.hpp"
  "${CMAKE_BINARY_DIR}/include/nlohmann/json.hpp"
  EXPECTED_HASH SHA256=aaf127c04cb31c406e5b04a63f1ae89369fccde6d8fa7cdda1ed4f32dfc5de63
  TLS_VERIFY ON TIMEOUT 45)
add_library(franchise_protocol INTERFACE)
target_include_directories(franchise_protocol INTERFACE "${CMAKE_BINARY_DIR}/include" "${CMAKE_CURRENT_SOURCE_DIR}")
target_compile_features(franchise_protocol INTERFACE cxx_std_17)
add_executable(franchise_protocol_check protocol_check.cpp)
target_link_libraries(franchise_protocol_check PRIVATE franchise_protocol)
enable_testing()
add_test(NAME protocol_boundary COMMAND franchise_protocol_check)
if(WIN32)
  add_library(franchise_host_client STATIC host_client.cpp)
  target_link_libraries(franchise_host_client PUBLIC franchise_protocol)
  target_compile_definitions(franchise_host_client PRIVATE WIN32_LEAN_AND_MEAN NOMINMAX)
  add_executable(franchise_c_host_check c_host_smoke.c)
  target_link_libraries(franchise_c_host_check PRIVATE franchise_host_client)
  target_compile_definitions(franchise_c_host_check PRIVATE WIN32_LEAN_AND_MEAN NOMINMAX)
  set_target_properties(franchise_c_host_check PROPERTIES C_STANDARD 11)
  add_executable(franchise_bridge_check smoke.cpp)
  target_link_libraries(franchise_bridge_check PRIVATE franchise_protocol)
  target_compile_definitions(franchise_bridge_check PRIVATE WIN32_LEAN_AND_MEAN NOMINMAX)
endif()
