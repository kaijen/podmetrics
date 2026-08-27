"""Laden, Kanalwahl, Resampling."""

from __future__ import annotations

import hashlib
from fractions import Fraction
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from .models import Signal

_HASH_CHUNK = 1 << 20


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(_HASH_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def load(
    path: str | Path,
    *,
    channel: int = 0,
    target_rate: int | None = None,
) -> Signal:
    """Lädt eine Audiodatei und gibt genau einen Kanal zurück.

    Es wird nicht gemischt: Die Summierung zweier Sprecherkanäle erzeugt
    Kammfilter, die im Messergebnis wie ein Aufnahmefehler aussehen. Welcher
    Kanal gemeint ist, sagt der Aufrufer.
    """
    path = Path(path)
    data, sample_rate = sf.read(str(path), dtype="float64", always_2d=True)
    source_channels = data.shape[1]
    if not 0 <= channel < source_channels:
        raise ValueError(f"Kanal {channel} gibt es nicht, die Datei hat {source_channels}.")
    samples = np.ascontiguousarray(data[:, channel])

    if target_rate is not None and target_rate != sample_rate:
        ratio = Fraction(target_rate, sample_rate).limit_denominator(1000)
        samples = resample_poly(samples, ratio.numerator, ratio.denominator)
        sample_rate = target_rate

    return Signal(
        samples=samples,
        sample_rate=int(sample_rate),
        channel=channel,
        source_channels=source_channels,
        source_sha256=file_sha256(path),
    )


def slice_region(signal: Signal, region: tuple[float, float] | None) -> Signal:
    """Zeitausschnitt in Sekunden. Ohne Angabe unverändert."""
    if region is None:
        return signal
    start, end = region
    if end <= start:
        raise ValueError(f"Bereich {region} ist leer oder rückwärts.")
    a = max(0, round(start * signal.sample_rate))
    b = min(len(signal.samples), round(end * signal.sample_rate))
    if b <= a:
        raise ValueError(f"Bereich {region} liegt außerhalb des Signals.")
    return Signal(
        samples=signal.samples[a:b],
        sample_rate=signal.sample_rate,
        channel=signal.channel,
        source_channels=signal.source_channels,
        source_sha256=signal.source_sha256,
    )
