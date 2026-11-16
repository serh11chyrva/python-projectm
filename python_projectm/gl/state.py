"""Restore OpenGL state changed by projectM and pixel readback."""

from OpenGL import GL

from python_projectm.gl.context import ContextGuard


class ViewportGuard:
    """Restore the viewport on exit with the same thread and GL context current."""

    def __enter__(self):
        self._guard = ContextGuard()
        self._old = tuple(int(value) for value in GL.glGetIntegerv(GL.GL_VIEWPORT))
        return self

    def __exit__(self, exc_type, exc, tb):
        self._guard.check()
        GL.glViewport(*self._old)


class GLStateGuard:
    """Preserve the desktop OpenGL 3.3 state used by projectM.

    A guard does not make a context current. The same context must remain current
    until exit. Applications can disable preservation when they own all GL state.
    """

    _capabilities = (
        GL.GL_DEPTH_TEST, GL.GL_CULL_FACE, GL.GL_SCISSOR_TEST,
        GL.GL_STENCIL_TEST, GL.GL_RASTERIZER_DISCARD, GL.GL_FRAMEBUFFER_SRGB,
        GL.GL_PROGRAM_POINT_SIZE, GL.GL_LINE_SMOOTH, GL.GL_SAMPLE_ALPHA_TO_COVERAGE,
        GL.GL_SAMPLE_COVERAGE, GL.GL_COLOR_LOGIC_OP,
    )
    _pixel_parameters = (
        GL.GL_PACK_ALIGNMENT, GL.GL_PACK_ROW_LENGTH, GL.GL_PACK_SKIP_PIXELS,
        GL.GL_PACK_SKIP_ROWS, GL.GL_UNPACK_ALIGNMENT, GL.GL_UNPACK_ROW_LENGTH,
        GL.GL_UNPACK_SKIP_PIXELS, GL.GL_UNPACK_SKIP_ROWS,
        GL.GL_PACK_IMAGE_HEIGHT, GL.GL_PACK_SKIP_IMAGES, GL.GL_UNPACK_IMAGE_HEIGHT,
        GL.GL_UNPACK_SKIP_IMAGES, GL.GL_PACK_SWAP_BYTES, GL.GL_UNPACK_SWAP_BYTES,
        GL.GL_PACK_LSB_FIRST, GL.GL_UNPACK_LSB_FIRST,
    )

    def __init__(self, *, check_resources: bool = True):
        self._check_resources = check_resources

    def __enter__(self):
        self._guard = ContextGuard()
        get = lambda name: int(GL.glGetIntegerv(name))
        self._draw = get(GL.GL_DRAW_FRAMEBUFFER_BINDING)
        self._read = get(GL.GL_READ_FRAMEBUFFER_BINDING)
        self._read_buffer = get(GL.GL_READ_BUFFER)
        self._viewport = tuple(GL.glGetIntegerv(GL.GL_VIEWPORT))
        self._scissor = tuple(GL.glGetIntegerv(GL.GL_SCISSOR_BOX))
        self._program = get(GL.GL_CURRENT_PROGRAM)
        self._vao = get(GL.GL_VERTEX_ARRAY_BINDING)
        self._array_buffer = get(GL.GL_ARRAY_BUFFER_BINDING)
        self._renderbuffer = get(GL.GL_RENDERBUFFER_BINDING)
        self._pack_buffer = get(GL.GL_PIXEL_PACK_BUFFER_BINDING)
        self._unpack_buffer = get(GL.GL_PIXEL_UNPACK_BUFFER_BINDING)
        self._active_texture = get(GL.GL_ACTIVE_TEXTURE)
        self._enabled = {cap: bool(GL.glIsEnabled(cap)) for cap in self._capabilities}
        self._clip_enabled = [
            bool(GL.glIsEnabled(GL.GL_CLIP_DISTANCE0 + index))
            for index in range(get(GL.GL_MAX_CLIP_DISTANCES))
        ]
        self._blend_enabled = [
            bool(GL.glIsEnabledi(GL.GL_BLEND, index))
            for index in range(get(GL.GL_MAX_DRAW_BUFFERS))
        ]
        self._blend_func = tuple(get(name) for name in (
            GL.GL_BLEND_SRC_RGB, GL.GL_BLEND_DST_RGB, GL.GL_BLEND_SRC_ALPHA, GL.GL_BLEND_DST_ALPHA
        ))
        self._blend_equation = (get(GL.GL_BLEND_EQUATION_RGB), get(GL.GL_BLEND_EQUATION_ALPHA))
        self._indexed_blend = []
        if get(GL.GL_MAJOR_VERSION) >= 4:
            for index in range(len(self._blend_enabled)):
                self._indexed_blend.append(tuple(int(GL.glGetIntegeri_v(name, index)) for name in (
                    GL.GL_BLEND_SRC_RGB, GL.GL_BLEND_DST_RGB, GL.GL_BLEND_SRC_ALPHA,
                    GL.GL_BLEND_DST_ALPHA, GL.GL_BLEND_EQUATION_RGB, GL.GL_BLEND_EQUATION_ALPHA,
                )))
        self._clear_color = tuple(GL.glGetFloatv(GL.GL_COLOR_CLEAR_VALUE))
        self._line_width = float(GL.glGetFloatv(GL.GL_LINE_WIDTH))
        self._depth_mask = bool(GL.glGetBooleanv(GL.GL_DEPTH_WRITEMASK))
        self._polygon_mode = int(GL.glGetIntegerv(GL.GL_POLYGON_MODE)[0])
        self._pixel_store = {name: get(name) for name in self._pixel_parameters}
        self._color_masks = [
            tuple(bool(value) for value in GL.glGetBooleani_v(GL.GL_COLOR_WRITEMASK, index))
            for index in range(get(GL.GL_MAX_DRAW_BUFFERS))
        ]
        self._textures = []
        try:
            for unit in range(get(GL.GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS)):
                GL.glActiveTexture(GL.GL_TEXTURE0 + unit)
                self._textures.append((
                    get(GL.GL_TEXTURE_BINDING_2D),
                    get(GL.GL_TEXTURE_BINDING_3D),
                    get(GL.GL_SAMPLER_BINDING),
                ))
        finally:
            GL.glActiveTexture(self._active_texture)
        return self

    def __exit__(self, exc_type, exc, tb):
        self._guard.check()

        def existing(value, predicate):
            if self._check_resources and value and not predicate(value):
                return 0
            return value

        GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, existing(self._draw, GL.glIsFramebuffer))
        read = existing(self._read, GL.glIsFramebuffer)
        GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, read)
        if read == self._read and int(GL.glGetIntegerv(GL.GL_READ_BUFFER)) != self._read_buffer:
            GL.glReadBuffer(self._read_buffer)
        GL.glViewport(*self._viewport)
        GL.glScissor(*self._scissor)
        program = existing(self._program, GL.glIsProgram)
        if self._check_resources and program and GL.glGetProgramiv(program, GL.GL_DELETE_STATUS):
            program = 0
        GL.glUseProgram(program)
        GL.glBindVertexArray(existing(self._vao, GL.glIsVertexArray))
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, existing(self._array_buffer, GL.glIsBuffer))
        GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, existing(self._renderbuffer, GL.glIsRenderbuffer))
        GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, existing(self._pack_buffer, GL.glIsBuffer))
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, existing(self._unpack_buffer, GL.glIsBuffer))
        GL.glBlendFuncSeparate(*self._blend_func)
        GL.glBlendEquationSeparate(*self._blend_equation)
        for index, state in enumerate(self._indexed_blend):
            GL.glBlendFuncSeparatei(index, *state[:4])
            GL.glBlendEquationSeparatei(index, *state[4:])
        for index, enabled in enumerate(self._blend_enabled):
            (GL.glEnablei if enabled else GL.glDisablei)(GL.GL_BLEND, index)
        GL.glClearColor(*self._clear_color)
        GL.glLineWidth(self._line_width)
        GL.glDepthMask(self._depth_mask)
        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, self._polygon_mode)
        for index, mask in enumerate(self._color_masks):
            GL.glColorMaski(index, *mask)
        for name, value in self._pixel_store.items():
            GL.glPixelStorei(name, value)
        for unit, (texture_2d, texture_3d, sampler) in enumerate(self._textures):
            GL.glActiveTexture(GL.GL_TEXTURE0 + unit)
            GL.glBindTexture(GL.GL_TEXTURE_2D, existing(texture_2d, GL.glIsTexture))
            GL.glBindTexture(GL.GL_TEXTURE_3D, existing(texture_3d, GL.glIsTexture))
            GL.glBindSampler(unit, existing(sampler, GL.glIsSampler))
        GL.glActiveTexture(self._active_texture)
        for cap, enabled in self._enabled.items():
            (GL.glEnable if enabled else GL.glDisable)(cap)
        for index, enabled in enumerate(self._clip_enabled):
            (GL.glEnable if enabled else GL.glDisable)(GL.GL_CLIP_DISTANCE0 + index)


def prepare_render_state() -> None:
    """Remove caller state that would clip, mask, or discard projectM's output."""
    for cap in (
        GL.GL_BLEND, GL.GL_DEPTH_TEST, GL.GL_CULL_FACE, GL.GL_SCISSOR_TEST, GL.GL_STENCIL_TEST,
        GL.GL_RASTERIZER_DISCARD, GL.GL_FRAMEBUFFER_SRGB, GL.GL_SAMPLE_ALPHA_TO_COVERAGE,
        GL.GL_SAMPLE_COVERAGE, GL.GL_COLOR_LOGIC_OP,
    ):
        GL.glDisable(cap)
    GL.glColorMask(True, True, True, True)
    GL.glDepthMask(False)
    GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)
    GL.glBlendEquationSeparate(GL.GL_FUNC_ADD, GL.GL_FUNC_ADD)
    for index in range(int(GL.glGetIntegerv(GL.GL_MAX_CLIP_DISTANCES))):
        GL.glDisable(GL.GL_CLIP_DISTANCE0 + index)
    for unit in range(int(GL.glGetIntegerv(GL.GL_MAX_TEXTURE_IMAGE_UNITS))):
        GL.glBindSampler(unit, 0)
    GL.glActiveTexture(GL.GL_TEXTURE0)
    GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)
    GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
    for name in (
        GL.GL_UNPACK_ROW_LENGTH, GL.GL_UNPACK_SKIP_PIXELS, GL.GL_UNPACK_SKIP_ROWS,
        GL.GL_UNPACK_IMAGE_HEIGHT, GL.GL_UNPACK_SKIP_IMAGES, GL.GL_UNPACK_SWAP_BYTES,
        GL.GL_UNPACK_LSB_FIRST,
    ):
        GL.glPixelStorei(name, 0)
