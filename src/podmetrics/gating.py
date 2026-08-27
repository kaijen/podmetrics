"""Sprachsegmente und Pausen trennen.

Vor jeder Pegelstatistik und vor allem Spektralen werden Sprechpausen
entfernt. Stille mischt dem Spektrum einen Rauschanteil bei und zieht die
Pegelverteilung mit einem Schwanz sehr leiser Werte nach unten, was den
Median verschiebt.
"""

from __future__ import annotations

import numpy as np

from .models import AnalysisParams, Signal

# Kleinster Pegel, den wir noch als Zahl ausgeben. Verhindert -inf in der
# Serialisierung, ohne eine reale Messung zu verfälschen.
FLOOR_DB = -120.0


def to_db(value: float | np.ndarray) -> np.ndarray:
    amplitude = np.maximum(np.abs(np.asarray(value, dtype=np.float64)), 1e-12)
    return np.maximum(20.0 * np.log10(amplitude), FLOOR_DB)


def rms_envelope(signal: Signal, params: AnalysisParams) -> tuple[np.ndarray, np.ndarray]:
    """Gleitendes RMS in dBFS. Gibt (Startzeiten, Pegel) zurück."""
    window = max(1, round(params.rms_window_ms * 1e-3 * signal.sample_rate))
    hop = max(1, round(window * (1.0 - params.rms_overlap)))
    samples = signal.samples
    if len(samples) < window:
        single = float(np.sqrt(np.mean(samples**2))) if len(samples) else 0.0
        return np.array([0.0]), to_db(single).reshape(1)

    starts = np.arange(0, len(samples) - window + 1, hop)
    frames = np.lib.stride_tricks.sliding_window_view(samples, window)[starts]
    rms = np.sqrt(np.mean(frames**2, axis=1))
    return starts / signal.sample_rate, to_db(rms)


def speech_segments(signal: Signal, params: AnalysisParams) -> list[tuple[int, int]]:
    """Sprachabschnitte als Sample-Indizes (Anfang, Ende).

    Gating gegen die Schwelle auf gleitendem RMS; Segmente unterhalb der
    Mindestdauer werden verworfen.
    """
    times, levels = rms_envelope(signal, params)
    window = max(1, round(params.rms_window_ms * 1e-3 * signal.sample_rate))
    loud = levels > params.gate_threshold_dbfs
    if not loud.any():
        return []

    min_len = round(params.gate_min_segment_ms * 1e-3 * signal.sample_rate)
    segments: list[tuple[int, int]] = []
    start_idx: int | None = None
    for i, is_loud in enumerate(loud):
        if is_loud and start_idx is None:
            start_idx = i
        elif not is_loud and start_idx is not None:
            segments.append((start_idx, i))
            start_idx = None
    if start_idx is not None:
        segments.append((start_idx, len(loud)))

    out: list[tuple[int, int]] = []
    for a, b in segments:
        first = round(times[a] * signal.sample_rate)
        last = round(times[b - 1] * signal.sample_rate) + window
        last = min(last, len(signal.samples))
        if last - first >= min_len:
            out.append((first, last))
    return out


def speech_samples(signal: Signal, params: AnalysisParams) -> np.ndarray:
    """Nur die Sprachabschnitte, aneinandergehängt."""
    segments = speech_segments(signal, params)
    if not segments:
        return np.empty(0, dtype=np.float64)
    return np.concatenate([signal.samples[a:b] for a, b in segments])


def speech_ratio(signal: Signal, params: AnalysisParams) -> float:
    if len(signal.samples) == 0:
        return 0.0
    total = sum(b - a for a, b in speech_segments(signal, params))
    return total / len(signal.samples)
