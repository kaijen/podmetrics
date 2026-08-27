"""Welch-PSD, Terzbänder, Kammfilternachweis."""

from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks, welch

from .models import AnalysisParams


# Terzband-Mittenfrequenzen nach ISO 266, verankert auf 1 kHz.
def third_octave_centers(low_hz: float, high_hz: float) -> np.ndarray:
    n = np.arange(-30, 21)
    centers = 1000.0 * 2.0 ** (n / 3.0)
    return centers[(centers >= low_hz) & (centers <= high_hz)]


def psd(
    samples: np.ndarray, sample_rate: int, params: AnalysisParams
) -> tuple[np.ndarray, np.ndarray]:
    nperseg = int(2 ** round(np.log2(params.welch_segment_s * sample_rate)))
    nperseg = int(min(max(nperseg, 256), max(256, len(samples))))
    freqs, power = welch(samples, fs=sample_rate, nperseg=nperseg)
    return freqs, power


def third_octave_bands(
    samples: np.ndarray, sample_rate: int, params: AnalysisParams
) -> tuple[list[float], list[float]]:
    """Terzband-Energien in dB, auf ihren eigenen Mittelwert normiert.

    Die Normierung macht die Kurve unabhängig vom Aufnahmegain. Aussagekräftig
    ist die Differenzkurve zur Referenz, nicht die Absolutkurve.
    """
    if len(samples) < 64:
        return [], []
    freqs, power = psd(samples, sample_rate, params)
    centers = third_octave_centers(params.third_octave_low_hz, params.third_octave_high_hz)

    values = []
    kept = []
    for center in centers:
        low = center / 2 ** (1 / 6)
        high = center * 2 ** (1 / 6)
        band = power[(freqs >= low) & (freqs < high)]
        if band.size == 0 or not np.isfinite(band).all():
            continue
        energy = float(band.sum())
        if energy <= 0.0:
            continue
        kept.append(float(center))
        values.append(energy)

    if not values:
        return [], []
    db = 10.0 * np.log10(np.asarray(values))
    return kept, (db - db.mean()).tolist()


def band_level_db(
    centers: list[float], values: list[float], low_hz: float, high_hz: float
) -> float | None:
    """Mittlerer Pegel der Terzbänder zwischen low_hz und high_hz."""
    picked = [v for c, v in zip(centers, values, strict=True) if low_hz <= c <= high_hz]
    if not picked:
        return None
    return float(np.mean(picked))


def detect_comb(
    samples: np.ndarray, sample_rate: int, params: AnalysisParams
) -> tuple[float | None, float | None]:
    """Kammfilter aus der PSD nachweisen. Gibt (Abstand, Tiefe) zurück.

    Nicht aus Terzbändern: Deren Mittelung löscht genau die Einbrüche aus, die
    das Muster ausmachen. Die Signatur sind Einbrüche in gleichmäßigem
    Frequenzabstand; der Abstand nennt die Verzögerung der störenden Kopie,
    die Tiefe ihren Pegelabstand.
    """
    if len(samples) < 4096:
        return None, None
    freqs, power = psd(samples, sample_rate, params)
    usable = (freqs >= 100.0) & (freqs <= 8000.0) & (power > 0)
    if usable.sum() < 64:
        return None, None
    freqs = freqs[usable]
    db = 10.0 * np.log10(power[usable])

    # Grobe Hüllkurve abziehen, damit der Sprachformant nicht als Einbruch zählt.
    width = max(5, (len(db) // 24) | 1)
    kernel = np.ones(width) / width
    smooth = np.convolve(db, kernel, mode="same")
    detrended = db - smooth

    notches, properties = find_peaks(-detrended, prominence=params.comb_min_depth_db)
    if len(notches) < params.comb_min_notches:
        return None, None

    spacings = np.diff(freqs[notches])
    spacing = float(np.median(spacings))
    if spacing <= 0.0:
        return None, None
    # Ein Kamm ist regelmäßig. Streuen die Abstände stark, ist es keiner.
    if float(np.std(spacings) / spacing) > 0.25:
        return None, None

    depth = float(np.median(properties["prominences"]))
    return spacing, depth
