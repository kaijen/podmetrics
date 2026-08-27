"""Peak, True Peak, Crest, RMS-Perzentile, Plosive."""

from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks, resample_poly

from .gating import FLOOR_DB, rms_envelope, speech_samples, speech_segments, to_db
from .models import AnalysisParams, Plosive, Signal


def peak_dbfs(samples: np.ndarray) -> float:
    if len(samples) == 0:
        return FLOOR_DB
    return float(to_db(np.max(np.abs(samples))))


def clipped_samples(samples: np.ndarray, threshold: float = 0.999969) -> int:
    """Samples an oder über der Vollaussteuerung.

    Die Schwelle liegt bei −1 LSB von 16 Bit; alles darüber ist bei jeder
    üblichen Wortbreite an der Grenze.
    """
    return int(np.count_nonzero(np.abs(samples) >= threshold))


def true_peak_dbtp(samples: np.ndarray, oversampling: int = 4) -> float:
    """True Peak durch Oversampling.

    pyloudnorm liefert keinen True Peak, und der Sample-Peak übersieht
    Intersample-Spitzen.
    """
    if len(samples) == 0:
        return FLOOR_DB
    upsampled = resample_poly(samples, oversampling, 1)
    return float(to_db(np.max(np.abs(upsampled))))


def rms_dbfs(samples: np.ndarray) -> float:
    if len(samples) == 0:
        return FLOOR_DB
    return float(to_db(np.sqrt(np.mean(samples**2))))


def crest_db(samples: np.ndarray) -> float:
    """Abstand zwischen Spitze und Mittel."""
    return peak_dbfs(samples) - rms_dbfs(samples)


def speech_percentiles(signal: Signal, params: AnalysisParams) -> tuple[float, float, float]:
    """Median, P10 und P90 des Sprechpegels in dBFS.

    Gerechnet auf dem gleitenden RMS der Sprachabschnitte, nicht auf
    Einzelsamples: Gefragt ist der Pegel, den man hört, nicht der Momentanwert.
    """
    segments = speech_segments(signal, params)
    if not segments:
        return FLOOR_DB, FLOOR_DB, FLOOR_DB

    levels: list[np.ndarray] = []
    for a, b in segments:
        part = Signal(
            samples=signal.samples[a:b],
            sample_rate=signal.sample_rate,
            channel=signal.channel,
            source_channels=signal.source_channels,
            source_sha256=signal.source_sha256,
        )
        _, block = rms_envelope(part, params)
        levels.append(block)
    values = np.concatenate(levels)
    median, p10, p90 = np.percentile(values, [50, 10, 90])
    return float(median), float(p10), float(p90)


def _low_share(block: np.ndarray, sample_rate: int, split_hz: float) -> float:
    """Energieanteil unterhalb von split_hz."""
    if len(block) < 8:
        return 0.0
    windowed = block * np.hanning(len(block))
    spectrum = np.abs(np.fft.rfft(windowed)) ** 2
    freqs = np.fft.rfftfreq(len(block), 1.0 / sample_rate)
    total = float(spectrum.sum())
    if total <= 0.0:
        return 0.0
    return float(spectrum[freqs < split_hz].sum() / total)


def find_plosives(signal: Signal, params: AnalysisParams) -> list[Plosive]:
    """Spitzen, deren Tieftonanteil weit über dem des Sprachblocks liegt.

    Bei P und B verlässt ein Luftstoß den Mund und trifft die Membran. In der
    Messreihe lagen 95,6 % der Energie einer solchen Spitze unter 120 Hz,
    gegen 28,7 % im Blockdurchschnitt. Zur Verständlichkeit trägt sie nichts
    bei, und der Hochpass entfernt sie später ohnehin — deshalb ist sie kein
    Maßstab für den Gain.
    """
    speech = speech_samples(signal, params)
    if len(speech) == 0:
        return []
    sr = signal.sample_rate
    block_share = _low_share(speech, sr, params.plosive_split_hz)

    envelope = np.abs(signal.samples)
    peak = float(envelope.max()) if len(envelope) else 0.0
    if peak <= 0.0:
        return []

    # Kandidaten sind nur die lautesten Ausschläge — nur dort entscheidet sich,
    # ob der Peak-Wert von Sprache oder von einem Luftstoß stammt.
    height = peak * 10 ** (-6.0 / 20.0)
    distance = max(1, round(0.05 * sr))
    indices, _ = find_peaks(envelope, height=height, distance=distance)

    half = max(4, round(0.015 * sr))
    threshold = max(params.plosive_min_share, params.plosive_share_factor * block_share)

    out: list[Plosive] = []
    for index in indices:
        a = max(0, index - half)
        b = min(len(signal.samples), index + half)
        share = _low_share(signal.samples[a:b], sr, params.plosive_split_hz)
        if share >= threshold:
            out.append(
                Plosive(
                    time_s=float(index / sr),
                    peak_dbfs=float(to_db(envelope[index])),
                    low_energy_share=share,
                    block_share=block_share,
                )
            )
    return out


def peak_speech_dbfs(signal: Signal, params: AnalysisParams, plosives: list[Plosive]) -> float:
    """Spitzenpegel ohne die Plosivspitzen.

    Wer den Gain gegen ``peak_dbfs`` einstellt, steuert gegen einen Luftstoß
    aus und nimmt die Sprache mehrere Dezibel zu leise auf.
    """
    if len(signal.samples) == 0:
        return FLOOR_DB
    if not plosives:
        return peak_dbfs(signal.samples)

    mask = np.ones(len(signal.samples), dtype=bool)
    half = max(4, round(0.015 * signal.sample_rate))
    for plosive in plosives:
        index = round(plosive.time_s * signal.sample_rate)
        mask[max(0, index - half) : index + half] = False
    remaining = signal.samples[mask]
    if len(remaining) == 0:
        return peak_dbfs(signal.samples)
    return peak_dbfs(remaining)


def noise_floor_dbfs(signal: Signal, region: tuple[float, float]) -> float:
    """Rauschteppich im ausdrücklich übergebenen Bereich.

    Die Bibliothek sucht sich keine Pause selbst; welcher Abschnitt eine echte
    Sprechpause ist, weiß nur der Nutzer.
    """
    start, end = region
    a = max(0, round(start * signal.sample_rate))
    b = min(len(signal.samples), round(end * signal.sample_rate))
    if b <= a:
        raise ValueError(f"Rauschbereich {region} liegt außerhalb des Signals.")
    return rms_dbfs(signal.samples[a:b])
