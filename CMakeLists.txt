cmake_minimum_required(VERSION 3.21)

project(python_projectm_native
    LANGUAGES C CXX
)

# ============================================================
# Global options
# ============================================================

if (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "" FORCE)
endif()

set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Where final binaries should go
set(PYPM_NATIVE_BIN_DIR
    ${CMAKE_SOURCE_DIR}/python_projectm/native/bin
)

message(STATUS "Native binaries will be placed in:")
message(STATUS "  ${PYPM_NATIVE_BIN_DIR}")

# ============================================================
# libprojectM (extracted release archive)
# ============================================================

if (NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/libprojectM-4.1.6/CMakeLists.txt")
    message(FATAL_ERROR
        "Extract libprojectM-4.1.6.tar.gz into the repository root first. See README.md."
    )
endif()

add_subdirectory(libprojectM-4.1.6)

include(cmake/ProjectMFramebuffer.cmake)

if (NOT BUILD_SHARED_LIBS)
    message(FATAL_ERROR "python-projectm requires BUILD_SHARED_LIBS=ON.")
endif()

# ============================================================
# pypm_wrapper
# ============================================================

add_subdirectory(pypm_wrapper)
