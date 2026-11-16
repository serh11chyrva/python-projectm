#include "pypm_capi.h"

#if defined(_WIN32)
#include <GL/glew.h>
#elif defined(__APPLE__)
#include <OpenGL/gl3.h>
#else
#define GL_GLEXT_PROTOTYPES
#include <GL/gl.h>
#include <GL/glext.h>
#endif

#include <projectM-4/audio.h>
#include <projectM-4/callbacks.h>
#include <projectM-4/core.h>
#include <projectM-4/memory.h>
#include <projectM-4/parameters.h>
#include <projectM-4/render_opengl.h>

#include <cstdio>
#include <exception>
#include <memory>
#include <stdexcept>

struct pypm_context {
    projectm_handle pm = nullptr;
    bool preset_failed = false;
};

namespace {
// A fixed buffer also permits reporting allocation failures without allocating.
thread_local char last_error[2048] = {};

void set_error(const char* message) noexcept
{
    std::snprintf(last_error, sizeof(last_error), "%s", message ? message : "Unknown projectM error");
}

template<typename Function, typename Result>
Result guarded(Function function, Result fallback) noexcept
{
    last_error[0] = '\0';
    try {
        return function();
    } catch (const std::exception& error) {
        set_error(error.what());
    } catch (...) {
        set_error("Unknown native exception");
    }
    return fallback;
}

template<typename Function>
void invoke(pypm_context_t* ctx, Function function) noexcept
{
    guarded([&]() {
        if (!ctx || !ctx->pm)
            throw std::invalid_argument("Invalid projectM context");
        function(ctx->pm);
        return 1;
    }, 0);
}

void preset_failed(const char*, const char* message, void* user_data) noexcept
{
    static_cast<pypm_context_t*>(user_data)->preset_failed = true;
    set_error(message);
}

template<typename Sample, typename Function>
void add_pcm(pypm_context_t* ctx, const Sample* samples, unsigned int count,
             unsigned int channels, Function function) noexcept
{
    invoke(ctx, [&](projectm_handle pm) {
        if ((channels != 1 && channels != 2) || (count && !samples))
            throw std::invalid_argument("PCM requires a valid mono or interleaved stereo buffer");
        if (count > projectm_pcm_get_max_samples())
            throw std::invalid_argument("PCM block exceeds the native sample limit");
        if (count)
            function(pm, samples, count, static_cast<projectm_channels>(channels));
    });
}
} // namespace

const char* pypm_get_last_error(void)
{
    return last_error;
}

void pypm_clear_error(void)
{
    last_error[0] = '\0';
}

pypm_context_t* pypm_create(void)
{
    return guarded([]() -> pypm_context_t* {
        if (!glGetString(GL_VERSION))
            throw std::runtime_error("An OpenGL context must be current before creating projectM");
#if defined(_WIN32)
        glewExperimental = GL_TRUE;
        const auto status = glewInit();
        if (status != GLEW_OK)
            throw std::runtime_error(reinterpret_cast<const char*>(glewGetErrorString(status)));
        // GLEW can leave GL_INVALID_ENUM in core-profile contexts.
        while (glGetError() != GL_NO_ERROR) {}
#endif
        auto ctx = std::make_unique<pypm_context_t>();
        ctx->pm = projectm_create();
        if (!ctx->pm)
            throw std::runtime_error("projectM initialization failed; OpenGL 3.3 or newer is required");
        projectm_set_preset_switch_failed_event_callback(ctx->pm, preset_failed, ctx.get());
        return ctx.release();
    }, static_cast<pypm_context_t*>(nullptr));
}

void pypm_destroy(pypm_context_t* ctx)
{
    guarded([&]() {
        if (ctx) {
            if (ctx->pm)
                projectm_destroy(ctx->pm);
            delete ctx;
        }
        return 1;
    }, 0);
}

int pypm_load_preset_file(pypm_context_t* ctx, const char* path, int smooth)
{
    return guarded([&]() {
        if (!ctx || !ctx->pm || !path)
            throw std::invalid_argument("Invalid context or preset path");
        ctx->preset_failed = false;
        projectm_load_preset_file(ctx->pm, path, smooth != 0);
        return ctx->preset_failed ? 0 : 1;
    }, 0);
}

int pypm_load_preset_data(pypm_context_t* ctx, const char* data, int smooth)
{
    return guarded([&]() {
        if (!ctx || !ctx->pm || !data)
            throw std::invalid_argument("Invalid context or preset data");
        ctx->preset_failed = false;
        projectm_load_preset_data(ctx->pm, data, smooth != 0);
        return ctx->preset_failed ? 0 : 1;
    }, 0);
}

void pypm_reset_textures(pypm_context_t* ctx)
{
    invoke(ctx, projectm_reset_textures);
}

void pypm_render_frame(pypm_context_t* ctx)
{
    invoke(ctx, [](projectm_handle pm) {
        if (glCheckFramebufferStatus(GL_DRAW_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE)
            throw std::runtime_error("The draw framebuffer is incomplete");
        projectm_opengl_render_frame(pm);
    });
}

void pypm_render_frame_to_fbo(pypm_context_t* ctx, unsigned int framebuffer)
{
    if (!ctx || !ctx->pm) {
        set_error("Invalid projectM context");
        return;
    }
    if (framebuffer && !glIsFramebuffer(framebuffer)) {
        set_error("The requested framebuffer does not exist in the current context");
        return;
    }
    GLint previous = 0;
    glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING, &previous);
    glBindFramebuffer(GL_DRAW_FRAMEBUFFER, framebuffer);
    pypm_render_frame(ctx);
    glBindFramebuffer(GL_DRAW_FRAMEBUFFER, static_cast<GLuint>(previous));
}

void pypm_set_window_size(pypm_context_t* ctx, size_t width, size_t height)
{
    invoke(ctx, [&](projectm_handle pm) { projectm_set_window_size(pm, width, height); });
}

void pypm_get_window_size(pypm_context_t* ctx, size_t* width, size_t* height)
{
    invoke(ctx, [&](projectm_handle pm) {
        if (!width || !height)
            throw std::invalid_argument("Window size output pointers must not be null");
        projectm_get_window_size(pm, width, height);
    });
}

#define PROXY_SETGET(name, type) \
void pypm_set_##name(pypm_context_t* ctx, type value) { \
    invoke(ctx, [&](projectm_handle pm) { projectm_set_##name(pm, value); }); \
} \
type pypm_get_##name(pypm_context_t* ctx) { \
    type result = {}; \
    invoke(ctx, [&](projectm_handle pm) { result = projectm_get_##name(pm); }); \
    return result; \
}

PROXY_SETGET(fps, int)
PROXY_SETGET(beat_sensitivity, float)
PROXY_SETGET(preset_duration, double)
PROXY_SETGET(hard_cut_duration, double)
PROXY_SETGET(soft_cut_duration, double)
PROXY_SETGET(hard_cut_sensitivity, float)
PROXY_SETGET(easter_egg, float)

#define PROXY_BOOL(name) \
void pypm_set_##name(pypm_context_t* ctx, int value) { \
    invoke(ctx, [&](projectm_handle pm) { projectm_set_##name(pm, value != 0); }); \
} \
int pypm_get_##name(pypm_context_t* ctx) { \
    int result = 0; \
    invoke(ctx, [&](projectm_handle pm) { result = projectm_get_##name(pm) ? 1 : 0; }); \
    return result; \
}

PROXY_BOOL(hard_cut_enabled)
PROXY_BOOL(aspect_correction)
PROXY_BOOL(preset_locked)

void pypm_set_mesh_size(pypm_context_t* ctx, size_t width, size_t height)
{
    invoke(ctx, [&](projectm_handle pm) { projectm_set_mesh_size(pm, width, height); });
}

void pypm_get_mesh_size(pypm_context_t* ctx, size_t* width, size_t* height)
{
    invoke(ctx, [&](projectm_handle pm) {
        if (!width || !height)
            throw std::invalid_argument("Mesh size output pointers must not be null");
        projectm_get_mesh_size(pm, width, height);
    });
}

void pypm_set_texture_search_paths(pypm_context_t* ctx, const char** paths, size_t count)
{
    invoke(ctx, [&](projectm_handle pm) {
        if (count && !paths)
            throw std::invalid_argument("Texture paths must not be null");
        for (size_t index = 0; index < count; ++index) {
            if (!paths[index])
                throw std::invalid_argument("A texture path must not be null");
        }
        projectm_set_texture_search_paths(pm, paths, count);
    });
}

unsigned int pypm_pcm_get_max_samples(void)
{
    return guarded([]() { return projectm_pcm_get_max_samples(); }, 0u);
}

void pypm_pcm_add_float(pypm_context_t* ctx, const float* samples, unsigned int count, unsigned int channels)
{
    add_pcm(ctx, samples, count, channels, projectm_pcm_add_float);
}

void pypm_pcm_add_int16(pypm_context_t* ctx, const int16_t* samples, unsigned int count, unsigned int channels)
{
    add_pcm(ctx, samples, count, channels, projectm_pcm_add_int16);
}

void pypm_pcm_add_uint8(pypm_context_t* ctx, const uint8_t* samples, unsigned int count, unsigned int channels)
{
    add_pcm(ctx, samples, count, channels, projectm_pcm_add_uint8);
}

char* pypm_get_version_string(void)
{
    return guarded([]() { return projectm_get_version_string(); }, static_cast<char*>(nullptr));
}

char* pypm_get_vcs_version_string(void)
{
    return guarded([]() { return projectm_get_vcs_version_string(); }, static_cast<char*>(nullptr));
}

void pypm_free_string(const char* value)
{
    projectm_free_string(value);
}
