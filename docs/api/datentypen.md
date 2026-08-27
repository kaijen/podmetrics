# Datentypen

!!! warning "Entwurf"

    Die Feldlisten sind ein Vorschlag und noch nicht implementiert.

Alle Modelle sind frozen Dataclasses in `models.py` und tragen `to_dict()` und
`from_dict()`. `models` importiert nichts aus dem eigenen Paket.

Serialisierung liefert reine Python-Typen: floats und Listen, keine numpy-Skalare und keine
Arrays. Sonst scheitert die JSON-Kodierung beim Konsumenten an Stellen, die hier nie
auffallen.

## Signal

```python
@dataclass(frozen=True)
class Signal:
    samples: np.ndarray      # float64, −1..1, eindimensional
    sample_rate: int
    channel: int             # welcher Kanal der Quelle
    source_channels: int     # wie viele die Quelle hatte
    duration_s: float
```

`Signal` ist der einzige Typ, der ein numpy-Array enthält, und wird deshalb nicht
serialisiert. `to_dict()` fehlt hier absichtlich: Wer Samples durch JSON schickt, hat sich
vertan.

## AnalysisParams

```python
@dataclass(frozen=True)
class AnalysisParams:
    rms_window_ms: float = 200.0
    rms_overlap: float = 0.5
    gate_threshold_dbfs: float = -45.0
    gate_min_segment_ms: float = 100.0
    short_term_window_s: float = 3.0
    true_peak_oversampling: int = 4
    lufs_min_duration_s: float = 30.0
    third_octave_low_hz: float = 40.0
    third_octave_high_hz: float = 16000.0
```

Hält alle Fensterlängen, Schwellen und Bandgrenzen. **Defaults werden nie stillschweigend
geändert**; jede Änderung entwertet alle früheren Vergleiche und ist ein Breaking Change,
auch wenn sich keine Signatur ändert.

## Measurement

```python
@dataclass(frozen=True)
class Measurement:
    schema_version: int
    sample_rate: int
    channel: int
    duration_s: float

    peak_dbfs: float
    true_peak_dbtp: float
    crest_db: float

    lufs_i: float
    lufs_i_reliable: bool          # falsch unter lufs_min_duration_s
    short_term_lufs: list[float]   # 3 s gleitend
    short_term_times_s: list[float]

    speech_median_dbfs: float
    speech_p10_dbfs: float
    speech_p90_dbfs: float
    speech_ratio: float            # Anteil Sprache nach dem Gating

    third_octave_hz: list[float]
    third_octave_db: list[float]   # auf den eigenen Mittelwert normiert

    noise_floor_dbfs: float | None  # None ohne noise_region
    noise_region_s: tuple[float, float] | None

    params: AnalysisParams
```

Der **Short-Term-Verlauf** wird als Kurve mitgeführt, nicht nur als Kennwert. Ein
wandernder Mikrofonabstand ist allein daran zu erkennen: Er zeigt sich als Drift über
Minuten, während eine große P10–P90-Spanne aus lauten und leisen Sätzen dasselbe Streumaß
erzeugt. Ohne den Verlauf sind beide Fälle nicht zu trennen, und die Positionsempfehlung
wäre geraten.

Die **Terzbänder** sind auf ihren eigenen Mittelwert normiert und damit unabhängig vom
Aufnahmegain. Aussagekräftig ist die Differenzkurve zur Referenz, nicht die Absolutkurve.

## Comparison

```python
@dataclass(frozen=True)
class Delta:
    peak_db: float
    true_peak_db: float
    lufs_i_db: float
    crest_db: float
    speech_median_db: float
    p10_p90_db: float                 # Differenz der Spannenbreiten
    noise_floor_db: float | None

@dataclass(frozen=True)
class Comparison:
    schema_version: int
    reference_index: int
    deltas: list[Delta]               # Reihenfolge wie die Eingabeliste
    third_octave_hz: list[float]
    third_octave_diff_db: list[list[float]]   # je Messung eine Kurve
    warnings: list[str]               # etwa abweichende Samplerate
```

Es gibt keine Take-Identitäten. Die Zuordnung läuft über die Reihenfolge der Eingabeliste;
wer Namen braucht, hält sie außerhalb.

## TargetProfile

```python
@dataclass(frozen=True)
class TargetProfile:
    name: str

    lufs_i: float
    lufs_i_tolerance_db: float
    true_peak_max_dbtp: float
    peak_max_dbfs: float

    p10_p90_max_db: float
    crest_range_db: tuple[float, float]
    snr_min_db: float
    noise_floor_max_dbfs: float

    eq_max_gain_db: float = 4.0
    eq_max_filters: int = 3
    comp_target_range_db: float = 8.0
    comp_attack_ms: float = 10.0
    comp_release_ms: float = 200.0

    @classmethod
    def raw(cls) -> "TargetProfile": ...
    @classmethod
    def delivery(cls) -> "TargetProfile": ...
```

Die Ziele, gegen die empfohlen wird. Die konkreten Werte und ihre Begründung stehen unter
[Zielwerte](../zielwerte.md).

`comp_attack_ms` und `comp_release_ms` stehen bewusst im Profil und nicht in einer
Rechnung: Sie folgen aus Sprechtempo und Geschmack, nicht aus Kennwerten.

## Advice und Suggestion

```python
@dataclass(frozen=True)
class Evidence:
    field: str            # etwa "third_octave_db[125]"
    value: float
    threshold: float
    unit: str

@dataclass(frozen=True)
class Expectation:
    field: str
    direction: str        # "sinkt" | "steigt"
    amount: float
    unit: str

@dataclass(frozen=True)
class Suggestion:
    id: str               # etwa "position.proximity_excess"
    topic: str            # "position" | "eq" | "comp"
    severity: str         # "low" | "medium" | "high"
    order: int            # Rangfolge, 1 zuerst
    title: str            # deutsch
    detail: str           # deutsch
    evidence: list[Evidence]
    expected: list[Expectation]
    parameters: dict[str, float]   # leer bei "position"

@dataclass(frozen=True)
class Advice:
    schema_version: int
    ruleset_version: int
    profile: TargetProfile
    material: str                  # "raw" | "processed"
    had_reference: bool
    suggestions: list[Suggestion]
    skipped: list[str]             # Regeln, die nicht geprüft werden konnten
```

Wie bei `Measurement` reisen die Voraussetzungen mit dem Ergebnis: Eine Empfehlung ohne ihr
Ziel ist nicht nachvollziehbar.

`skipped` ist kein Randfall, sondern wichtig. Fehlt die `noise_region`, kann die
Abstandsregel nicht greifen — und dass sie nicht gegriffen hat, ist eine andere Aussage
als „alles in Ordnung".

## ReferenceCheck

```python
@dataclass(frozen=True)
class ReferenceCheck:
    schema_version: int
    suitable: bool
    reasons: list[str]      # deutsch, leer wenn suitable
    checked: list[str]      # welche Prüfungen liefen
```

`suitable` heißt „technisch als Maßstab brauchbar", nicht „klingt gut".
