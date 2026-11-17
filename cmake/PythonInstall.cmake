# Only this component is installed into wheels; upstream SDK install rules and
# the manual wrapper SDK remain available to ordinary CMake consumers.
if(UNIX AND NOT APPLE)
    set_target_properties(projectM pypm_capi PROPERTIES INSTALL_RPATH "$ORIGIN")
endif()
install(TARGETS projectM pypm_capi
    RUNTIME DESTINATION "${PYPM_NATIVE_INSTALL_DIR}" COMPONENT python
    LIBRARY DESTINATION "${PYPM_NATIVE_INSTALL_DIR}" COMPONENT python
)
install(FILES "${CMAKE_CURRENT_SOURCE_DIR}/cmake/native_bin_init.py"
    DESTINATION "${PYPM_NATIVE_INSTALL_DIR}" RENAME __init__.py COMPONENT python)

if(WIN32)
    install(FILES $<TARGET_RUNTIME_DLLS:pypm_capi>
        DESTINATION "${PYPM_NATIVE_INSTALL_DIR}" COMPONENT python)
    if(MSVC)
        # App-local deployment: users do not need to install the VC++ redist.
        set(CMAKE_INSTALL_SYSTEM_RUNTIME_LIBS_SKIP TRUE)
        set(CMAKE_INSTALL_DEBUG_LIBRARIES FALSE)
        include(InstallRequiredSystemLibraries)
        if(SKBUILD AND NOT CMAKE_INSTALL_SYSTEM_RUNTIME_LIBS)
            message(FATAL_ERROR "The redistributable MSVC runtime was not found.")
        endif()
        install(PROGRAMS ${CMAKE_INSTALL_SYSTEM_RUNTIME_LIBS}
            DESTINATION "${PYPM_NATIVE_INSTALL_DIR}" COMPONENT python)
    endif()
endif()

configure_file("${CMAKE_CURRENT_SOURCE_DIR}/cmake/native-build.txt.in"
    "${CMAKE_CURRENT_BINARY_DIR}/native-build.txt" @ONLY)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/native-build.txt"
    DESTINATION python_projectm/native COMPONENT python)
