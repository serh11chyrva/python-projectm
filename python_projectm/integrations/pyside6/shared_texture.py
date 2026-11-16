"""Triple-buffered textures shared by a render context and a Qt widget context."""

import threading
from contextlib import contextmanager
from dataclasses import dataclass

from OpenGL import GL
from PySide6.QtGui import QOpenGLContext

from python_projectm.gl.fbo import TextureFramebuffer
from python_projectm.gl.renderer import Renderer
from python_projectm.integrations.pyside6.render_thread import RenderThread


def frame_fence():
    """Submit a fence before handing GPU resources to the other context."""
    fence = GL.glFenceSync(GL.GL_SYNC_GPU_COMMANDS_COMPLETE, 0)
    if not fence:
        raise RuntimeError("OpenGL could not create a shared-texture fence")
    GL.glFlush()
    return fence


def wait_fence(fence):
    """Enqueue a GPU wait without blocking Python, then release the sync object."""
    if fence is not None:
        GL.glWaitSync(fence, 0, GL.GL_TIMEOUT_IGNORED)
        GL.glDeleteSync(fence)


@dataclass
class _TextureSlot:
    target: TextureFramebuffer | None = None
    texture_id: int = 0
    width: int = 0
    height: int = 0
    state: str = "free"
    sequence: int = 0
    ready_fence: object = None
    read_fence: object = None


class TextureMailbox:
    """Transfer texture ownership, retaining only the newest pending frame.

    The GUI holds ``reading()`` until its blit and read fence are submitted.
    This also prevents shutdown from retiring a texture during a GUI read.
    Framebuffer objects always remain in the contexts that created them.
    """

    def __init__(self):
        self._slots = [_TextureSlot() for _ in range(3)]
        self._lock = threading.Lock()
        self._displayed = None
        self._sequence = 0
        self._notification_queued = False
        self._awaiting_paint = False
        self._closed = False

    def writing(self):
        with self._lock:
            if self._closed:
                raise RuntimeError("The shared-texture mailbox is closed")
            available = []
            for slot in self._slots:
                if slot.state not in ("free", "ready"):
                    continue
                fence = slot.read_fence if slot.state == "free" else slot.ready_fence
                if fence is not None:
                    status = GL.glClientWaitSync(fence, 0, 0)
                    if status == GL.GL_WAIT_FAILED:
                        raise RuntimeError("OpenGL could not query a shared-texture fence")
                    if status == GL.GL_TIMEOUT_EXPIRED:
                        continue
                available.append(slot)
            if not available:
                return None, None, None
            slot = min(available, key=lambda item: item.sequence)
            slot.state = "writing"
            ready, consumed = slot.ready_fence, slot.read_fence
            slot.ready_fence = slot.read_fence = None
            return slot, ready, consumed

    def publish(self, slot, fence) -> bool:
        with self._lock:
            self._sequence += 1
            slot.sequence = self._sequence
            slot.ready_fence = fence
            slot.state = "ready"
            notify = not self._notification_queued and not self._awaiting_paint
            if notify:
                self._notification_queued = True
            return notify

    def notification_received(self):
        with self._lock:
            self._notification_queued = False
            self._awaiting_paint = True

    @contextmanager
    def reading(self):
        with self._lock:
            self._awaiting_paint = False
            if self._closed:
                yield None, None
                return
            sequence = self._displayed.sequence if self._displayed is not None else 0
            ready = [slot for slot in self._slots
                     if slot.state == "ready" and slot.sequence > sequence]
            fence = None
            if ready:
                if self._displayed is not None:
                    self._displayed.state = "free"
                self._displayed = max(ready, key=lambda item: item.sequence)
                self._displayed.state = "displayed"
                fence = self._displayed.ready_fence
                self._displayed.ready_fence = None
            yield self._displayed, fence

    def retire(self):
        with self._lock:
            self._closed = True
            self._displayed = None
            return self._slots


class _SharedTextureRenderer(Renderer):
    def __init__(self, context, width, height, mailbox):
        self.mailbox = mailbox
        super().__init__(context, width, height, preserve_state=False)

    def render_frame(self) -> bool:
        with self.current() as pm:
            slot, ready, consumed = self.mailbox.writing()
            if slot is None:
                return False
            # A superseded producer fence is ordered before this frame in the
            # same context. Only GUI reads require a cross-context wait.
            if ready is not None:
                GL.glDeleteSync(ready)
            wait_fence(consumed)
            if (slot.width, slot.height) != self.size:
                if slot.target is not None:
                    slot.target.close()
                    slot.target = None
                slot.target = TextureFramebuffer(*self.size)
                slot.texture_id = slot.target.texture_id
                slot.width, slot.height = self.size
            pm.render(framebuffer=slot.target.fbo_id, preserve_state=False)
            return self.mailbox.publish(slot, frame_fence())

    def close(self) -> None:
        if self.closed:
            return
        with self.current():
            for slot in self.mailbox.retire():
                wait_fence(slot.read_fence)
                slot.read_fence = None
                if slot.ready_fence is not None:
                    GL.glDeleteSync(slot.ready_fence)
                    slot.ready_fence = None
                if slot.target is not None:
                    slot.target.close()
                    slot.target = None
        super().close()


class TextureRenderThread(RenderThread):
    """Internal worker for ThreadedProjectMWidget; all output stays on the GPU."""

    def __init__(self, width, height, emitter, *, fps, share_context, commands,
                 pcm_buffers, startup_preset=None):
        self._share_context = share_context
        self._startup_preset = startup_preset
        self.mailbox = TextureMailbox()
        super().__init__(width, height, emitter, fps=fps)
        self._commands = commands
        self._pcm_buffers = pcm_buffers

    def _surface_format(self):
        return self._share_context.format()

    def _configure_context(self, context):
        context.setShareContext(self._share_context)

    def _create_renderer(self, adapter):
        if not QOpenGLContext.areSharing(QOpenGLContext.currentContext(), self._share_context):
            raise RuntimeError("Qt could not share textures with the widget's OpenGL context")
        renderer = _SharedTextureRenderer(adapter, self.width, self.height, self.mailbox)
        if self._startup_preset is not None:
            name, args, kwargs = self._startup_preset
            try:
                getattr(renderer, name)(*args, **kwargs)
            except Exception as error:
                self._report_error(error)
        return renderer

    def _emit_frame(self, renderer):
        if renderer.render_frame():
            # At most one notification is pending while the GUI is busy/hidden.
            self.emitter.frame_ready.emit(None)
