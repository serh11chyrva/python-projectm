#include "pypm_capi.h"

#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include <projectM-4/core.h>
#include <projectM-4/render_opengl.h>
#include <projectM-4/audio.h>
#include <projectM-4/parameters.h>

#include <stdlib.h>

/* ============================================================
   Context
   ============================================================ */

struct pypm_context {
    projectm_handle pm;
};

/* ============================================================
   Lifecycle
   ============================================================ */

pypm_context_t* pypm_create(void)
{
    pypm_context_t* ctx = (pypm_context_t*)malloc(sizeof(pypm_context_t));
    if (!ctx)
        return NULL;

    ctx->pm = projectm_create();
    if (!ctx->pm) {
        free(ctx);
        return NULL;
    }
    return ctx;
}

void pypm_destroy(pypm_context_t* ctx)
{
    if (!ctx) return;
    if (ctx->pm) projectm_destroy(ctx->pm);
    free(ctx);
}

/* ============================================================
   Presets
   ============================================================ */

int pypm_load_preset_file(pypm_context_t* ctx, const char* p, int s)
{
    if (!ctx || !ctx->pm || !p) return 0;
    projectm_load_preset_file(ctx->pm, p, s != 0);
    return 1;
}

int pypm_load_preset_data(pypm_context_t* ctx, const char* d, int s)
{
    if (!ctx || !ctx->pm || !d) return 0;
    projectm_load_preset_data(ctx->pm, d, s != 0);
    return 1;
}

void pypm_reset_textures(pypm_context_t* ctx)
{
    if (ctx && ctx->pm)
        projectm_reset_textures(ctx->pm);
}

/* ============================================================
   Rendering
   ============================================================ */

void pypm_render_frame(pypm_context_t* ctx)
{
    if (ctx && ctx->pm)
        projectm_opengl_render_frame(ctx->pm);
}

void pypm_set_window_size(pypm_context_t* ctx, size_t w, size_t h)
{
    if (ctx && ctx->pm)
        projectm_set_window_size(ctx->pm, w, h);
}

void pypm_get_window_size(pypm_context_t* ctx, size_t* w, size_t* h)
{
    if (ctx && ctx->pm)
        projectm_get_window_size(ctx->pm, w, h);
}

/* ============================================================
   FPS / timing
   ============================================================ */

void pypm_set_fps(pypm_context_t* ctx, int fps)
{
    if (ctx && ctx->pm)
        projectm_set_fps(ctx->pm, fps);
}

int pypm_get_fps(pypm_context_t* ctx)
{
    return (ctx && ctx->pm) ? projectm_get_fps(ctx->pm) : 0;
}

/* ============================================================
   Beat / transitions
   ============================================================ */

#define PROXY_SETGET(name, type) \
void pypm_set_##name(pypm_context_t* c, type v){ if(c&&c->pm) projectm_set_##name(c->pm,v);} \
type pypm_get_##name(pypm_context_t* c){ return (c&&c->pm)?projectm_get_##name(c->pm):0; }

PROXY_SETGET(beat_sensitivity, float)
PROXY_SETGET(preset_duration, double)
PROXY_SETGET(hard_cut_duration, double)
PROXY_SETGET(soft_cut_duration, double)

void pypm_set_hard_cut_enabled(pypm_context_t* c, int e)
{
    if (c && c->pm) projectm_set_hard_cut_enabled(c->pm, e != 0);
}
int pypm_get_hard_cut_enabled(pypm_context_t* c)
{
    return (c && c->pm) ? projectm_get_hard_cut_enabled(c->pm) : 0;
}

/* ============================================================
   Mesh / aspect
   ============================================================ */

void pypm_set_mesh_size(pypm_context_t* c, size_t w, size_t h)
{
    if (c && c->pm) projectm_set_mesh_size(c->pm, w, h);
}

void pypm_get_mesh_size(pypm_context_t* c, size_t* w, size_t* h)
{
    if (c && c->pm) projectm_get_mesh_size(c->pm, w, h);
}

void pypm_set_aspect_correction(pypm_context_t* c, int e)
{
    if (c && c->pm) projectm_set_aspect_correction(c->pm, e != 0);
}
int pypm_get_aspect_correction(pypm_context_t* c)
{
    return (c && c->pm) ? projectm_get_aspect_correction(c->pm) : 0;
}

/* ============================================================
   Audio
   ============================================================ */

unsigned int pypm_pcm_get_max_samples(void)
{
    return projectm_pcm_get_max_samples();
}

void pypm_pcm_add_float(pypm_context_t* c, const float* s, unsigned int n, unsigned int ch)
{
    if (c && c->pm) projectm_pcm_add_float(c->pm, s, n, (projectm_channels)ch);
}

void pypm_pcm_add_int16(pypm_context_t* c, const int16_t* s, unsigned int n, unsigned int ch)
{
    if (c && c->pm) projectm_pcm_add_int16(c->pm, s, n, (projectm_channels)ch);
}

void pypm_pcm_add_uint8(pypm_context_t* c, const uint8_t* s, unsigned int n, unsigned int ch)
{
    if (c && c->pm) projectm_pcm_add_uint8(c->pm, s, n, (projectm_channels)ch);
}

/* ============================================================
   Version
   ============================================================ */

char* pypm_get_version_string(void)
{
    return projectm_get_version_string();
}

char* pypm_get_vcs_version_string(void)
{
    return projectm_get_vcs_version_string();
}
