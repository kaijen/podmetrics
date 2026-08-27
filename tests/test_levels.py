"""Rechenfunktionen gegen analytisch bekannte Ergebnisse."""

from __future__ import annotations

import numpy as np
import pytest

from helpers import SR, make_signal
from podmetrics import levels
from podmetrics.gating import speech_ratio, speech_segments
from podmetrics.models import AnalysisParams


def test_peak_of_known_sine(sine):
    # Amplitude 0,5 → 20·log10(0,5) = −6,02 dBFS
    assert levels.peak_dbfs(sine.samples) == pytest.approx(-6.0206, abs=1e-3)


def test_rms_of_known_sine(sine):
    # Effektivwert eines Sinus ist A/√2 → −9,03 dBFS
    assert levels.rms_dbfs(sine.samples) == pytest.approx(-9.0309, abs=1e-3)


def test_crest_of_sine_is_three_db(sine):
    assert levels.crest_db(sine.samples) == pytest.approx(3.0103, abs=1e-3)


def test_rms_of_white_noise_matches_sigma(white_noise):
    # Bei Mittelwert 0 ist das RMS gleich der Standardabweichung.
    assert levels.rms_dbfs(white_noise.samples) == pytest.approx(20 * np.log10(0.1), abs=0.05)


def test_silence_returns_floor():
    assert levels.peak_dbfs(np.zeros(1000)) == levels.FLOOR_DB
    assert levels.rms_dbfs(np.zeros(1000)) == levels.FLOOR_DB


def test_true_peak_at_least_sample_peak(sine):
    peak = levels.peak_dbfs(sine.samples)
    assert levels.true_peak_dbtp(sine.samples) >= peak - 1e-6


def test_true_peak_finds_intersample_overshoot():
    # Ein Signal knapp unter Vollaussteuerung, dessen Rekonstruktion zwischen
    # den Abtastwerten höher ausschlägt als jeder einzelne davon.
    t = np.arange(SR) / SR
    x = 0.99 * np.sin(2 * np.pi * (SR / 4 - 30) * t + np.pi / 4)
    assert levels.true_peak_dbtp(x) > levels.peak_dbfs(x)


def test_clipping_is_counted():
    x = np.array([0.1, 1.0, -1.0, 0.2, 0.999999])
    assert levels.clipped_samples(x) == 3


def test_gating_finds_two_segments(sine_with_pause):
    segments = speech_segments(sine_with_pause, AnalysisParams())
    assert len(segments) == 2
    # Erstes Segment beginnt am Anfang, zweites nach der Pause.
    assert segments[0][0] == 0
    assert segments[1][0] / SR == pytest.approx(2.0, abs=0.15)


def test_gating_drops_silence_from_ratio(sine_with_pause):
    ratio = speech_ratio(sine_with_pause, AnalysisParams())
    # Zwei von drei Sekunden sind Ton; die Fensterlänge verschmiert die Kanten.
    assert 0.6 < ratio < 0.85


def test_gating_on_pure_silence_returns_nothing():
    silence = make_signal(np.zeros(SR))
    assert speech_segments(silence, AnalysisParams()) == []


def test_plosive_is_recognised_and_excluded_from_speech_peak():
    # Sprachähnlicher Grundton plus ein kurzer Tieftonstoß, wie ihn ein P
    # erzeugt: fast die gesamte Energie unterhalb von 120 Hz.
    t = np.arange(5 * SR) / SR
    x = 0.2 * np.sin(2 * np.pi * 200 * t)
    burst = slice(int(2.0 * SR), int(2.0 * SR) + int(0.02 * SR))
    window = np.hanning(burst.stop - burst.start)
    x[burst] += 0.75 * window * np.sin(2 * np.pi * 70 * t[burst])

    signal = make_signal(x)
    params = AnalysisParams()
    plosives = levels.find_plosives(signal, params)
    assert plosives, "Der Tieftonstoß muss als Plosiv erkannt werden."
    assert plosives[0].low_energy_share > plosives[0].block_share
    assert plosives[0].time_s == pytest.approx(2.01, abs=0.05)

    # Der Sprachpeak liegt deutlich unter dem Gesamtpeak — genau deshalb ist
    # der Gesamtpeak kein Maßstab für den Gain.
    speech_peak = levels.peak_speech_dbfs(signal, params, plosives)
    assert speech_peak < levels.peak_dbfs(signal.samples) - 3.0


def test_clean_speech_has_no_plosives():
    t = np.arange(5 * SR) / SR
    x = 0.2 * np.sin(2 * np.pi * 200 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 3 * t))
    assert levels.find_plosives(make_signal(x), AnalysisParams()) == []


def test_noise_floor_needs_a_region(white_noise):
    value = levels.noise_floor_dbfs(white_noise, (1.0, 2.0))
    assert value == pytest.approx(20 * np.log10(0.1), abs=0.2)
