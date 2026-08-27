# CLAUDE.md

## Projekt

`podmetrics` — eigenständige Python-Bibliothek mit CLI zur Messung von Sprachaufnahmen. Nimmt Audio, gibt Zahlen zurück. Kein Web, keine Datenbank, kein persistenter Zustand.

Zwei Konsumenten: die CLI für den direkten Gebrauch am Terminal und eine Vue-Webapp in einem separaten Repository. Weil die Bibliothek von außen benutzt wird, ist ihre öffentliche API ein Vertrag und keine Implementierungsdetail-Sammlung.

Material, das gemessen wird: Podcast-Sprachaufnahmen, WAV 24 Bit, aus Shure MV7 / MV7X → Zoom PodTrak P4next → Ultraschall (REAPER).

## Abgrenzung

Was hier hineingehört: alles, was aus Audio Zahlen macht. Gating, Pegelstatistik, Lautheit, Spektrum, die Vergleichsrechnung zweier Messungen und die Berechnung des Gainfaktors für eine Pegelangleichung.

Was hier nicht hineingehört: Dateiverwaltung über den Einzelaufruf hinaus, Datenbank, HTTP, Take-Identitäten, Referenzverwaltung als Zustand, Bedienoberfläche, das Ausspielen von Audio.

Der Grenzfall, an dem sich die Regel zeigt: `gain_for_target_lufs()` gehört hierher, weil es eine Rechnung ist. Das Anwenden dieses Faktors und das Streamen der Datei an einen Browser gehört in die Webapp.

Wenn die Webapp eine Zahl braucht, die es hier noch nicht gibt, wird sie hier ergänzt und nicht dort gerechnet. Doppelte DSP-Logik in zwei Repositories ist der Fehler, den diese Trennung verhindern soll.

## Öffentliche API

```python
from podmetrics import load, measure, compare, gain_for_target_lufs
from podmetrics import Signal, AnalysisParams, Measurement, Comparison

signal = load("take_002.wav")
m2 = measure(signal, params=AnalysisParams(), noise_region=(12.4, 42.4))
m7 = measure(load("take_007.wav"))
cmp = compare([m2, m7], reference=m2)
```

Diese Namen sind der Vertrag. Alles unterhalb davon ist privat und darf ohne Versionssprung geändert werden. Neue Funktionen kommen erst in den Namensraum, wenn sie stabil sind.

## Datentypen

Alle Modelle sind frozen Dataclasses in `models.py` und tragen `to_dict()` / `from_dict()`.

`Signal` hält Samples als float64 in −1..1 und die Samplerate. Mehrkanaliges Material wird beim Laden auf einen Kanal reduziert, die Kanalwahl ist explizit anzugeben statt zu mischen — Summierung zweier Sprecherkanäle erzeugt Kammfilter im Messergebnis.

`AnalysisParams` hält alle Fensterlängen, Schwellen und Bandgrenzen. Defaults werden nie stillschweigend geändert; jede Änderung entwertet alle früheren Vergleiche.

`Measurement` enthält die Kennwerte, die verwendeten `AnalysisParams` und ein `schema_version`. Die Parameter reisen mit dem Ergebnis mit, weil eine Messung ohne ihre Parameter nicht reproduzierbar ist.

`Comparison` enthält Kennwert-Deltas und die Terzband-Differenzkurve gegen die Referenz.

Serialisierung liefert reine Python-Typen. Keine numpy-Skalare, keine Arrays — floats und Listen, sonst scheitert die JSON-Kodierung beim Konsumenten an Stellen, die hier nie auffallen.

## Struktur

```
src/podmetrics/
  models.py       Dataclasses, kennt nur numpy
  io.py           laden, Kanalwahl, Resampling
  gating.py       Sprachsegmente und Pausen trennen
  levels.py       Peak, True Peak, Crest, RMS-Perzentile
  loudness.py     LUFS-I, Short-Term, Blockbalance, Gainberechnung
  spectrum.py     Welch-PSD, Terzbänder
  compare.py      Deltas und Differenzkurven
  report.py       measure() — setzt die Einzelmodule zusammen
  cli.py
tests/
pyproject.toml
```

Schichtung: `models` kennt niemanden. Die Rechenmodule kennen nur `models` und numpy/scipy, nicht einander. `report` und `cli` kennen alles. Ein Rechenmodul, das ein anderes importiert, ist ein Hinweis auf einen falschen Schnitt.

## Fachliche Regeln

Vor jeder Pegelstatistik und vor allem Spektralen werden Sprechpausen entfernt. Stille mischt dem Spektrum einen Rauschanteil bei und zieht die Pegelverteilung mit einem Schwanz sehr leiser Werte nach unten, was den Median verschiebt. Gating gegen −45 dBFS auf gleitendem RMS, Segmente unter 100 ms verwerfen.

True Peak wird 4-fach oversampled per `resample_poly` berechnet. pyloudnorm liefert keinen True Peak, und der Sample-Peak übersieht Intersample-Spitzen.

LUFS-I braucht mindestens 30 Sekunden, sonst greift das BS.1770-Gating unzuverlässig. Kürzeres Material wird gemessen, aber im Ergebnis als unzuverlässig markiert — nicht stillschweigend geliefert und nicht verweigert.

Der Rauschteppich wird ausschließlich in einem explizit übergebenen Bereich gemessen. Ohne `noise_region` bleibt das Feld `None`. Die Bibliothek sucht sich keine Pause selbst; welcher Abschnitt eine echte Sprechpause ist, weiß nur der Nutzer.

Terzband-Energien werden auf ihren eigenen Mittelwert normiert, damit sie unabhängig vom Aufnahmegain vergleichbar sind. Aussagekräftig ist die Differenzkurve zur Referenz, nicht die Absolutkurve.

Fenster: gleitendes RMS 200 ms bei 50 % Überlappung, Short-Term-Lautheit 3 s gleitend.

Der Median-Sprechpegel und die Spanne P10–P90 werden mitgeliefert, weil daraus der Kompressor-Threshold folgt. Die Bibliothek schlägt keinen Threshold vor — die Umrechnung hängt von Ratio und Zielspanne ab und ist eine Entscheidung, keine Messung.

## CLI

Der Terminalgebrauch ist gleichrangig mit dem Bibliotheksgebrauch, nicht ein Nebenprodukt. Die häufigste Arbeitsweise ist: rendern, `podmetrics batch` auf den Ordner, Zeilen vergleichen, nächste Version. Dafür darf nichts installiert, gestartet oder geöffnet werden müssen außer diesem Paket.

```
podmetrics measure FILE [--noise 12.4:42.4] [--channel 0] [--json]
podmetrics batch DIR --reference take_002.wav [--csv out.csv]
podmetrics compare FILE_A FILE_B --reference FILE_A
```

`batch` ist der Hauptanwendungsfall: ein Ordner mit Renderversionen, eine Zeile pro Datei, Spalten für Peak, True Peak, LUFS-I, Crest, P10–P90, Rauschteppich. Untereinander stehende Zeilen sind der Zweck — der Vergleich soll eine Subtraktion sein und keine Erinnerung.

Zahlenausgabe rechtsbündig und monospace, sonst sind die Spalten nicht lesbar. `--json` gibt maschinenlesbar aus, ohne Tabellenrahmen und ohne Farbcodes, damit die Ausgabe in `jq` und Skripte fließen kann.

Abweichungen von den Zielwerten werden farblich markiert, aber nur wenn die Ausgabe auf ein Terminal geht. Bei Umleitung in eine Datei entfallen die Steuerzeichen.

## Eigenständiger Gebrauch

Installation als Werkzeug, ohne Projektumgebung:

```
uv tool install podmetrics[cli]
```

Kein Docker, kein Server, kein Browser. Das Paket bleibt bewusst leichtgewichtig, damit dieser Weg schnell startet — jede zusätzliche Abhängigkeit verlängert die Startzeit bei einem Aufruf, der zwanzigmal am Tag vorkommt.

Die Webapp ist Konsument dieses Pakets, nie umgekehrt. Ein Import aus dem Webapp-Repository, eine Konfiguration, die dort liegt, oder ein Kennwert, der nur im Zusammenspiel mit ihr berechenbar ist, sind Fehler. Wenn die CLI ohne die Webapp nicht mehr vollständig arbeitet, ist die Trennung gebrochen.

## Abhängigkeiten

numpy, scipy, soundfile, pyloudnorm. Für die CLI zusätzlich typer und rich als Extra `podmetrics[cli]`, damit die Bibliothek als Webapp-Dependency ohne Terminal-Ballast installierbar bleibt.

Kein librosa. Es zieht viel Ballast für Funktionen mit, die hier nicht gebraucht werden.

## Versionierung

SemVer für das Paket. `Measurement.schema_version` wird getrennt geführt und erhöht, wenn Felder wegfallen oder ihre Bedeutung sich ändert. Die Webapp speichert Messungen dauerhaft und muss alte Datensätze erkennen können.

Änderungen an Default-Werten in `AnalysisParams` sind Breaking Changes, auch wenn sich keine Signatur ändert.

## Tests

Jede Rechenfunktion bekommt mindestens einen Test mit synthetischem Signal, dessen Ergebnis analytisch bekannt ist: Sinus bekannter Amplitude, weißes Rauschen bekannter Leistung, Stille, ein Sinus mit definierter Pause für das Gating.

Dazu ein Golden Test: ein deterministisch erzeugtes Signal, dessen vollständiges `Measurement` als JSON im Repository liegt. Er schlägt fehl, sobald sich ein Rechenweg unbeabsichtigt ändert — genau der Fall, der sonst erst Monate später als unerklärliche Abweichung auffällt.

Roundtrip-Test für `to_dict()` / `from_dict()` auf jedem Modell.

Keine echten Audiodateien im Repository.
