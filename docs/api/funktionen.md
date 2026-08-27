# Funktionen

!!! warning "Entwurf"

    Diese Signaturen sind ein Vorschlag und noch nicht implementiert. Solange keine
    Version 1.0 veröffentlicht ist, können sie sich ändern.

Alles, was auf dieser Seite steht, ist der Vertrag. Alles darunter ist privat und darf
ohne Versionssprung geändert werden. Neue Funktionen kommen erst in den Namensraum, wenn
sie stabil sind.

```python
from podmetrics import load, measure, compare, gain_for_target_lufs
from podmetrics import advise, check_reference
from podmetrics import Signal, AnalysisParams, Measurement, Comparison
from podmetrics import TargetProfile, Advice, Suggestion, ReferenceCheck
```

## load

```python
def load(
    path: str | os.PathLike,
    *,
    channel: int = 0,
    target_rate: int | None = None,
) -> Signal
```

Lädt eine Audiodatei und gibt genau einen Kanal zurück, als float64 im Bereich −1..1.

`channel` wählt den Kanal aus. Es wird nicht gemischt — die Summierung zweier
Sprecherkanäle erzeugt Kammfilter, die im Messergebnis wie ein Aufnahmefehler aussehen.
Bei mehrkanaligem Material ohne ausdrückliche Angabe wird Kanal 0 genommen und das im
`Signal` vermerkt.

`target_rate` resampelt, wenn nötig. Ohne Angabe bleibt die Samplerate der Datei erhalten.
Zwei Messungen mit verschiedener Samplerate sind vergleichbar, aber `compare()` weist
darauf hin.

## measure

```python
def measure(
    signal: Signal,
    *,
    params: AnalysisParams = AnalysisParams(),
    noise_region: tuple[float, float] | None = None,
    region: tuple[float, float] | None = None,
) -> Measurement
```

Führt alle Messungen aus und setzt sie zu einem `Measurement` zusammen. Das ist die
einzige Funktion, die die Rechenmodule kennt; sie ist ein Zusammenbau und enthält selbst
keine DSP-Logik.

`noise_region` ist ein Zeitbereich in Sekunden, in dem der Rauschteppich gemessen wird.
Ohne diese Angabe bleibt `noise_floor_dbfs` leer. Die Bibliothek sucht sich keine Pause
selbst.

`region` schränkt die Auswertung auf einen Zeitabschnitt ein. Für den Spektralvergleich
zweier Takes desselben Textes ist das der Unterschied zwischen einer belastbaren und einer
zufälligen Differenzkurve: Verschiedene Sätze haben verschiedene Spektren, und was dann als
Positionsbefund erscheint, ist in Wahrheit anderer Inhalt. In der Messreihe wurde
durchgängig derselbe Abschnitt 11,8–15,0 s verglichen. Ohne Angabe wird das ganze Signal
ausgewertet.

Das zurückgegebene `Measurement` enthält die verwendeten `AnalysisParams` sowie beide
Bereiche. Die Voraussetzungen reisen mit dem Ergebnis, weil eine Messung ohne sie nicht
reproduzierbar ist.

## compare

```python
def compare(
    measurements: list[Measurement],
    *,
    reference: Measurement,
) -> Comparison
```

Rechnet Kennwert-Deltas und Terzband-Differenzkurven aller übergebenen Messungen gegen die
Referenz. Die Referenz darf selbst in der Liste stehen; ihre Deltas sind dann null, was
als Kontrollzeile in einer Tabelle nützlich ist.

`compare()` verwaltet keine Referenz und merkt sich nichts. Die Referenz wird bei jedem
Aufruf übergeben.

## gain_for_target_lufs

```python
def gain_for_target_lufs(
    measurement: Measurement,
    target_lufs: float,
) -> float
```

Gibt den Faktor in dB zurück, um den das Material verstärkt oder abgesenkt werden muss,
damit es den Zielwert erreicht. Die Bibliothek wendet ihn nicht an — das Anwenden ist
Sache des Aufrufers.

Ist `lufs_i_reliable` falsch, ist auch dieser Wert unzuverlässig. Die Funktion rechnet
trotzdem und verweigert nicht; die Markierung im `Measurement` bleibt die Warnung.

## advise

```python
def advise(
    measurement: Measurement,
    *,
    reference: Measurement | None = None,
    profile: TargetProfile = TargetProfile.raw(),
    topics: tuple[str, ...] = ("position", "eq", "comp"),
    material: str = "raw",
) -> Advice
```

Leitet Empfehlungen ab. Sieht keine Samples, sondern rechnet ausschließlich auf
`Measurement` und den daraus gebildeten Deltas.

`topics` wählt die Themen: `"position"` für die Mikrofonaufstellung, `"eq"` und `"comp"`
für ReaEQ und ReaComp.

`material` sagt, ob die Messung aus unbearbeitetem Material stammt (`"raw"`) oder aus einem
gerenderten Take mit EQ und Kompressor (`"processed"`). Die Bibliothek kann das nicht
erkennen, deshalb wird es übergeben. Bei `"processed"` entfallen Positionsempfehlungen mit
Begründung, statt still falsch zu sein.

Ohne `reference` und ohne abweichendes `profile` gibt es nichts zu raten: Aus einer
einzelnen Messung ohne Ziel folgt nichts. Die Regeln stehen unter
[Empfehlungen](empfehlungen.md).

## check_reference

```python
def check_reference(
    measurement: Measurement,
    *,
    profile: TargetProfile = TargetProfile.raw(),
    against: Measurement | None = None,
) -> ReferenceCheck
```

Beantwortet eine technische Frage, keine künstlerische: Taugt diese Messung als Maßstab?

Geprüft werden Mindestdauer für belastbares LUFS-I, Freiheit von Clipping, True Peak
innerhalb der Profilgrenze und das Vorhandensein eines gemessenen Rauschteppichs. Ist
`against` übergeben, wird zusätzlich die Vergleichbarkeit mit dem Prüfling in Samplerate
und Kanalwahl geprüft.

Ob ein Take gut klingt, entscheidest Du. Die Bibliothek sagt nur, ob er als Bezugspunkt
brauchbar ist. Beides zusammen ist der Weg: Du wählst nach Gehör, die Prüfung wehrt
Kandidaten ab, die zu kurz, übersteuert oder aus einer anderen Kette sind. Ein untauglicher
Maßstab erzeugt lauter Empfehlungen, die alle in dieselbe falsche Richtung zeigen.
