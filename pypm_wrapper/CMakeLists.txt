cmake_minimum_required(VERSION 3.21)

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
)

# ------------------------------------------------------------
# Link projectM and inherit its public and generated headers
# ------------------------------------------------------------

target_link_libraries(pypm_capi
    PRIVATE
        libprojectM::projectM
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
)

if(WIN32)
    set_target_properties(pypm_capi PROPERTIES PREFIX "")
elseif(UNIX AND NOT APPLE)
    set_target_properties(pypm_capi PROPERTIES BUILD_RPATH "$ORIGIN")
elseif(APPLE)
    set_target_properties(pypm_capi PROPERTIES BUILD_RPATH "@loader_path")
endif()

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

if(NOT WIN32)
    add_custom_command(TARGET pypm_capi POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E make_directory "${PYPM_NATIVE_BIN_DIR}"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "$<TARGET_FILE:projectM>" "${PYPM_NATIVE_BIN_DIR}"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "$<TARGET_SONAME_FILE:projectM>" "${PYPM_NATIVE_BIN_DIR}"
        VERBATIM
    )
endif()

# POST_BUILD commands must be declared in the directory that owns the target.
add_custom_command(TARGET pypm_capi POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory "${PYPM_NATIVE_BIN_DIR}"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "$<TARGET_FILE:pypm_capi>" "${PYPM_NATIVE_BIN_DIR}"
    VERBATIM
)

if (WIN32)
    # Includes projectM and its transitive DLL dependencies (such as GLEW).
    add_custom_command(TARGET pypm_capi POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            $<TARGET_RUNTIME_DLLS:pypm_capi> "${PYPM_NATIVE_BIN_DIR}"
        COMMAND_EXPAND_LISTS
        VERBATIM
    )
endif()
