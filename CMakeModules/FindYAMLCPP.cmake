
# CMake find module to search for the WRENCH library.

# Copyright (c) 2022. The WRENCH Team.
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the license (GNU LGPL) which comes with this package.

#
# USERS OF PROGRAMS USING WRENCH
# -------------------------------
#
# If cmake does not find this file, add its path to CMAKE_PREFIX_PATH:
#    CMAKE_PREFIX_PATH="/path/to/FindWRENCH.cmake:$CMAKE_PREFIX_PATH"  cmake .
#
# If this file does not find WRENCH, define WRENCH_PATH:
#    WRENCH_PATH=/path/to/wrench cmake .

#
# DEVELOPERS OF PROGRAMS USING WRENCH
# ------------------------------------
#
#  1. Include this file in your own CMakeLists.txt (before defining any target)
#     by copying it in your development tree. 
#
#  2. Afterward, if you have CMake >= 2.8.12, this will define a
#     target called 'WRENCH::WRENCH'. Use it as:
#       target_link_libraries(your-simulator WRENCH::WRENCH)
#
#    With older CMake (< 2.8.12), it simply defines several variables:
#       WRENCH_INCLUDE_DIR - the WRENCH include directories
#       WRENCH_LIBRARY - link your simulator against it to use WRENCH
#    Use as:
#      include_directories("${WRENCH_INCLUDE_DIR}" SYSTEM)
#      target_link_libraries(your-simulator ${WRENCH_LIBRARY})
#
#  Since WRENCH header files require C++14, so we set CMAKE_CXX_STANDARD to 14.
#    Change this variable in your own file if you need a later standard.

cmake_minimum_required(VERSION 2.8.12)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_path(YAMLCPP_INCLUDE_DIR
        NAMES yaml-cpp/yaml.h
        PATHS ${YAMLCPP_PATH}/include /opt/wrench/include
        )

find_library(YAMLCPP_LIBRARY
        NAMES yaml-cpp
        PATHS ${WRENCH_PATH}/lib64 /opt/wrench/lib64
        )


mark_as_advanced(YAMLCPP_INCLUDE_DIR)
mark_as_advanced(YAMLCPP_LIBRARY)


include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(YAMLCPP
        FOUND_VAR YAMLCPP_FOUND
        REQUIRED_VARS YAMLCPP_INCLUDE_DIR YAMLCPP_LIBRARY
        VERSION_VAR YAMLCPP_VERSION
        REASON_FAILURE_MESSAGE "The YAMLCPP package could not be located. If you installed YAMLCPP in a non-standard location, pass -DYAMLCPP_PATH=<path to location> to cmake (e.g., cmake -DYAMLCPP_PATH=/opt/somewhere/)"
        FAIL_MESSAGE "Could not find the YAMLCPP installation"
        )


if (YAMLCPP_FOUND AND NOT CMAKE_VERSION VERSION_LESS 2.8.12)

    add_library(YAMLCPP::YAMLCPP SHARED IMPORTED)
    set_target_properties(YAMLCPP::YAMLCPP PROPERTIES
            INTERFACE_SYSTEM_INCLUDE_DIRECTORIES ${YAMLCPP_INCLUDE_DIR}
            INTERFACE_COMPILE_FEATURES cxx_alias_templates
            IMPORTED_LOCATION ${YAMLCPP_LIBRARY}
            )
endif ()

