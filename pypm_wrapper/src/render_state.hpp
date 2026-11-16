#pragma once

#include <array>
#include <vector>

namespace pypm_detail {

// Limits and scratch storage belong to one instance and its original GL context.
// Preserve all combined texture units: preset descriptors can bind units even
// when a shader optimizer removes the corresponding sampler uniforms.
class RenderState {
public:
    RenderState()
    {
        m_fragmentTextureUnits = get(GL_MAX_TEXTURE_IMAGE_UNITS);
        m_textures.resize(get(GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS));
        m_clipEnabled.resize(get(GL_MAX_CLIP_DISTANCES));
        m_drawBuffers.resize(get(GL_MAX_DRAW_BUFFERS));
        m_indexedBlend = get(GL_MAJOR_VERSION) >= 4;
    }

    void save()
    {
        m_draw = get(GL_DRAW_FRAMEBUFFER_BINDING);
        m_read = get(GL_READ_FRAMEBUFFER_BINDING);
        m_readBuffer = get(GL_READ_BUFFER);
        glGetIntegerv(GL_VIEWPORT, m_viewport.data());
        glGetIntegerv(GL_SCISSOR_BOX, m_scissor.data());
        m_program = get(GL_CURRENT_PROGRAM);
        m_vao = get(GL_VERTEX_ARRAY_BINDING);
        m_arrayBuffer = get(GL_ARRAY_BUFFER_BINDING);
        m_renderbuffer = get(GL_RENDERBUFFER_BINDING);
        m_packBuffer = get(GL_PIXEL_PACK_BUFFER_BINDING);
        m_unpackBuffer = get(GL_PIXEL_UNPACK_BUFFER_BINDING);
        m_activeTexture = get(GL_ACTIVE_TEXTURE);
        for (size_t index = 0; index < capabilities.size(); ++index)
            m_enabled[index] = glIsEnabled(capabilities[index]);
        for (size_t index = 0; index < m_clipEnabled.size(); ++index)
            m_clipEnabled[index] = glIsEnabled(GL_CLIP_DISTANCE0 + static_cast<GLenum>(index));
        for (size_t index = 0; index < blendParameters.size(); ++index)
            m_blend[index] = get(blendParameters[index]);
        for (GLuint index = 0; index < m_drawBuffers.size(); ++index) {
            auto& state = m_drawBuffers[index];
            state.blend = glIsEnabledi(GL_BLEND, index);
            glGetBooleani_v(GL_COLOR_WRITEMASK, index, state.mask.data());
            if (m_indexedBlend) {
                for (size_t parameter = 0; parameter < blendParameters.size(); ++parameter)
                    glGetIntegeri_v(blendParameters[parameter], index, &state.function[parameter]);
            }
        }
        glGetFloatv(GL_COLOR_CLEAR_VALUE, m_clearColor.data());
        glGetFloatv(GL_LINE_WIDTH, &m_lineWidth);
        glGetBooleanv(GL_DEPTH_WRITEMASK, &m_depthMask);
        std::array<GLint, 2> polygonMode{};
        glGetIntegerv(GL_POLYGON_MODE, polygonMode.data());
        m_polygonMode = polygonMode[0];
        for (size_t index = 0; index < pixelParameters.size(); ++index)
            m_pixelStore[index] = get(pixelParameters[index]);
        for (GLuint unit = 0; unit < m_textures.size(); ++unit) {
            glActiveTexture(GL_TEXTURE0 + unit);
            m_textures[unit] = {get(GL_TEXTURE_BINDING_2D), get(GL_TEXTURE_BINDING_3D), get(GL_SAMPLER_BINDING)};
        }
        glActiveTexture(m_activeTexture);
    }

    void prepare() const
    {
        for (const auto capability : resetCapabilities)
            glDisable(capability);
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE);
        glDepthMask(GL_FALSE);
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
        glBlendEquationSeparate(GL_FUNC_ADD, GL_FUNC_ADD);
        for (GLuint index = 0; index < m_clipEnabled.size(); ++index)
            glDisable(GL_CLIP_DISTANCE0 + index);
        for (GLint unit = 0; unit < m_fragmentTextureUnits; ++unit)
            glBindSampler(unit, 0);
        glActiveTexture(GL_TEXTURE0);
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, 0);
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
        for (const auto parameter : unpackParameters)
            glPixelStorei(parameter, 0);
    }

    void restore() const noexcept
    {
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, existing(m_draw, glIsFramebuffer));
        const auto read = existing(m_read, glIsFramebuffer);
        glBindFramebuffer(GL_READ_FRAMEBUFFER, read);
        if (read == static_cast<GLuint>(m_read) && get(GL_READ_BUFFER) != m_readBuffer)
            glReadBuffer(m_readBuffer);
        glViewport(m_viewport[0], m_viewport[1], m_viewport[2], m_viewport[3]);
        glScissor(m_scissor[0], m_scissor[1], m_scissor[2], m_scissor[3]);
        auto program = existing(m_program, glIsProgram);
        GLint deleted = GL_FALSE;
        if (program)
            glGetProgramiv(program, GL_DELETE_STATUS, &deleted);
        glUseProgram(deleted ? 0 : program);
        glBindVertexArray(existing(m_vao, glIsVertexArray));
        glBindBuffer(GL_ARRAY_BUFFER, existing(m_arrayBuffer, glIsBuffer));
        glBindRenderbuffer(GL_RENDERBUFFER, existing(m_renderbuffer, glIsRenderbuffer));
        glBindBuffer(GL_PIXEL_PACK_BUFFER, existing(m_packBuffer, glIsBuffer));
        glBindBuffer(GL_PIXEL_UNPACK_BUFFER, existing(m_unpackBuffer, glIsBuffer));
        glBlendFuncSeparate(m_blend[0], m_blend[1], m_blend[2], m_blend[3]);
        glBlendEquationSeparate(m_blend[4], m_blend[5]);
        for (GLuint index = 0; index < m_drawBuffers.size(); ++index) {
            const auto& state = m_drawBuffers[index];
            if (m_indexedBlend) {
                glBlendFuncSeparatei(index, state.function[0], state.function[1], state.function[2], state.function[3]);
                glBlendEquationSeparatei(index, state.function[4], state.function[5]);
            }
            if (state.blend)
                glEnablei(GL_BLEND, index);
            else
                glDisablei(GL_BLEND, index);
            glColorMaski(index, state.mask[0], state.mask[1], state.mask[2], state.mask[3]);
        }
        glClearColor(m_clearColor[0], m_clearColor[1], m_clearColor[2], m_clearColor[3]);
        glLineWidth(m_lineWidth);
        glDepthMask(m_depthMask);
        glPolygonMode(GL_FRONT_AND_BACK, m_polygonMode);
        for (size_t index = 0; index < pixelParameters.size(); ++index)
            glPixelStorei(pixelParameters[index], m_pixelStore[index]);
        for (GLuint unit = 0; unit < m_textures.size(); ++unit) {
            const auto& texture = m_textures[unit];
            glActiveTexture(GL_TEXTURE0 + unit);
            glBindTexture(GL_TEXTURE_2D, existing(texture[0], glIsTexture));
            glBindTexture(GL_TEXTURE_3D, existing(texture[1], glIsTexture));
            glBindSampler(unit, existing(texture[2], glIsSampler));
        }
        glActiveTexture(m_activeTexture);
        for (size_t index = 0; index < capabilities.size(); ++index)
            enable(capabilities[index], m_enabled[index]);
        for (GLuint index = 0; index < m_clipEnabled.size(); ++index)
            enable(GL_CLIP_DISTANCE0 + index, m_clipEnabled[index]);
    }

private:
    static GLint get(GLenum parameter) noexcept
    {
        GLint value = 0;
        glGetIntegerv(parameter, &value);
        return value;
    }

    template<typename Predicate>
    static GLuint existing(GLint value, Predicate predicate) noexcept
    {
        return value && !predicate(static_cast<GLuint>(value)) ? 0 : static_cast<GLuint>(value);
    }

    static void enable(GLenum capability, GLboolean enabled) noexcept
    {
        if (enabled)
            glEnable(capability);
        else
            glDisable(capability);
    }

    static constexpr std::array<GLenum, 11> capabilities = {
        GL_DEPTH_TEST, GL_CULL_FACE, GL_SCISSOR_TEST, GL_STENCIL_TEST,
        GL_RASTERIZER_DISCARD, GL_FRAMEBUFFER_SRGB, GL_PROGRAM_POINT_SIZE,
        GL_LINE_SMOOTH, GL_SAMPLE_ALPHA_TO_COVERAGE, GL_SAMPLE_COVERAGE, GL_COLOR_LOGIC_OP
    };
    static constexpr std::array<GLenum, 10> resetCapabilities = {
        GL_BLEND, GL_DEPTH_TEST, GL_CULL_FACE, GL_SCISSOR_TEST, GL_STENCIL_TEST,
        GL_RASTERIZER_DISCARD, GL_FRAMEBUFFER_SRGB, GL_SAMPLE_ALPHA_TO_COVERAGE,
        GL_SAMPLE_COVERAGE, GL_COLOR_LOGIC_OP
    };
    static constexpr std::array<GLenum, 6> blendParameters = {
        GL_BLEND_SRC_RGB, GL_BLEND_DST_RGB, GL_BLEND_SRC_ALPHA, GL_BLEND_DST_ALPHA,
        GL_BLEND_EQUATION_RGB, GL_BLEND_EQUATION_ALPHA
    };
    static constexpr std::array<GLenum, 16> pixelParameters = {
        GL_PACK_ALIGNMENT, GL_PACK_ROW_LENGTH, GL_PACK_SKIP_PIXELS, GL_PACK_SKIP_ROWS,
        GL_UNPACK_ALIGNMENT, GL_UNPACK_ROW_LENGTH, GL_UNPACK_SKIP_PIXELS, GL_UNPACK_SKIP_ROWS,
        GL_PACK_IMAGE_HEIGHT, GL_PACK_SKIP_IMAGES, GL_UNPACK_IMAGE_HEIGHT, GL_UNPACK_SKIP_IMAGES,
        GL_PACK_SWAP_BYTES, GL_UNPACK_SWAP_BYTES, GL_PACK_LSB_FIRST, GL_UNPACK_LSB_FIRST
    };
    static constexpr std::array<GLenum, 7> unpackParameters = {
        GL_UNPACK_ROW_LENGTH, GL_UNPACK_SKIP_PIXELS, GL_UNPACK_SKIP_ROWS,
        GL_UNPACK_IMAGE_HEIGHT, GL_UNPACK_SKIP_IMAGES, GL_UNPACK_SWAP_BYTES, GL_UNPACK_LSB_FIRST
    };

    struct DrawBufferState {
        GLboolean blend{};
        std::array<GLboolean, 4> mask{};
        std::array<GLint, 6> function{};
    };

    bool m_indexedBlend{};
    GLint m_fragmentTextureUnits{};
    GLint m_draw{}, m_read{}, m_readBuffer{}, m_program{}, m_vao{}, m_arrayBuffer{};
    GLint m_renderbuffer{}, m_packBuffer{}, m_unpackBuffer{}, m_activeTexture{}, m_polygonMode{};
    GLfloat m_lineWidth{};
    GLboolean m_depthMask{};
    std::array<GLint, 4> m_viewport{}, m_scissor{};
    std::array<GLint, 6> m_blend{};
    std::array<GLint, 16> m_pixelStore{};
    std::array<GLfloat, 4> m_clearColor{};
    std::array<GLboolean, 11> m_enabled{};
    std::vector<GLboolean> m_clipEnabled;
    std::vector<DrawBufferState> m_drawBuffers;
    std::vector<std::array<GLint, 3>> m_textures;
};

class RenderStateGuard {
public:
    RenderStateGuard(RenderState& state, bool preserve) : m_state(state), m_preserve(preserve)
    {
        if (m_preserve)
            m_state.save();
    }

    ~RenderStateGuard()
    {
        if (m_preserve)
            m_state.restore();
    }

    RenderStateGuard(const RenderStateGuard&) = delete;
    RenderStateGuard& operator=(const RenderStateGuard&) = delete;

private:
    RenderState& m_state;
    bool m_preserve;
};

// Explicit framebuffer selection restores the preceding draw binding even when
// the caller owns all other GL state, matching pypm_render_frame_to_fbo.
class DrawFramebufferGuard {
public:
    explicit DrawFramebufferGuard(bool restore) : m_restore(restore)
    {
        if (m_restore)
            glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING, &m_draw);
    }

    ~DrawFramebufferGuard()
    {
        if (m_restore)
            glBindFramebuffer(GL_DRAW_FRAMEBUFFER, static_cast<GLuint>(m_draw));
    }

    DrawFramebufferGuard(const DrawFramebufferGuard&) = delete;
    DrawFramebufferGuard& operator=(const DrawFramebufferGuard&) = delete;

private:
    bool m_restore;
    GLint m_draw{};
};

} // namespace pypm_detail
