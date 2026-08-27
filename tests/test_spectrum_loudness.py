"""Spektrum und Lautheit."""

from __future__ import annotations

import numpy as np
import pytest

from helpers import SR, make_signal
from podmetrics import loudness, spectrum
from podmetrics.models import AnalysisParams


def test_third_octave_curve_is_normalised(white_noise):
    hz, db = spectrum.third_octave_bands(white_noise.samples, SR, AnalysisParams())
    assert len(hz) == len(db) > 10
    # Auf den eigenen Mittelwert normiert: unabhängig vom Aufnahmegain.
    assert float(np.mean(db)) == pytest.approx(0.0, abs=1e-9)


def test_third_octave_curve_ignores_gain(white_noise):
    params = AnalysisParams()
    _, quiet = spectrum.third_octave_bands(white_noise.samples * 0.01, SR, params)
    _, loud = spectrum.third_octave_bands(white_noise.samples, SR, params)
    assert np.allclose(quiet, loud, atol=1e-9)


def test_third_octave_shows_a_boosted_band(white_noise):
    t = np.arange(len(white_noise.samples)) / SR
    boosted = white_noise.samples + 0.3 * np.sin(2 * np.pi * 1000 * t)
    hz, db = spectrum.third_octave_bands(boosted, SR, AnalysisParams())
    assert db[hz.index(1000.0)] == max(db)


def test_comb_filter_spacing_matches_delay(white_noise):
    # Eine Kopie mit 1 ms Verzögerung erzeugt Einbrüche alle 1000 Hz.
    delay = int(0.001 * SR)
    combed = white_noise.samples.copy()
    combed[delay:] += 0.9 * white_noise.samples[:-delay]
    spacing, depth = spectrum.detect_comb(combed, SR, AnalysisParams())
    assert spacing == pytest.approx(1000.0, rel=0.1)
    assert depth is not None and depth >= AnalysisParams().comb_min_depth_db


def test_no_comb_in_plain_noise(white_noise):
    assert spectrum.detect_comb(white_noise.samples, SR, AnalysisParams()) == (None, None)


def test_lufs_scales_with_gain(white_noise):
    quiet = make_signal(white_noise.samples * 0.5)
    difference = loudness.integrated_lufs(white_noise) - loudness.integrated_lufs(quiet)
    # Halbe Amplitude sind 6,02 dB weniger.
    assert difference == pytest.approx(6.0206, abs=0.05)


def test_short_material_is_marked_unreliable():
    params = AnalysisParams()
    short = make_signal(np.random.default_rng(1).normal(0, 0.1, 5 * SR))
    assert not loudness.is_reliable(short, params)
    # Gemessen wird trotzdem — nicht verweigert.
    assert np.isfinite(loudness.integrated_lufs(short))


def test_long_material_is_reliable(white_noise):
    assert loudness.is_reliable(white_noise, AnalysisParams())


def test_block_balance_detects_a_level_step(white_noise):
    samples = white_noise.samples.copy()
    samples[len(samples) // 2 :] *= 0.5  # zweite Hälfte 6 dB leiser
    stepped = make_signal(samples)
    assert loudness.block_balance_db(stepped) > 3.0
    assert loudness.block_balance_db(white_noise) < 1.0
