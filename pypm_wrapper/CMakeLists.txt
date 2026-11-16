cmake_minimum_required(VERSION 3.20)

project(pypm_capi
    VERSION 1.0.0
    LANGUAGES C CXX
)

# ------------------------------------------------------------
# Build type
# ------------------------------------------------------------

if (NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "" FORCE)
endif()

# ------------------------------------------------------------
# Library target
# ------------------------------------------------------------

add_library(pypm_capi SHARED
    src/pypm_capi.cpp
    include/pypm_capi.h
)

# ------------------------------------------------------------
# C / C++ standard
# ------------------------------------------------------------

set_target_properties(pypm_capi PROPERTIES
    C_STANDARD 11
    CXX_STANDARD 17
    CXX_STANDARD_REQUIRED YES
)

# ------------------------------------------------------------
# Include directories
# ------------------------------------------------------------

target_include_directories(pypm_capi
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include

        # projectM public C API headers
        ${CMAKE_CURRENT_SOURCE_DIR}/../libprojectM-4.1.6/src/api/include

        # generated headers (projectM_export.h, etc.)
        ${CMAKE_CURRENT_SOURCE_DIR}/../libprojectM-4.1.6/build/src/api/include
)

# ------------------------------------------------------------
# Link projectM import library
# ------------------------------------------------------------

target_link_libraries(pypm_capi
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/../libprojectM-4.1.6/build/src/libprojectM/Release/projectM-4.lib
)

# ------------------------------------------------------------
# Windows specifics
# ------------------------------------------------------------

if (WIN32)
    target_compile_definitions(pypm_capi
        PRIVATE
            PYPM_CAPI_EXPORTS
            WIN32_LEAN_AND_MEAN
            NOMINMAX
    )

    # Avoid MSVC CRT warnings when used from Python
    target_compile_definitions(pypm_capi
        PRIVATE
            _CRT_SECURE_NO_WARNINGS
    )
endif()

# ------------------------------------------------------------
# Output naming
# ------------------------------------------------------------

set_target_properties(pypm_capi PROPERTIES
    OUTPUT_NAME "pypm_capi"
    PREFIX ""
)

# ------------------------------------------------------------
# Install (optional, but nice)
# ------------------------------------------------------------

install(TARGETS pypm_capi
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(FILES include/pypm_capi.h
    DESTINATION include
)
