"""Real-time mode: feed EEG as it arrives, get a prediction at every fMRI volume.

The model is causal by construction (each frame uses only the preceding 24 s of EEG), so it can run
during a scan. This class keeps a 24 s ring buffer, high-passes causally (Butterworth, 0.5 Hz) and
standardizes features with running statistics, since a live recording has no future to standardize with.
"""
import time

import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi

from .features import FS, WINDOW, bands60, vigilance, window_features


class StreamingMonitor:
    def __init__(self, model, channels=26, warmup_frames=15, prior_stats=None):
        self.model = model
        self.sos = butter(2, 0.5, btype="highpass", fs=FS, output="sos")
        self.zi = np.repeat(sosfilt_zi(self.sos)[:, None, :], channels, axis=1) * 0.0
        self.buffer = np.zeros((channels, WINDOW), dtype=np.float32)
        self.filled = 0
        self.n, self.sum, self.sumsq = 0, None, None
        self.warmup = warmup_frames
        self.prior = prior_stats  # (mean, sd) to use until enough frames are seen; default: the model's
        self.latency_ms = []

    def push(self, chunk):
        """chunk: (26, n) µV at 200 Hz, in the model's channel order."""
        filtered, self.zi = sosfilt(self.sos, chunk, axis=1, zi=self.zi)
        n = filtered.shape[1]
        if n >= WINDOW:
            self.buffer[:] = filtered[:, -WINDOW:]
        else:
            self.buffer = np.roll(self.buffer, -n, axis=1)
            self.buffer[:, -n:] = filtered
        self.filled = min(WINDOW, self.filled + n)

    def frame(self):
        """Prediction for a volume acquired now; None until 24 s of EEG have been seen."""
        if self.filled < WINDOW:
            return None
        start = time.perf_counter()
        window = self.buffer - self.buffer.mean(axis=1, keepdims=True)
        feats = window_features(window[None])
        x = self.model.inputs(feats)[0]
        self.n += 1
        self.sum = x.copy() if self.sum is None else self.sum + x
        self.sumsq = x ** 2 if self.sumsq is None else self.sumsq + x ** 2
        if self.n >= self.warmup:
            mean = self.sum / self.n
            sd = np.sqrt(np.maximum(self.sumsq / self.n - mean ** 2, 0)) + 1e-8
        else:
            mean, sd = self.prior if self.prior is not None else (self.model.mean, self.model.sd)
        pred = ((x - mean) / sd) @ self.model.weights + self.model.intercept
        self.latency_ms.append((time.perf_counter() - start) * 1000)
        return pred, float(vigilance(feats)[0])
