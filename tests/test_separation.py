"""Die Trennung von Messung und Meinung.

Gemessen wird immer, geraten nur auf Anforderung. Diese Trennung geht sonst
als bequeme Kleinigkeit verloren.
"""

from __future__ import annotations

import inspect
from dataclasses import fields

import pytest

from helpers import speech_like
from podmetrics import advice, cli, compare, models, report
from podmetrics.models import Advice, Measurement, Suggestion


def test_measurement_carries_no_advice():
    names = {f.name for f in fields(Measurement)}
    for forbidden in ("advice", "suggestions", "recommendations", "tips"):
        assert forbidden not in names


def test_measure_returns_only_a_measurement():
    result = report.measure(speech_like(seconds=32.0), noise_region=(12.5, 14.5))
    assert isinstance(result, Measurement)
    assert not any(isinstance(v, (Advice, Suggestion)) for v in result.to_dict().values())


def test_batch_command_takes_no_advice_options():
    """Wer für zwanzig Dateien Ratschläge ausgibt, bekommt eine Textwand statt
    einer Tabelle, und die Empfehlungen widersprechen einander."""
    parameters = set(inspect.signature(cli.batch).parameters)
    assert not parameters & {"topic", "advise", "processed", "delivery"}


def test_measure_command_takes_no_advice_options():
    parameters = set(inspect.signature(cli.measure_cmd).parameters)
    assert not parameters & {"topic", "advise", "processed"}


def test_advice_layer_touches_no_samples():
    """advice kennt models und sonst nichts — insbesondere kein Signal, kein
    soundfile, kein scipy. Ein Import von numpy dort ist ein Warnzeichen."""
    source = inspect.getsource(advice)
    for forbidden in ("import numpy", "import scipy", "import soundfile", "from .io"):
        assert forbidden not in source, forbidden
    assert "Signal" not in {name for name in dir(advice) if not name.startswith("_")}


def test_models_knows_nobody_in_this_package():
    source = inspect.getsource(models)
    assert "from ." not in source and "from podmetrics" not in source


@pytest.mark.parametrize("module", [advice, compare, report])
def test_compute_modules_do_not_import_each_other(module):
    source = inspect.getsource(module)
    # report darf zusammenbauen, die anderen nicht.
    if module is report:
        return
    for other in ("from .report", "from .cli"):
        assert other not in source


def test_public_contract_is_explicit():
    import podmetrics

    assert set(podmetrics.__all__) >= {
        "load",
        "measure",
        "compare",
        "gain_for_target_lufs",
        "advise",
        "check_reference",
        "Signal",
        "AnalysisParams",
        "Measurement",
        "Comparison",
        "TargetProfile",
        "Advice",
        "Suggestion",
        "ReferenceCheck",
    }
    for name in podmetrics.__all__:
        assert hasattr(podmetrics, name), name
