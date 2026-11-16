"""PCM validation and native frame counts without an OpenGL context."""

import unittest

import numpy as np

from python_projectm.core.audio import AudioMixin, prepare_pcm
from python_projectm.native import bindings as native


class RecordingAudio(AudioMixin):
    """Copy submitted native buffers while their ctypes pointers are valid."""

    def __init__(self, maximum=3):
        self.maximum = maximum
        self.blocks = []

    def _check_alive(self):
        pass

    def _call(self, function, *args, **kwargs):
        if function is native.pypm_pcm_get_max_samples:
            return self.maximum
        pointer, count, channels = args
        data = np.ctypeslib.as_array(pointer, shape=(count * channels,)).copy()
        self.blocks.append((function, count, channels, data))


class PreparePCMTests(unittest.TestCase):
    def test_mono_and_stereo_channel_inference(self):
        for shape, expected in (((7,), 1), ((7, 1), 1), ((7, 2), 2)):
            with self.subTest(shape=shape):
                data, channels = prepare_pcm(np.zeros(shape), None, np.float32)
                self.assertEqual(channels, expected)
                self.assertEqual(data.shape, (7, expected))
                self.assertEqual(data.dtype, np.float32)

    def test_flat_interleaved_stereo_preserves_channel_order(self):
        data, channels = prepare_pcm([1, 10, 2, 20], 2, np.int16)
        np.testing.assert_array_equal(data, [[1, 10], [2, 20]])
        self.assertEqual(channels, 2)

    def test_noncontiguous_stereo_is_copied(self):
        source = np.arange(40, dtype=np.float32).reshape(10, 4)[::2, ::2]
        data, _ = prepare_pcm(source, None, np.float32)
        self.assertTrue(data.flags.c_contiguous)
        np.testing.assert_array_equal(data, source)

    def test_invalid_shapes_and_channels_are_rejected(self):
        cases = ((np.zeros((2, 8)), None), (np.zeros((2, 2, 2)), None),
                 (np.zeros((4, 2)), 1), (np.zeros(5), 2),
                 (np.zeros(4), 0), (np.zeros(4), 3))
        for samples, channels in cases:
            with self.subTest(shape=samples.shape, channels=channels):
                with self.assertRaises(ValueError):
                    prepare_pcm(samples, channels, np.float32)
        with self.assertRaises(TypeError):
            prepare_pcm([0], True, np.float32)

    def test_nonfinite_audio_is_rejected(self):
        for value in (np.nan, np.inf, -np.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                prepare_pcm([value], None, np.float32)


class AudioSubmissionTests(unittest.TestCase):
    def test_dispatch_and_chunking_count_frames_per_channel(self):
        formats = ((np.float64, native.pypm_pcm_add_float, np.float32),
                   (np.int16, native.pypm_pcm_add_int16, np.int16),
                   (np.uint8, native.pypm_pcm_add_uint8, np.uint8))
        for dtype, function, native_dtype in formats:
            with self.subTest(dtype=dtype):
                audio = RecordingAudio()
                samples = np.arange(16, dtype=dtype).reshape(8, 2)
                audio.add_pcm(samples)
                self.assertEqual([block[1] for block in audio.blocks], [3, 3, 2])
                self.assertTrue(all(block[0] is function for block in audio.blocks))
                self.assertTrue(all(block[2] == 2 for block in audio.blocks))
                actual = np.concatenate([block[3] for block in audio.blocks])
                np.testing.assert_array_equal(actual, samples.astype(native_dtype).ravel())

    def test_empty_audio_never_reaches_native_submission(self):
        audio = RecordingAudio()
        audio.add_pcm(np.empty((0, 2), dtype=np.int16))
        self.assertEqual(audio.blocks, [])

    def test_unsupported_integer_scaling_is_not_guessed(self):
        audio = RecordingAudio()
        for dtype in (np.int32, np.int64, np.uint16, np.bool_, np.complex64):
            with self.subTest(dtype=dtype), self.assertRaises(TypeError):
                audio.add_pcm(np.zeros(4, dtype=dtype))
        self.assertEqual(audio.blocks, [])

    def test_invalid_native_limit_is_reported(self):
        from python_projectm.core.errors import ProjectMError

        with self.assertRaises(ProjectMError):
            RecordingAudio(maximum=0).add_pcm_float([0.0])
