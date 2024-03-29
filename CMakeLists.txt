
cmake_minimum_required(VERSION 3.2)
message(STATUS "Cmake version ${CMAKE_MAJOR_VERSION}.${CMAKE_MINOR_VERSION}.${CMAKE_PATCH_VERSION}")

project(insitu-ensemble-simulator)

add_definitions("-Wall -Wno-unused-variable -Wno-unused-private-field")

set(CMAKE_CXX_STANDARD 17)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/CMakeModules/")

# Find WRENCH, SimGrid, and Boost
find_package(WRENCH REQUIRED)
find_package(SimGrid REQUIRED)
find_package(Boost REQUIRED)
find_package(YAMLCPP REQUIRED)

# include directories
include_directories(include/ /usr/local/include/ /opt/local/include/ ${WRENCH_INCLUDE_DIR} ${SimGrid_INCLUDE_DIR} ${Boost_INCLUDE_DIR} ${YAMLCPP_INCLUDE_DIR})

# source files
set(SOURCE_FILES
        include/Controller.h
        src/Controller.cpp
        src/Simulator.cpp
        )

# generating the executable
add_executable(insitu-ensemble-simulator ${SOURCE_FILES})

# PugiXML, needed if using the WRENCH_WFCOMMONS_WORKFLOW_PARSER_LIBRARY
#find_library(PUGIXML_LIBRARY NAMES pugixml)

# Specify libraries to link
if (ENABLE_BATSCHED)
    target_link_libraries(insitu-ensemble-simulator
            ${WRENCH_LIBRARY}
            ${SimGrid_LIBRARY}
            ${Boost_LIBRARIES}
            ${YAMLCPP_LIBRARY}
#            ${WRENCH_WFCOMMONS_WORKFLOW_PARSER_LIBRARY}
#            ${PUGIXML_LIBRARY}
            -lzmq)
else()
    target_link_libraries(insitu-ensemble-simulator
            ${WRENCH_LIBRARY}
            ${SimGrid_LIBRARY}
            ${Boost_LIBRARIES}
            ${YAMLCPP_LIBRARY}
#            ${WRENCH_WFCOMMONS_WORKFLOW_PARSER_LIBRARY}
#            ${PUGIXML_LIBRARY}
            )
endif()

install(TARGETS insitu-ensemble-simulator DESTINATION bin)
