#pragma once

#ifdef _WIN32
  #ifdef PYPM_CAPI_EXPORTS
    #define PYPM_API __declspec(dllexport)
  #else
    #define PYPM_API __declspec(dllimport)
  #endif
#else
  #define PYPM_API
#endif

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ============================================================
   Opaque handle
   ============================================================ */

typedef struct pypm_context pypm_context_t;

/* ============================================================
   Lifecycle
   ============================================================ */

PYPM_API pypm_context_t* pypm_create(void);
PYPM_API void            pypm_destroy(pypm_context_t* ctx);

/* ============================================================
   Presets
   ============================================================ */

PYPM_API int  pypm_load_preset_file(
    pypm_context_t* ctx,
    const char* path,
    int smooth
);

PYPM_API int  pypm_load_preset_data(
    pypm_context_t* ctx,
    const char* data,
    int smooth
);

PYPM_API void pypm_reset_textures(pypm_context_t* ctx);

/* ============================================================
   Rendering
   ============================================================ */

PYPM_API void pypm_render_frame(pypm_context_t* ctx);
PYPM_API void pypm_set_window_size(pypm_context_t* ctx, size_t w, size_t h);
PYPM_API void pypm_get_window_size(pypm_context_t* ctx, size_t* w, size_t* h);

/* ============================================================
   Timing / FPS
   ============================================================ */

PYPM_API void  pypm_set_fps(pypm_context_t* ctx, int fps);
PYPM_API int   pypm_get_fps(pypm_context_t* ctx);

/* ============================================================
   Beat / transitions
   ============================================================ */

PYPM_API void  pypm_set_beat_sensitivity(pypm_context_t* ctx, float v);
PYPM_API float pypm_get_beat_sensitivity(pypm_context_t* ctx);

PYPM_API void  pypm_set_preset_duration(pypm_context_t* ctx, double v);
PYPM_API double pypm_get_preset_duration(pypm_context_t* ctx);

PYPM_API void  pypm_set_hard_cut_enabled(pypm_context_t* ctx, int enabled);
PYPM_API int   pypm_get_hard_cut_enabled(pypm_context_t* ctx);

PYPM_API void  pypm_set_hard_cut_duration(pypm_context_t* ctx, double v);
PYPM_API double pypm_get_hard_cut_duration(pypm_context_t* ctx);

PYPM_API void  pypm_set_soft_cut_duration(pypm_context_t* ctx, double v);
PYPM_API double pypm_get_soft_cut_duration(pypm_context_t* ctx);

/* ============================================================
   Mesh / aspect
   ============================================================ */

PYPM_API void pypm_set_mesh_size(pypm_context_t* ctx, size_t w, size_t h);
PYPM_API void pypm_get_mesh_size(pypm_context_t* ctx, size_t* w, size_t* h);

PYPM_API void pypm_set_aspect_correction(pypm_context_t* ctx, int enabled);
PYPM_API int  pypm_get_aspect_correction(pypm_context_t* ctx);

/* ============================================================
   Audio
   ============================================================ */

PYPM_API unsigned int pypm_pcm_get_max_samples(void);

PYPM_API void pypm_pcm_add_float(
    pypm_context_t* ctx,
    const float* samples,
    unsigned int count,
    unsigned int channels
);

PYPM_API void pypm_pcm_add_int16(
    pypm_context_t* ctx,
    const int16_t* samples,
    unsigned int count,
    unsigned int channels
);

PYPM_API void pypm_pcm_add_uint8(
    pypm_context_t* ctx,
    const uint8_t* samples,
    unsigned int count,
    unsigned int channels
);

/* ============================================================
   Version
   ============================================================ */

PYPM_API char* pypm_get_version_string(void);
PYPM_API char* pypm_get_vcs_version_string(void);

#ifdef __cplusplus
}
#endif
