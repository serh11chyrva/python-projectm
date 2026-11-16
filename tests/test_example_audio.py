"""Ensure the examples' streamed PCM stays continuous and handles WAV looping."""

import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from examples._common import AudioSource, audio_frame_count


class ExampleAudioTests(unittest.TestCase):
    def test_synthetic_blocks_are_continuous(self):
        with AudioSource() as split, AudioSource() as whole:
            actual = np.concatenate((split.read(127), split.read(385)))
            np.testing.assert_array_equal(actual, whole.read(512))
            self.assertEqual(actual.dtype, np.float32)
            self.assertEqual(actual.shape, (512, 2))
            self.assertLessEqual(float(np.abs(actual).max()), 1.0)

    def test_frame_counts_do_not_accumulate_rounding_error(self):
        counts = [audio_frame_count(index, 44100, 59) for index in range(59)]
        self.assertEqual(sum(counts), 44100)

    def test_wav_loops_and_converts_8_and_16_bit_pcm(self):
        with tempfile.TemporaryDirectory() as directory:
            for width, dtype, values, expected in (
                (1, np.uint8, [0, 128, 255], [-1, 0, 127 / 128]),
                (2, np.dtype("<i2"), [-32768, 0, 32767], [-1, 0, 32767 / 32768]),
            ):
                with self.subTest(width=width):
                    path = Path(directory) / "audio.wav"
                    with wave.open(str(path), "wb") as output:
                        output.setnchannels(1)
                        output.setsampwidth(width)
                        output.setframerate(22050)
                        output.writeframes(np.array(values, dtype=dtype).tobytes())
                    with AudioSource(path) as audio:
                        self.assertEqual(audio.sample_rate, 22050)
                        block = audio.read(8, gain=1.0)
                        np.testing.assert_allclose(block[:, 0], (expected * 3)[:8])

    def test_pausing_preserves_the_audio_position(self):
        with AudioSource() as paused, AudioSource() as reference:
            np.testing.assert_array_equal(paused.read(100, paused=True), np.zeros((100, 2)))
            np.testing.assert_array_equal(paused.read(100), reference.read(100))

    def test_unsupported_wav_width_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audio.wav"
            with wave.open(str(path), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(3)
                output.setframerate(44100)
                output.writeframes(b"\0\0\0")
            with self.assertRaisesRegex(ValueError, "8-bit or 16-bit"):
                AudioSource(path)

    def test_truncated_wav_cannot_loop_forever(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "truncated.wav"
            with wave.open(str(path), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(44100)
                output.writeframes(b"\0\0" * 8)
            path.write_bytes(path.read_bytes()[:-16])
            with AudioSource(path) as audio, self.assertRaisesRegex(ValueError, "no readable PCM"):
                audio.read(8)
