"""Small shared CLI and PCM sources; no audio device or extra package is needed."""

import argparse
import wave
from importlib.resources import files
from pathlib import Path

import numpy as np


DEMO_PRESET = Path(str(files("python_projectm").joinpath("presets/pulse.milk")))
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def positive_int(value):
    value = int(value)
    if value <= 0:
        raise argparse.ArgumentTypeError("Value must be positive")
    return value


def nonnegative_int(value):
    value = int(value)
    if value < 0:
        raise argparse.ArgumentTypeError("Value must be nonnegative")
    return value


def parser(description, *, frames=0):
    result = argparse.ArgumentParser(description=description)
    result.add_argument("--preset", type=Path, default=DEMO_PRESET, help="Milkdrop preset file")
    result.add_argument("--wav", type=Path, help="Loop an 8/16-bit PCM mono/stereo WAV instead of the demo signal")
    result.add_argument("--width", type=positive_int, default=960)
    result.add_argument("--height", type=positive_int, default=540)
    result.add_argument("--fps", type=positive_int, default=60)
    result.add_argument("--frames", type=nonnegative_int, default=frames,
                        help="Stop after N frames; 0 runs until interrupted or the window closes")
    return result


def audio_frame_count(index, sample_rate, fps):
    """Distribute fractional samples over successive frames without timing drift."""
    return (index + 1) * sample_rate // fps - index * sample_rate // fps


class AudioSource:
    """Stream looping WAV data or generate continuous stereo demonstration PCM.

    All reads belong to the caller's thread. Audio is submitted for analysis only;
    the examples do not play it or capture system audio.
    """

    def __init__(self, path=None):
        self._wave = None
        self._position = 0
        self.sample_rate = 44100
        self.channels = 2
        self.label = "Synthetic stereo"
        if path is not None:
            source = wave.open(str(path), "rb")
            try:
                if source.getcomptype() != "NONE" or source.getsampwidth() not in (1, 2):
                    raise ValueError("Choose an uncompressed 8-bit or 16-bit PCM WAV file")
                if source.getnchannels() not in (1, 2) or source.getnframes() == 0:
                    raise ValueError("Choose a nonempty mono or stereo WAV file")
            except BaseException:
                source.close()
                raise
            self._wave = source
            self.sample_rate = source.getframerate()
            self.channels = source.getnchannels()
            self.label = Path(path).name

    def read(self, frames, *, gain=0.65, paused=False):
        if paused:
            return np.zeros((frames, self.channels), dtype=np.float32)
        if self._wave is None:
            time = (np.arange(frames, dtype=np.float64) + self._position) / self.sample_rate
            envelope = 0.3 + 0.7 * np.maximum(0.0, np.sin(2 * np.pi * 1.8 * time)) ** 6
            left = envelope * (0.7 * np.sin(2 * np.pi * 110 * time) + 0.3 * np.sin(2 * np.pi * 440 * time))
            right = envelope * (0.7 * np.sin(2 * np.pi * 165 * time) + 0.3 * np.sin(2 * np.pi * 660 * time))
            self._position += frames
            return np.ascontiguousarray(np.column_stack((left, right)) * gain, dtype=np.float32)
        chunks = []
        remaining = frames
        while remaining:
            raw = self._wave.readframes(remaining)
            if not raw:
                self._wave.rewind()
                raw = self._wave.readframes(remaining)
                if not raw:
                    raise ValueError("The WAV file contains no readable PCM frames")
            width = self._wave.getsampwidth()
            dtype = np.uint8 if width == 1 else np.dtype("<i2")
            samples = np.frombuffer(raw, dtype=dtype).astype(np.float32)
            samples = (samples - 128.0) / 128.0 if width == 1 else samples / 32768.0
            samples = samples.reshape(-1, self.channels)
            chunks.append(samples)
            remaining -= len(samples)
        return np.ascontiguousarray(np.concatenate(chunks) * gain, dtype=np.float32)

    def close(self):
        if self._wave is not None:
            self._wave.close()
            self._wave = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


def save_ppm(path, frame):
    """Write a top-left-origin RGBA frame as RGB PPM using only the standard library."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    height, width, _ = frame.shape
    with path.open("wb") as output:
        output.write(f"P6\n{width} {height}\n255\n".encode("ascii"))
        output.write(np.ascontiguousarray(frame[:, :, :3]).tobytes())
