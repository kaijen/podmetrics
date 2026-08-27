"""Datentypen. Kennt niemanden außer numpy.

Alle Modelle sind frozen Dataclasses mit ``to_dict()`` und ``from_dict()``.
Serialisierung liefert reine Python-Typen — floats und Listen, keine
numpy-Skalare und keine Arrays. Sonst scheitert die JSON-Kodierung beim
Konsumenten an Stellen, die hier nie auffallen.
"""

from __future__ import annotations

import types
import typing
from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any, ClassVar, TypeVar, get_args, get_origin

import numpy as np

# Steigt, wenn Felder wegfallen oder ihre Bedeutung sich ändert. Die Webapp
# speichert Messungen dauerhaft und muss alte Datensätze erkennen können.
SCHEMA_VERSION = 1

# Steigt, sobald sich Regeln, Schwellen oder die Bedeutung einer
# Suggestion-ID ändern. Eine ID wird nie wiederverwendet.
RULESET_VERSION = 1

T = TypeVar("T", bound="Model")


def _to_plain(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _to_plain(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, np.ndarray):
        return [_to_plain(v) for v in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (list, tuple)):
        return [_to_plain(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_plain(v) for k, v in value.items()}
    return value


def _from_plain(annotation: Any, value: Any) -> Any:
    origin = get_origin(annotation)

    # Optional[X] / X | None
    if origin in (typing.Union, types.UnionType):
        args = [a for a in get_args(annotation) if a is not type(None)]
        if value is None:
            return None
        return _from_plain(args[0], value)

    if origin is list:
        (item_type,) = get_args(annotation) or (Any,)
        return [_from_plain(item_type, v) for v in value]

    if origin is tuple:
        members = get_args(annotation)
        if len(members) == 2 and members[1] is Ellipsis:
            return tuple(_from_plain(members[0], v) for v in value)
        return tuple(_from_plain(t, v) for t, v in zip(members, value, strict=True))

    if origin is dict:
        members = get_args(annotation)
        value_type = members[1] if len(members) == 2 else Any
        return {k: _from_plain(value_type, v) for k, v in value.items()}

    if is_dataclass(annotation) and isinstance(annotation, type):
        return annotation.from_dict(value)  # type: ignore[attr-defined]

    return value


@dataclass(frozen=True)
class Model:
    """Gemeinsame Serialisierung für alle Modelle."""

    def to_dict(self) -> dict[str, Any]:
        return typing.cast(dict[str, Any], _to_plain(self))

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        hints = typing.get_type_hints(cls)
        kwargs = {
            f.name: _from_plain(hints[f.name], data[f.name])
            for f in fields(cls)
            if f.name in data
        }
        return cls(**kwargs)


@dataclass(frozen=True)
class AnalysisParams(Model):
    """Fensterlängen, Schwellen und Bandgrenzen.

    Defaults werden nie stillschweigend geändert; jede Änderung entwertet alle
    früheren Vergleiche und ist ein Breaking Change, auch ohne Signaturänderung.
    """

    rms_window_ms: float = 200.0
    rms_overlap: float = 0.5
    gate_threshold_dbfs: float = -45.0
    gate_min_segment_ms: float = 100.0
    short_term_window_s: float = 3.0
    true_peak_oversampling: int = 4
    lufs_min_duration_s: float = 30.0
    third_octave_low_hz: float = 40.0
    third_octave_high_hz: float = 16000.0
    # Ein Plosiv ist eine Spitze, deren Energieanteil unter plosive_split_hz
    # weit über dem des umgebenden Sprachblocks liegt. Der Faktor stammt aus
    # der Messreihe: 95,6 % gegen 28,7 % im Durchschnitt, also gut das
    # Dreifache. 2.0 lässt Raum nach unten, ohne normale Silben zu treffen.
    plosive_split_hz: float = 120.0
    plosive_share_factor: float = 2.0
    plosive_min_share: float = 0.6
    welch_segment_s: float = 0.093
    # Kammfilter: Einbrüche in gleichmäßigem Frequenzabstand. Unterhalb von
    # 3 dB Tiefe ist das Muster von normaler Spektralstruktur nicht zu trennen.
    comb_min_depth_db: float = 3.0
    comb_min_notches: int = 4


@dataclass(frozen=True)
class Signal:
    """Ein Kanal als float64 in −1..1.

    Kein ``to_dict()``: Wer Samples durch JSON schickt, hat sich vertan.
    """

    samples: np.ndarray
    sample_rate: int
    channel: int
    source_channels: int
    source_sha256: str

    @property
    def duration_s(self) -> float:
        return len(self.samples) / self.sample_rate


@dataclass(frozen=True)
class Plosive(Model):
    time_s: float
    peak_dbfs: float
    low_energy_share: float
    block_share: float


@dataclass(frozen=True)
class Measurement(Model):
    sample_rate: int
    channel: int
    duration_s: float

    peak_dbfs: float
    peak_speech_dbfs: float
    true_peak_dbtp: float
    crest_db: float
    clipped_samples: int

    lufs_i: float
    lufs_i_reliable: bool
    short_term_lufs: list[float]
    short_term_times_s: list[float]
    block_balance_db: float

    speech_median_dbfs: float
    speech_p10_dbfs: float
    speech_p90_dbfs: float
    speech_ratio: float

    third_octave_hz: list[float]
    third_octave_db: list[float]
    comb_spacing_hz: float | None
    comb_depth_db: float | None

    plosives: list[Plosive]

    noise_floor_dbfs: float | None
    noise_region_s: tuple[float, float] | None
    analysis_region_s: tuple[float, float] | None

    source_sha256: str
    params: AnalysisParams
    schema_version: int = SCHEMA_VERSION

    @property
    def p10_p90_db(self) -> float:
        return self.speech_p90_dbfs - self.speech_p10_dbfs

    @property
    def snr_db(self) -> float | None:
        if self.noise_floor_dbfs is None:
            return None
        return self.speech_median_dbfs - self.noise_floor_dbfs


@dataclass(frozen=True)
class Delta(Model):
    peak_db: float
    true_peak_db: float
    lufs_i_db: float
    crest_db: float
    speech_median_db: float
    p10_p90_db: float
    noise_floor_db: float | None


@dataclass(frozen=True)
class Comparison(Model):
    reference_index: int
    deltas: list[Delta]
    third_octave_hz: list[float]
    third_octave_diff_db: list[list[float]]
    warnings: list[str]
    schema_version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class TargetProfile(Model):
    """Die Ziele, gegen die empfohlen wird.

    Jeder Defaultwert hat eine Begründung. Ein Zielwert ohne Herkunft wird nach
    drei Monaten nicht mehr hinterfragt, sondern geglaubt. Woher die Zahlen
    stammen, steht in der Dokumentation unter „Zielwerte“ und „Messreihen“.
    """

    name: str

    lufs_i: float
    lufs_i_tolerance_db: float
    true_peak_max_dbtp: float
    peak_max_dbfs: float

    p10_p90_range_db: tuple[float, float]
    crest_range_db: tuple[float, float]
    snr_min_db: float
    noise_floor_max_dbfs: float
    noise_floor_compressed_max_dbfs: float
    block_balance_max_db: float

    eq_max_gain_db: float = 4.0
    eq_max_filters: int = 4
    eq_highpass_hz: float = 80.0

    comp_target_range_db: float = 15.0
    comp_threshold_below_median_db: float = 3.0
    comp_ratio: float = 3.0
    comp_attack_ms: float = 8.0
    comp_release_ms: float = 110.0
    comp_knee_db: float = 3.0

    # Schwellen der Empfehlungsregeln, in dB gegen die Referenz.
    band_low_threshold_db: float = 3.0
    band_high_threshold_db: float = 3.0
    band_strong_factor: float = 2.0
    drift_threshold_db: float = 3.0

    @classmethod
    def raw(cls) -> TargetProfile:
        """Rohaufnahme, pro Spur, ohne EQ und Kompressor."""
        return cls(
            name="raw",
            # Aus dem Peak-Ziel zurückgerechnet; Messreihe v010: −20,86.
            lufs_i=-22.0,
            lufs_i_tolerance_db=2.0,
            # Abstand zur Wandlergrenze, der auch Intersample-Spitzen überlebt.
            true_peak_max_dbtp=-3.0,
            # Reserve für Lacher. Headroom ist knapper als Rauschreserve.
            peak_max_dbfs=-6.0,
            # Messreihe v010: 18,5 dB unkomprimiert.
            p10_p90_range_db=(15.0, 19.0),
            crest_range_db=(12.0, 18.0),
            # Messreihe: Median −21, Rauschen −57,5 → 36,5 dB.
            snr_min_db=35.0,
            noise_floor_max_dbfs=-55.0,
            noise_floor_compressed_max_dbfs=-48.0,
            block_balance_max_db=1.0,
        )

    @classmethod
    def delivery(cls) -> TargetProfile:
        """Fertige Folge, einkanalig gemessen.

        −19 und nicht −16: podmetrics misst einen Kanal, BS.1770 summiert
        Kanalenergien. Die verbreiteten −16 LUFS beziehen sich auf Stereo.
        """
        return cls(
            name="delivery",
            lufs_i=-19.0,
            lufs_i_tolerance_db=1.0,
            true_peak_max_dbtp=-1.0,
            peak_max_dbfs=-1.5,
            # Messreihe v020: 15,4 dB nach Kompression.
            p10_p90_range_db=(14.0, 15.5),
            crest_range_db=(10.0, 15.0),
            snr_min_db=35.0,
            noise_floor_max_dbfs=-55.0,
            noise_floor_compressed_max_dbfs=-48.0,
            block_balance_max_db=1.0,
        )


@dataclass(frozen=True)
class Evidence(Model):
    field: str
    value: float
    threshold: float
    unit: str


@dataclass(frozen=True)
class Expectation(Model):
    field: str
    direction: str  # "sinkt" | "steigt" | "bleibt"
    amount: float
    unit: str


@dataclass(frozen=True)
class Suggestion(Model):
    id: str
    topic: str  # "position" | "eq" | "comp"
    severity: str  # "low" | "medium" | "high"
    order: int
    title: str
    detail: str
    evidence: list[Evidence] = field(default_factory=list)
    expected: list[Expectation] = field(default_factory=list)
    parameters: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Advice(Model):
    profile: TargetProfile
    material: str  # "raw" | "processed"
    had_reference: bool
    suggestions: list[Suggestion]
    skipped: list[str]
    chain_order: list[str] = field(
        default_factory=lambda: ["Hochpass", "EQ", "Kompressor", "Pegelangleichung"]
    )
    schema_version: int = SCHEMA_VERSION
    ruleset_version: int = RULESET_VERSION

    TOPICS: ClassVar[tuple[str, ...]] = ("position", "eq", "comp")


@dataclass(frozen=True)
class ReferenceCheck(Model):
    suitable: bool
    reasons: list[str]
    checked: list[str]
    schema_version: int = SCHEMA_VERSION
