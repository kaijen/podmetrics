"""podmetrics — Messung von Sprachaufnahmen.

Die hier exportierten Namen sind der Vertrag. Alles darunter ist privat und
darf ohne Versionssprung geändert werden. Neue Funktionen kommen erst in den
Namensraum, wenn sie stabil sind.
"""

from __future__ import annotations

from .advice import advise, check_reference
from .compare import compare
from .io import load
from .loudness import gain_for_target_lufs
from .models import (
    Advice,
    AnalysisParams,
    Comparison,
    Delta,
    Evidence,
    Expectation,
    Measurement,
    Plosive,
    ReferenceCheck,
    Signal,
    Suggestion,
    TargetProfile,
)
from .report import measure

__version__ = "0.1.0"

__all__ = [
    "Advice",
    "AnalysisParams",
    "Comparison",
    "Delta",
    "Evidence",
    "Expectation",
    "Measurement",
    "Plosive",
    "ReferenceCheck",
    "Signal",
    "Suggestion",
    "TargetProfile",
    "__version__",
    "advise",
    "check_reference",
    "compare",
    "gain_for_target_lufs",
    "load",
    "measure",
]
