# Datentypen

!!! note "Stand 0.1.0"

    Die Feldlisten entsprechen dem Code. Weicht eine Zeile hier vom Quelltext ab, ist
    das ein Fehler in dieser Seite und kein zweiter Standpunkt.

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
    source_sha256: str

    @property
    def duration_s(self) -> float: ...
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

    # Ein Plosiv ist eine Spitze, deren Tieftonanteil weit über dem des
    # umgebenden Sprachblocks liegt — in der Messreihe 95,6 % gegen 28,7 %.
    plosive_split_hz: float = 120.0
    plosive_share_factor: float = 2.0
    plosive_min_share: float = 0.6

    welch_segment_s: float = 0.093
    comb_min_depth_db: float = 3.0
    comb_min_notches: int = 4
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
    peak_speech_dbfs: float        # Peak ohne Plosivspitzen
    true_peak_dbtp: float
    crest_db: float
    clipped_samples: int

    lufs_i: float
    lufs_i_reliable: bool          # falsch unter lufs_min_duration_s
    short_term_lufs: list[float]   # 3 s gleitend
    short_term_times_s: list[float]
    block_balance_db: float        # Lautheitsspanne zwischen Abschnitten

    speech_median_dbfs: float
    speech_p10_dbfs: float
    speech_p90_dbfs: float
    speech_ratio: float            # Anteil Sprache nach dem Gating

    third_octave_hz: list[float]
    third_octave_db: list[float]   # auf den eigenen Mittelwert normiert
    comb_spacing_hz: float | None  # Einbruchsabstand, None wenn kein Kamm
    comb_depth_db: float | None

    plosives: list[Plosive]

    noise_floor_dbfs: float | None  # None ohne noise_region
    noise_region_s: tuple[float, float] | None

    analysis_region_s: tuple[float, float] | None
    source_sha256: str

    params: AnalysisParams
```

```python
@dataclass(frozen=True)
class Plosive:
    time_s: float
    peak_dbfs: float
    low_energy_share: float    # Anteil unter 120 Hz
    block_share: float         # derselbe Anteil im umgebenden Sprachblock
```

Der **Short-Term-Verlauf** wird als Kurve mitgeführt, nicht nur als Kennwert. Ein
wandernder Mikrofonabstand ist allein daran zu erkennen: Er zeigt sich als Drift über
Minuten, während eine große P10–P90-Spanne aus lauten und leisen Sätzen dasselbe Streumaß
erzeugt. Ohne den Verlauf sind beide Fälle nicht zu trennen, und die Positionsempfehlung
wäre geraten.

Die **Terzbänder** sind auf ihren eigenen Mittelwert normiert und damit unabhängig vom
Aufnahmegain. Aussagekräftig ist die Differenzkurve zur Referenz, nicht die Absolutkurve.

`comb_spacing_hz` kommt dagegen **nicht** aus den Terzbändern, sondern aus der feiner
aufgelösten Welch-PSD: Ein Kammfilter zeigt Einbrüche in gleichmäßigem Frequenzabstand,
und Terzbänder mitteln genau die weg. Der Abstand nennt die Verzögerung der störenden
Kopie, die Tiefe ihren Pegelabstand.

`peak_dbfs` und `peak_speech_dbfs` stehen nebeneinander, weil sie verschiedene Fragen
beantworten. Der erste sagt, ob etwas angeschlagen ist. Der zweite ist der Maßstab für den
Gain, denn Plosivspitzen sitzen unter 120 Hz und fallen dem Hochpass später ohnehin zum
Opfer. Wer den Gain nach `peak_dbfs` einstellt, nimmt die Sprache mehrere Dezibel zu leise
auf.

`source_sha256` ist die einzige Take-Identität, die es hier gibt — und sie ist eine
gemessene Eigenschaft der Eingabe, keine Verwaltung. Sie steht drin, weil in der Messreihe
aus übereinstimmenden Kennwerten auf dieselbe Datei geschlossen wurde und das falsch war.
Gleiche Zahlen sind kein Beweis für gleiche Datei.

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
    def raw(cls) -> "TargetProfile": ...
    @classmethod
    def delivery(cls) -> "TargetProfile": ...
```

Die Ziele, gegen die empfohlen wird. Die konkreten Werte und ihre Begründung stehen unter
[Zielwerte](../zielwerte.md).

`comp_attack_ms`, `comp_release_ms` und `comp_knee_db` stehen bewusst im Profil und nicht
in einer Rechnung: Sie folgen aus Sprechtempo und Geschmack, nicht aus Kennwerten.

`comp_threshold_below_median_db` ist der Kern der Kompressor-Empfehlung. Der Wert ist
positiv und wird vom Median **abgezogen** — ein Threshold oberhalb des Medians lässt den
Kompressor fast nichts tun. Die Herleitung steht unter [Messreihen](../messreihen.md#der-denkfehler-der-die-formel-festlegt).

`noise_floor_compressed_max_dbfs` (−48 dB) ist die Grenze, an der Kompression zu stark
geworden ist. Sie steht getrennt von `noise_floor_max_dbfs` für die Rohaufnahme, weil es
zwei verschiedene Fragen sind: wie sauber die Aufnahme ist, und wie viel die Bearbeitung
davon hochgezogen hat.

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
    profile: TargetProfile
    material: str                  # "raw" | "processed"
    had_reference: bool
    suggestions: list[Suggestion]
    skipped: list[str]             # Regeln, die nicht geprüft werden konnten
    chain_order: list[str]         # Hochpass → EQ → Kompressor → Pegelangleichung
    schema_version: int
    ruleset_version: int
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

## Abgeleitete Werte

`Measurement` trägt zwei Eigenschaften, die aus den Feldern folgen und deshalb nicht
gespeichert werden:

```python
measurement.p10_p90_db   # speech_p90_dbfs − speech_p10_dbfs
measurement.snr_db       # speech_median_dbfs − noise_floor_dbfs, None ohne Rauschbereich
```
