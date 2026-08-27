"""Synthetische Signale und Messungen von Hand.

Keine echten Audiodateien im Repository. Alles hier ist deterministisch
erzeugt, damit ein Testlauf zweimal dasselbe Ergebnis liefert.
"""

from __future__ import annotations

import numpy as np

from podmetrics.models import AnalysisParams, Measurement, Plosive, Signal

SR = 48000


def make_signal(samples: np.ndarray, sample_rate: int = SR) -> Signal:
    return Signal(
        samples=np.asarray(samples, dtype=np.float64),
        sample_rate=sample_rate,
        channel=0,
        source_channels=1,
        source_sha256="0" * 64,
    )


def speech_like(seconds: float = 40.0, seed: int = 1, low_boost: float = 0.0) -> Signal:
    """Sprachähnliches Signal: Grundton mit Silbenrhythmus, Pause, Rauschen."""
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    x = 0.25 * np.sin(2 * np.pi * 180 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.9 * t))
    x += 0.04 * rng.normal(0.0, 1.0, n)
    if low_boost:
        x += low_boost * np.sin(2 * np.pi * 150 * t)
    pause = slice(int(12 * SR), int(15 * SR))
    x[pause] = 2e-4 * rng.normal(0.0, 1.0, pause.stop - pause.start)
    return make_signal(x)


def make_measurement(**overrides: object) -> Measurement:
    """Ein Measurement von Hand, für die Empfehlungsregeln.

    Empfehlungen werden nicht aus Audio getestet: Das hielte die Tests langsam
    und versteckte die Schwellen im Signal, statt sie im Test zu zeigen.
    """
    centers = [100.0, 125.0, 160.0, 200.0, 250.0, 1000.0, 5000.0, 6300.0, 8000.0, 10000.0]
    defaults: dict[str, object] = dict(
        sample_rate=SR,
        channel=0,
        duration_s=60.0,
        peak_dbfs=-8.0,
        peak_speech_dbfs=-8.0,
        true_peak_dbtp=-7.9,
        crest_db=14.0,
        clipped_samples=0,
        lufs_i=-21.0,
        lufs_i_reliable=True,
        short_term_lufs=[-21.0] * 20,
        short_term_times_s=[float(i) for i in range(20)],
        block_balance_db=0.4,
        speech_median_dbfs=-21.0,
        speech_p10_dbfs=-29.0,
        speech_p90_dbfs=-13.0,
        speech_ratio=0.8,
        third_octave_hz=list(centers),
        third_octave_db=[0.0] * len(centers),
        comb_spacing_hz=None,
        comb_depth_db=None,
        plosives=[],
        noise_floor_dbfs=-58.0,
        noise_region_s=(10.0, 12.0),
        analysis_region_s=None,
        source_sha256="a" * 64,
        params=AnalysisParams(),
    )
    defaults.update(overrides)
    return Measurement(**defaults)  # type: ignore[arg-type]


def bands(**values: float) -> list[float]:
    """Terzbandkurve bauen: bands(hz_125=4.0) setzt nur dieses Band."""
    centers = [100.0, 125.0, 160.0, 200.0, 250.0, 1000.0, 5000.0, 6300.0, 8000.0, 10000.0]
    curve = [0.0] * len(centers)
    for key, value in values.items():
        curve[centers.index(float(key.removeprefix("hz_")))] = value
    return curve


def a_plosive() -> Plosive:
    return Plosive(time_s=6.818, peak_dbfs=-0.16, low_energy_share=0.956, block_share=0.287)
