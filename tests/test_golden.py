"""Golden Test.

Ein deterministisch erzeugtes Signal, dessen vollständiges Measurement als
JSON im Repository liegt. Der Test schlägt fehl, sobald sich ein Rechenweg
unbeabsichtigt ändert — genau der Fall, der sonst erst Monate später als
unerklärliche Abweichung auffällt.

Neu erzeugen nach einer *beabsichtigten* Änderung:

    python -m tests.test_golden
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from helpers import SR, make_signal
from podmetrics.models import Measurement
from podmetrics.report import measure

GOLDEN = Path(__file__).parent / "data" / "golden_measurement.json"

# Toleranz für Fließkommaunterschiede zwischen BLAS-Bibliotheken und
# numpy-Versionen. Größer als das Rauschen der Plattform, kleiner als jede
# Änderung, die einen Rechenweg wirklich betrifft.
TOLERANCE = 1e-6


def golden_signal():
    """Sprachähnlich, mit Pause und einem Plosiv. Fester Seed, feste Länge."""
    rng = np.random.default_rng(20260827)
    n = 35 * SR
    t = np.arange(n) / SR
    x = 0.25 * np.sin(2 * np.pi * 180 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.9 * t))
    x += 0.03 * rng.normal(0.0, 1.0, n)
    pause = slice(int(10 * SR), int(13 * SR))
    x[pause] = 3e-4 * rng.normal(0.0, 1.0, pause.stop - pause.start)
    burst = slice(int(20 * SR), int(20 * SR) + int(0.02 * SR))
    x[burst] += 0.6 * np.hanning(burst.stop - burst.start) * np.sin(2 * np.pi * 70 * t[burst])
    return make_signal(x)


def golden_measurement() -> Measurement:
    return measure(golden_signal(), noise_region=(10.5, 12.5))


def _flatten(value, prefix=""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _flatten(item, f"{prefix}.{key}" if prefix else key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _flatten(item, f"{prefix}[{index}]")
    else:
        yield prefix, value


@pytest.mark.skipif(not GOLDEN.is_file(), reason="Golden-Datei fehlt")
def test_measurement_matches_the_golden_file():
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    actual = golden_measurement().to_dict()

    expected_flat = dict(_flatten(expected))
    actual_flat = dict(_flatten(actual))
    assert set(expected_flat) == set(actual_flat), "Felder haben sich geändert."

    for key, want in expected_flat.items():
        got = actual_flat[key]
        if isinstance(want, bool) or not isinstance(want, (int, float)):
            assert got == want, key
        else:
            assert got == pytest.approx(want, rel=TOLERANCE, abs=TOLERANCE), key


def test_golden_measurement_survives_a_roundtrip():
    measurement = golden_measurement()
    assert Measurement.from_dict(measurement.to_dict()) == measurement


if __name__ == "__main__":
    GOLDEN.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN.write_text(
        json.dumps(golden_measurement().to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{GOLDEN} neu geschrieben.")
