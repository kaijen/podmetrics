"""LUFS-I, Short-Term-Verlauf, Blockbalance, Gainberechnung."""

from __future__ import annotations

import itertools

import numpy as np
import pyloudnorm

from .models import AnalysisParams, Measurement, Signal

# Kürzestes Stück, das pyloudnorm noch entgegennimmt (Blockgröße 400 ms).
_MIN_BLOCK_S = 0.4


def _meter(sample_rate: int) -> pyloudnorm.Meter:
    return pyloudnorm.Meter(sample_rate)


def integrated_lufs(signal: Signal) -> float:
    if signal.duration_s < _MIN_BLOCK_S:
        return float("-inf")
    return float(_meter(signal.sample_rate).integrated_loudness(signal.samples))


def is_reliable(signal: Signal, params: AnalysisParams) -> bool:
    """LUFS-I braucht Mindestdauer, sonst greift das BS.1770-Gating unsicher.

    Kürzeres Material wird gemessen, aber als unzuverlässig markiert — nicht
    stillschweigend geliefert und nicht verweigert.
    """
    return signal.duration_s >= params.lufs_min_duration_s


def short_term(
    signal: Signal, params: AnalysisParams, hop_s: float = 1.0
) -> tuple[list[float], list[float]]:
    """Short-Term-Lautheit als grobe Kurve. Gibt (Werte, Zeiten) zurück.

    Der Verlauf wird mitgeführt und nicht nur sein Streumaß: Ein wandernder
    Mikrofonabstand zeigt sich als Drift über Minuten, während eine große
    P10–P90-Spanne aus lauten und leisen Sätzen dasselbe Streumaß erzeugt.
    """
    window = params.short_term_window_s
    if signal.duration_s < window:
        value = integrated_lufs(signal)
        return ([value], [0.0]) if np.isfinite(value) else ([], [])

    meter = _meter(signal.sample_rate)
    win = round(window * signal.sample_rate)
    hop = max(1, round(hop_s * signal.sample_rate))

    values: list[float] = []
    times: list[float] = []
    for start in range(0, len(signal.samples) - win + 1, hop):
        block = signal.samples[start : start + win]
        loudness = float(meter.integrated_loudness(block))
        if np.isfinite(loudness):
            values.append(loudness)
            times.append(start / signal.sample_rate)
    return values, times


def block_balance_db(signal: Signal, block_s: float = 30.0) -> float:
    """Lautheitsunterschied zwischen Abschnitten.

    Teilt das Material in gleich lange Blöcke und gibt die Spanne zwischen dem
    lautesten und dem leisesten zurück. Über 1 dB fällt beim Hören als
    Lautstärkesprung zwischen Abschnitten auf.
    """
    if signal.duration_s < 2 * _MIN_BLOCK_S:
        return 0.0
    count = max(2, int(signal.duration_s // block_s))
    edges = np.linspace(0, len(signal.samples), count + 1).astype(int)
    meter = _meter(signal.sample_rate)

    values = []
    for a, b in itertools.pairwise(edges):
        if (b - a) / signal.sample_rate < _MIN_BLOCK_S:
            continue
        loudness = float(meter.integrated_loudness(signal.samples[a:b]))
        if np.isfinite(loudness):
            values.append(loudness)
    if len(values) < 2:
        return 0.0
    return float(max(values) - min(values))


def gain_for_target_lufs(measurement: Measurement, target_lufs: float) -> float:
    """Faktor in dB, um den das Material auf den Zielwert zu schieben ist.

    Die Bibliothek wendet ihn nicht an; das ist Sache des Aufrufers. Ist
    ``lufs_i_reliable`` falsch, ist auch dieser Wert unzuverlässig — die
    Funktion rechnet trotzdem und verweigert nicht.
    """
    if not np.isfinite(measurement.lufs_i):
        raise ValueError("Ohne belastbaren LUFS-Wert gibt es keinen Gainfaktor.")
    return float(target_lufs - measurement.lufs_i)
