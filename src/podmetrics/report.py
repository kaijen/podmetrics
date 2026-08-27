"""measure() — setzt die Einzelmodule zusammen.

Enthält selbst keine DSP-Logik. Wenn hier gerechnet wird statt zusammengebaut,
fehlt woanders ein Modul.
"""

from __future__ import annotations

from . import gating, levels, loudness, spectrum
from .io import slice_region
from .models import AnalysisParams, Measurement, Signal


def measure(
    signal: Signal,
    *,
    params: AnalysisParams | None = None,
    noise_region: tuple[float, float] | None = None,
    region: tuple[float, float] | None = None,
) -> Measurement:
    """Misst ein Signal und setzt die Kennwerte zu einem Measurement zusammen.

    ``noise_region`` ist die Sprechpause, in der der Rauschteppich gemessen
    wird; ohne sie bleibt das Feld leer. ``region`` ist der ausgewertete
    Sprachabschnitt. Beide Zeitangaben beziehen sich auf das übergebene
    Signal, nicht aufeinander.
    """
    params = params or AnalysisParams()

    # Der Rauschteppich wird am ungeschnittenen Signal gemessen: Die Pause
    # liegt in aller Regel außerhalb des ausgewerteten Sprachabschnitts.
    noise = levels.noise_floor_dbfs(signal, noise_region) if noise_region is not None else None

    part = slice_region(signal, region)
    speech = gating.speech_samples(part, params)
    plosives = levels.find_plosives(part, params)
    median, p10, p90 = levels.speech_percentiles(part, params)
    short_values, short_times = loudness.short_term(part, params)
    hz, band_db = spectrum.third_octave_bands(speech, part.sample_rate, params)
    comb_spacing, comb_depth = spectrum.detect_comb(speech, part.sample_rate, params)

    return Measurement(
        sample_rate=part.sample_rate,
        channel=part.channel,
        duration_s=part.duration_s,
        peak_dbfs=levels.peak_dbfs(part.samples),
        peak_speech_dbfs=levels.peak_speech_dbfs(part, params, plosives),
        true_peak_dbtp=levels.true_peak_dbtp(part.samples, params.true_peak_oversampling),
        crest_db=levels.crest_db(speech) if len(speech) else levels.crest_db(part.samples),
        clipped_samples=levels.clipped_samples(part.samples),
        lufs_i=loudness.integrated_lufs(part),
        lufs_i_reliable=loudness.is_reliable(part, params),
        short_term_lufs=short_values,
        short_term_times_s=short_times,
        block_balance_db=loudness.block_balance_db(part),
        speech_median_dbfs=median,
        speech_p10_dbfs=p10,
        speech_p90_dbfs=p90,
        speech_ratio=gating.speech_ratio(part, params),
        third_octave_hz=hz,
        third_octave_db=band_db,
        comb_spacing_hz=comb_spacing,
        comb_depth_db=comb_depth,
        plosives=plosives,
        noise_floor_dbfs=noise,
        noise_region_s=noise_region,
        analysis_region_s=region,
        source_sha256=part.source_sha256,
        params=params,
    )
