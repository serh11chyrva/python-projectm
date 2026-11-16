"""Render to a ModernGL texture, consume it in a shader, and save the result."""

import sys
import time

import moderngl
import numpy as np

from python_projectm.integrations.moderngl import ModernGLRenderer

from ._common import AudioSource, OUTPUT_DIR, audio_frame_count, parser, save_ppm


VERTEX_SHADER = """#version 330
out vec2 uv;
void main() {
    vec2 p = vec2((gl_VertexID << 1) & 2, gl_VertexID & 2);
    uv = p;
    gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0);
}
"""

FRAGMENT_SHADER = """#version 330
uniform sampler2D projectm_frame;
in vec2 uv;
out vec4 color;
void main() {
    vec3 rgb = texture(projectm_frame, uv).rgb;
    float vignette = 1.0 - 0.7 * dot(uv - 0.5, uv - 0.5);
    color = vec4(rgb * vignette, 1.0);
}
"""


def main(argv=None):
    options = parser(__doc__, frames=120)
    options.add_argument("--output", default=str(OUTPUT_DIR / "moderngl.ppm"))
    options.add_argument("--backend", help="Optional glcontext backend, for example egl on Linux")
    args = options.parse_args(argv)
    context = None
    resources = []
    try:
        kwargs = {"backend": args.backend} if args.backend else {}
        context = moderngl.create_standalone_context(require=330, **kwargs)
        with context, AudioSource(args.wav) as audio:
            program = context.program(vertex_shader=VERTEX_SHADER, fragment_shader=FRAGMENT_SHADER)
            resources.append(program)
            vao = context.vertex_array(program, [])
            resources.append(vao)
            output = context.texture((args.width, args.height), components=4, dtype="f1")
            resources.append(output)
            target = context.framebuffer(color_attachments=[output])
            resources.append(target)
            program["projectm_frame"].value = 0
            with ModernGLRenderer(context, args.width, args.height) as renderer:
                renderer.load_preset_file(args.preset, smooth=False)
                with renderer.current() as pm:
                    pm.fps = args.fps
                count = 0
                while not args.frames or count < args.frames:
                    started = time.monotonic()
                    renderer.add_pcm(audio.read(audio_frame_count(count, audio.sample_rate, args.fps)))
                    texture = renderer.render()
                    # The projectM output stays on the GPU while this shader consumes it.
                    target.use()
                    context.viewport = (0, 0, args.width, args.height)
                    context.disable(moderngl.BLEND | moderngl.DEPTH_TEST | moderngl.CULL_FACE)
                    texture.use(location=0)
                    vao.render(mode=moderngl.TRIANGLES, vertices=3)
                    count += 1
                    time.sleep(max(0.0, 1.0 / args.fps - (time.monotonic() - started)))
                # Read back only the final result, converting OpenGL's bottom-left origin.
                frame = np.frombuffer(target.read(components=4, alignment=1), dtype=np.uint8)
                frame = frame.reshape(args.height, args.width, 4)[::-1]
                save_ppm(args.output, frame)
                print(f"ModernGL rendered {count} frames through a texture shader; saved {args.output}")
        return 0
    except (Exception, KeyboardInterrupt) as error:
        print(f"ModernGL: {error}", file=sys.stderr)
        return 130 if isinstance(error, KeyboardInterrupt) else 1
    finally:
        if context is not None:
            with context:
                for resource in reversed(resources):
                    resource.release()
            context.release()


if __name__ == "__main__":
    raise SystemExit(main())
