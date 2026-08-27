"""Fixtures. Die Bausteine stehen in helpers.py."""

from __future__ import annotations

import numpy as np
import pytest

from helpers import SR, make_signal
from podmetrics.models import Signal


@pytest.fixture
def sine() -> Signal:
    """Sinus mit Amplitude 0,5 — Peak −6,02 dBFS, RMS −9,03 dBFS."""
    t = np.arange(3 * SR) / SR
    return make_signal(0.5 * np.sin(2 * np.pi * 440 * t))


@pytest.fixture
def sine_with_pause() -> Signal:
    """Eine Sekunde Ton, eine Sekunde Stille, eine Sekunde Ton."""
    t = np.arange(SR) / SR
    tone = 0.5 * np.sin(2 * np.pi * 440 * t)
    return make_signal(np.concatenate([tone, np.zeros(SR), tone]))


@pytest.fixture
def white_noise() -> Signal:
    """Weißes Rauschen bekannter Leistung, lang genug für belastbares LUFS-I."""
    rng = np.random.default_rng(20260827)
    return make_signal(rng.normal(0.0, 0.1, 40 * SR))
