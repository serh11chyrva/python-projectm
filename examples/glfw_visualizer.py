"""A resizable GLFW visualizer with synthetic or WAV PCM input."""

import sys
import time

import glfw

from python_projectm.integrations.glfw import GLFWRenderer

from ._common import AudioSource, audio_frame_count, parser


def main(argv=None):
    args = parser(__doc__).parse_args(argv)
    count = 0
    try:
        with AudioSource(args.wav) as audio:
            with GLFWRenderer(width=args.width, height=args.height,
                              title="projectM | GLFW | Esc to close") as renderer:
                renderer.load_preset_file(args.preset, smooth=False)
                with renderer.current() as pm:
                    pm.fps = args.fps
                    glfw.swap_interval(1)
                while not renderer.should_close and (not args.frames or count < args.frames):
                    started = time.monotonic()
                    renderer.poll_events()
                    if glfw.get_key(renderer.window, glfw.KEY_ESCAPE) == glfw.PRESS:
                        break
                    samples = audio.read(audio_frame_count(count, audio.sample_rate, args.fps))
                    renderer.add_pcm(samples)
                    if renderer.render():
                        count += 1
                    time.sleep(max(0.0, 1.0 / args.fps - (time.monotonic() - started)))
        print(f"GLFW rendered {count} frames")
        return 0
    except (Exception, KeyboardInterrupt) as error:
        print(f"GLFW: {error}", file=sys.stderr)
        return 130 if isinstance(error, KeyboardInterrupt) else 1
    finally:
        # This example owns global GLFW lifetime; the adapter itself never terminates it.
        glfw.terminate()


if __name__ == "__main__":
    raise SystemExit(main())
