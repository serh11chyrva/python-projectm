# projectM 4.1.6 always binds framebuffer zero before its final composition pass.
# Compile a copy that remembers the caller's draw framebuffer instead. This keeps
# the upstream checkout and the public projectM C/C++ interfaces unchanged.
set(_pypm_projectm_source
    "${PYPM_PROJECTM_SOURCE_DIR}/src/libprojectM/ProjectM.cpp")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${_pypm_projectm_source}")
file(READ "${_pypm_projectm_source}" _pypm_projectm_code)
string(REPLACE "\r\n" "\n" _pypm_projectm_code "${_pypm_projectm_code}")
set(_pypm_render_signature "void ProjectM::RenderFrame()\n{")
set(_pypm_bind_default "glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0);")
string(FIND "${_pypm_projectm_code}" "${_pypm_render_signature}" _pypm_signature_position)
string(FIND "${_pypm_projectm_code}" "${_pypm_bind_default}" _pypm_bind_position)
if(_pypm_signature_position EQUAL -1 OR _pypm_bind_position EQUAL -1)
    message(FATAL_ERROR "Unexpected projectM source; cannot apply framebuffer support for 4.1.6.")
endif()
string(REPLACE "${_pypm_render_signature}"
    "${_pypm_render_signature}\n    GLint pypmTargetFramebuffer = 0;\n    glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING, &pypmTargetFramebuffer);"
    _pypm_projectm_code "${_pypm_projectm_code}")
string(REPLACE "${_pypm_bind_default}"
    "glBindFramebuffer(GL_DRAW_FRAMEBUFFER, static_cast<GLuint>(pypmTargetFramebuffer));"
    _pypm_projectm_code "${_pypm_projectm_code}")
set(_pypm_generated_dir "${CMAKE_CURRENT_BINARY_DIR}/pypm_projectm")
file(MAKE_DIRECTORY "${_pypm_generated_dir}")
# A prominent modification notice accompanies the generated LGPL source copy.
string(PREPEND _pypm_projectm_code
    "// Modified by python-projectm on 2026-11-17: preserve the caller's draw framebuffer.\n")
file(CONFIGURE OUTPUT "${_pypm_generated_dir}/ProjectM.cpp"
    CONTENT "${_pypm_projectm_code}" @ONLY)
get_target_property(_pypm_projectm_sources projectM_main SOURCES)
list(REMOVE_ITEM _pypm_projectm_sources ProjectM.cpp "${_pypm_projectm_source}")
set_property(TARGET projectM_main PROPERTY SOURCES "${_pypm_projectm_sources}")
target_sources(projectM_main PRIVATE "${_pypm_generated_dir}/ProjectM.cpp")
if(NOT ENABLE_CXX_INTERFACE)
    set_source_files_properties("${_pypm_generated_dir}/ProjectM.cpp"
        TARGET_DIRECTORY projectM_main PROPERTIES
        COMPILE_DEFINITIONS PROJECTM_STATIC_DEFINE)
endif()
