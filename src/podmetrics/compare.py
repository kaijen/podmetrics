"""Deltas und Differenzkurven gegen eine Referenz."""

from __future__ import annotations

import numpy as np

from .models import Comparison, Delta, Measurement


def _delta(measurement: Measurement, reference: Measurement) -> Delta:
    noise = None
    if measurement.noise_floor_dbfs is not None and reference.noise_floor_dbfs is not None:
        noise = measurement.noise_floor_dbfs - reference.noise_floor_dbfs
    return Delta(
        peak_db=measurement.peak_dbfs - reference.peak_dbfs,
        true_peak_db=measurement.true_peak_dbtp - reference.true_peak_dbtp,
        lufs_i_db=measurement.lufs_i - reference.lufs_i,
        crest_db=measurement.crest_db - reference.crest_db,
        speech_median_db=measurement.speech_median_dbfs - reference.speech_median_dbfs,
        p10_p90_db=measurement.p10_p90_db - reference.p10_p90_db,
        noise_floor_db=noise,
    )


def third_octave_difference(
    measurement: Measurement, reference: Measurement
) -> tuple[list[float], list[float]]:
    """Differenzkurve auf den gemeinsamen Terzbändern beider Messungen."""
    shared = [hz for hz in measurement.third_octave_hz if hz in set(reference.third_octave_hz)]
    if not shared:
        return [], []
    mine = dict(zip(measurement.third_octave_hz, measurement.third_octave_db, strict=True))
    theirs = dict(zip(reference.third_octave_hz, reference.third_octave_db, strict=True))
    return shared, [mine[hz] - theirs[hz] for hz in shared]


def compare(measurements: list[Measurement], *, reference: Measurement) -> Comparison:
    """Kennwert-Deltas und Terzband-Differenzkurven gegen die Referenz.

    Verwaltet nichts und merkt sich nichts: Die Referenz wird bei jedem Aufruf
    übergeben. Die Zuordnung läuft über die Reihenfolge der Eingabeliste; wer
    Namen braucht, hält sie außerhalb.
    """
    if not measurements:
        raise ValueError("Ohne Messungen gibt es nichts zu vergleichen.")

    warnings: list[str] = []
    curves: list[list[float]] = []
    shared_hz: list[float] = []

    for index, item in enumerate(measurements):
        if item.sample_rate != reference.sample_rate:
            warnings.append(
                f"Messung {index}: Samplerate {item.sample_rate} weicht von der "
                f"Referenz ({reference.sample_rate}) ab."
            )
        if item.channel != reference.channel:
            warnings.append(
                f"Messung {index}: Kanal {item.channel} weicht von der Referenz "
                f"({reference.channel}) ab."
            )
        if not item.lufs_i_reliable or not reference.lufs_i_reliable:
            warnings.append(f"Messung {index}: LUFS-I ist unzuverlässig, zu kurzes Material.")
        hz, curve = third_octave_difference(item, reference)
        if hz and not shared_hz:
            shared_hz = hz
        curves.append(curve if hz == shared_hz else [])

    try:
        reference_index = measurements.index(reference)
    except ValueError:
        reference_index = -1

    return Comparison(
        reference_index=reference_index,
        deltas=[_delta(m, reference) for m in measurements],
        third_octave_hz=shared_hz,
        third_octave_diff_db=curves,
        warnings=sorted(set(warnings)),
    )


def drift_db(measurement: Measurement) -> float:
    """Steigung des Short-Term-Verlaufs über die gesamte Dauer, in dB.

    Trennt einen wandernden Mikrofonabstand von lauten und leisen Sätzen: Beide
    erzeugen dieselbe P10–P90-Spanne, aber nur der Abstand driftet.
    """
    values = measurement.short_term_lufs
    times = measurement.short_term_times_s
    if len(values) < 4:
        return 0.0
    slope, _ = np.polyfit(times, values, 1)
    return float(abs(slope) * (times[-1] - times[0]))
