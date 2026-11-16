"""Read reusable RGBA NumPy frames and save the final frame without an image dependency."""

import sys
import time

import glfw
import numpy as np

from python_projectm.integrations.numpy import NumpyRenderer

from ._common import AudioSource, OUTPUT_DIR, audio_frame_count, parser, save_ppm


def main(argv=None):
    options = parser(__doc__, frames=120)
    options.add_argument("--output", type=str, default=str(OUTPUT_DIR / "numpy.ppm"))
    args = options.parse_args(argv)
    count = 0
    try:
        with AudioSource(args.wav) as audio, NumpyRenderer(args.width, args.height) as renderer:
            renderer.load_preset_file(args.preset, smooth=False)
            with renderer.current() as pm:
                pm.fps = args.fps
            # Consumers may reuse this buffer only after they have finished reading it.
            frame = np.empty((args.height, args.width, 4), dtype=np.uint8)
            while not args.frames or count < args.frames:
                started = time.monotonic()
                glfw.poll_events()
                renderer.add_pcm(audio.read(audio_frame_count(count, audio.sample_rate, args.fps)))
                renderer.render_frame(out=frame)
                count += 1
                time.sleep(max(0.0, 1.0 / args.fps - (time.monotonic() - started)))
            save_ppm(args.output, frame)
            print(f"NumPy rendered {count} RGBA frames: {frame.shape}, {frame.dtype}; saved {args.output}")
        return 0
    except (Exception, KeyboardInterrupt) as error:
        print(f"NumPy: {error}", file=sys.stderr)
        return 130 if isinstance(error, KeyboardInterrupt) else 1
    finally:
        glfw.terminate()


if __name__ == "__main__":
    raise SystemExit(main())
