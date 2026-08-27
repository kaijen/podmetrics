"""Serialisierung. Jedes Modell muss den Weg durch JSON überstehen."""

from __future__ import annotations

import json

import pytest

from helpers import a_plosive, bands, make_measurement
from podmetrics.models import (
    Advice,
    AnalysisParams,
    Comparison,
    Delta,
    Evidence,
    Expectation,
    Measurement,
    ReferenceCheck,
    Suggestion,
    TargetProfile,
)

CASES = [
    AnalysisParams(),
    TargetProfile.raw(),
    TargetProfile.delivery(),
    a_plosive(),
    Evidence(field="peak_dbfs", value=-8.0, threshold=-6.0, unit="dBFS"),
    Expectation(field="peak_dbfs", direction="sinkt", amount=2.0, unit="dB"),
    Delta(
        peak_db=1.0,
        true_peak_db=1.1,
        lufs_i_db=-0.5,
        crest_db=0.2,
        speech_median_db=0.3,
        p10_p90_db=-1.0,
        noise_floor_db=None,
    ),
    ReferenceCheck(suitable=False, reasons=["zu kurz"], checked=["Dauer"]),
]


@pytest.mark.parametrize("model", CASES, ids=lambda m: type(m).__name__)
def test_roundtrip(model):
    restored = type(model).from_dict(model.to_dict())
    assert restored == model


def test_measurement_roundtrip():
    measurement = make_measurement(plosives=[a_plosive()], third_octave_db=bands(hz_125=4.0))
    assert Measurement.from_dict(measurement.to_dict()) == measurement


def test_comparison_roundtrip():
    comparison = Comparison(
        reference_index=0,
        deltas=[CASES[6]],
        third_octave_hz=[100.0, 125.0],
        third_octave_diff_db=[[0.0, 1.0]],
        warnings=["Samplerate weicht ab"],
    )
    assert Comparison.from_dict(comparison.to_dict()) == comparison


def test_advice_roundtrip():
    advice = Advice(
        profile=TargetProfile.raw(),
        material="raw",
        had_reference=True,
        suggestions=[
            Suggestion(
                id="eq.band_125hz",
                topic="eq",
                severity="low",
                order=1,
                title="t",
                detail="d",
                evidence=[CASES[4]],
                expected=[CASES[5]],
                parameters={"gain_db": -3.0},
            )
        ],
        skipped=["nichts"],
    )
    assert Advice.from_dict(advice.to_dict()) == advice


def test_serialisation_is_plain_python():
    """Keine numpy-Skalare, keine Arrays — sonst scheitert die JSON-Kodierung
    beim Konsumenten an Stellen, die hier nie auffallen."""
    payload = make_measurement(plosives=[a_plosive()]).to_dict()
    text = json.dumps(payload)  # wirft, wenn ein numpy-Typ durchgerutscht ist
    assert json.loads(text)["peak_dbfs"] == payload["peak_dbfs"]

    def walk(value):
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        else:
            assert type(value) in (int, float, str, bool, type(None)), type(value)

    walk(payload)


def test_measurement_derives_span_and_snr():
    measurement = make_measurement(
        speech_p10_dbfs=-29.0,
        speech_p90_dbfs=-13.0,
        speech_median_dbfs=-21.0,
        noise_floor_dbfs=-58.0,
    )
    assert measurement.p10_p90_db == pytest.approx(16.0)
    assert measurement.snr_db == pytest.approx(37.0)


def test_snr_is_none_without_noise_region():
    assert make_measurement(noise_floor_dbfs=None).snr_db is None


def test_profiles_differ_where_it_matters():
    raw, delivery = TargetProfile.raw(), TargetProfile.delivery()
    # Wer roh auf Veröffentlichungspegel aufnimmt, hat beim ersten Lacher
    # keinen Headroom mehr.
    assert raw.lufs_i < delivery.lufs_i
    assert raw.peak_max_dbfs < delivery.peak_max_dbfs
    assert delivery.lufs_i == -19.0  # mono gemessen, nicht die Stereo-Zahl −16
