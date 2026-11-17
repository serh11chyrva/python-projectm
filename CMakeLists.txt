cmake_minimum_required(VERSION 3.21)

# projectM's generated version header uses the top-level CMake project version.
project(python_projectm_native
    VERSION 4.1.6
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
set(PYPM_NATIVE_BIN_DIR "${CMAKE_SOURCE_DIR}/python_projectm/native/bin"
    CACHE PATH "Runtime output directory for manual development builds")
if(SKBUILD)
    set(_pypm_copy_default OFF)
else()
    set(_pypm_copy_default ON)
endif()
option(PYPM_COPY_NATIVE_TO_SOURCE "Copy development libraries into the checkout" ${_pypm_copy_default})
set(PYPM_NATIVE_INSTALL_DIR "python_projectm/native/bin")

# Disable unused upstream components for both manual and PEP 517 builds.
option(BUILD_SHARED_LIBS "Build shared native libraries" ON)
option(ENABLE_SYSTEM_GLM "Use system GLM" OFF)
option(ENABLE_SYSTEM_PROJECTM_EVAL "Use system projectM-eval" OFF)
option(ENABLE_PLAYLIST "Build the upstream playlist library" OFF)
option(ENABLE_SDL_UI "Build the upstream SDL application" OFF)
option(BUILD_TESTING "Build upstream native tests" OFF)
# Use the parser sources distributed in the release, without rewriting vendor files.
set(CMAKE_DISABLE_FIND_PACKAGE_BISON TRUE)
set(CMAKE_DISABLE_FIND_PACKAGE_FLEX TRUE)

if(PYPM_COPY_NATIVE_TO_SOURCE)
    message(STATUS "Development runtime copy: ${PYPM_NATIVE_BIN_DIR}")
else()
    message(STATUS "Python runtime install destination: ${PYPM_NATIVE_INSTALL_DIR}")
endif()

# ============================================================
# libprojectM (extracted release archive)
# ============================================================

include(cmake/ProjectMSources.cmake)
add_subdirectory("${PYPM_PROJECTM_SOURCE_DIR}" "${CMAKE_CURRENT_BINARY_DIR}/projectm")

include(cmake/ProjectMFramebuffer.cmake)

if (NOT BUILD_SHARED_LIBS)
    message(FATAL_ERROR "python-projectm requires BUILD_SHARED_LIBS=ON.")
endif()

# ============================================================
# pypm_wrapper
# ============================================================

add_subdirectory(pypm_wrapper)

include(cmake/PythonInstall.cmake)
