# CLAUDE.md

## Projekt

`podmetrics` — eigenständige Python-Bibliothek mit CLI zur Messung von Sprachaufnahmen. Nimmt Audio, gibt Zahlen zurück. Kein Web, keine Datenbank, kein persistenter Zustand.

Zwei Konsumenten: die CLI für den direkten Gebrauch am Terminal und eine Vue-Webapp in einem separaten Repository. Weil die Bibliothek von außen benutzt wird, ist ihre öffentliche API ein Vertrag und keine Implementierungsdetail-Sammlung.

Material, das gemessen wird: Podcast-Sprachaufnahmen, WAV 24 Bit, aus Shure MV7 / MV7X → Zoom PodTrak P4next → Ultraschall (REAPER).

## Abgrenzung

Was hier hineingehört: alles, was aus Audio Zahlen macht. Gating, Pegelstatistik, Lautheit, Spektrum, die Vergleichsrechnung zweier Messungen und die Berechnung des Gainfaktors für eine Pegelangleichung.

Dazu alles, was aus diesen Zahlen folgt: Empfehlungen zur Mikrofonposition, zu EQ- und Kompressoreinstellungen, die Eignungsprüfung einer Referenz. Diese Rechnungen sehen keine Samples, sondern nur `Measurement` und `Comparison`. Sie gehören hierher, weil sie dieselben Kennwerte lesen, die hier entstehen — und weil eine Empfehlung, die anderswo gerechnet wird, die Schwellen dorthin kopiert und damit zwei Wahrheiten schafft.

Was hier nicht hineingehört: Dateiverwaltung über den Einzelaufruf hinaus, Datenbank, HTTP, Take-Identitäten, Referenzverwaltung als Zustand, Bedienoberfläche, das Ausspielen von Audio, das Anwenden einer Empfehlung, das Schreiben von REAPER- oder Ultraschall-Dateien wie FX-Chains und Trackvorlagen.

Der Grenzfall, an dem sich die Regel zeigt: `gain_for_target_lufs()` gehört hierher, weil es eine Rechnung ist. Das Anwenden dieses Faktors und das Streamen der Datei an einen Browser gehört in die Webapp.

Der zweite Grenzfall, gleiche Regel: Eine ReaComp-Einstellung zu berechnen gehört hierher. Sie in ein Ultraschall-Projekt zu schreiben nicht. Die Werte stehen in der Ausgabe und werden von Hand eingetragen; der Weg ist kurz genug, und die Bibliothek bleibt frei von Projektwissen. Wer eine `.RfxChain` schreibt, hat eine Dateiübernahme gebaut und muss ab dann REAPER-Versionen hinterherpflegen.

Wenn die Webapp eine Zahl braucht, die es hier noch nicht gibt, wird sie hier ergänzt und nicht dort gerechnet. Doppelte DSP-Logik in zwei Repositories ist der Fehler, den diese Trennung verhindern soll.

## Öffentliche API

```python
from podmetrics import load, measure, compare, gain_for_target_lufs
from podmetrics import advise, check_reference
from podmetrics import Signal, AnalysisParams, Measurement, Comparison
from podmetrics import TargetProfile, Advice, Suggestion, ReferenceCheck

signal = load("take_002.wav")
m2 = measure(signal, params=AnalysisParams(), noise_region=(12.4, 42.4))
m7 = measure(load("take_007.wav"))
cmp = compare([m2, m7], reference=m2)

eignung = check_reference(m2)
tipps = advise(m7, reference=m2, topics=("position", "eq"), profile=TargetProfile())
```

Diese Namen sind der Vertrag. Alles unterhalb davon ist privat und darf ohne Versionssprung geändert werden. Neue Funktionen kommen erst in den Namensraum, wenn sie stabil sind.

## Datentypen

Alle Modelle sind frozen Dataclasses in `models.py` und tragen `to_dict()` / `from_dict()`.

`Signal` hält Samples als float64 in −1..1 und die Samplerate. Mehrkanaliges Material wird beim Laden auf einen Kanal reduziert, die Kanalwahl ist explizit anzugeben statt zu mischen — Summierung zweier Sprecherkanäle erzeugt Kammfilter im Messergebnis.

`AnalysisParams` hält alle Fensterlängen, Schwellen und Bandgrenzen. Defaults werden nie stillschweigend geändert; jede Änderung entwertet alle früheren Vergleiche.

`Measurement` enthält die Kennwerte, die verwendeten `AnalysisParams` und ein `schema_version`. Die Parameter reisen mit dem Ergebnis mit, weil eine Messung ohne ihre Parameter nicht reproduzierbar ist.

`Comparison` enthält Kennwert-Deltas und die Terzband-Differenzkurve gegen die Referenz.

`TargetProfile` hält die Ziele, gegen die empfohlen wird: Ziel-LUFS-I, True-Peak-Grenze, Zielspanne für P10–P90, geforderter Rauschabstand, die Obergrenzen für EQ-Vorschläge und die Vorgaben für Attack und Release. Jeder Defaultwert steht im Quelltext mit einer Zeile Begründung. Ein Zielwert ohne Herkunft wird nach drei Monaten nicht mehr hinterfragt, sondern geglaubt.

`Advice` enthält eine Liste von `Suggestion`, das verwendete `TargetProfile`, die Angabe, ob und gegen welche Referenz geraten wurde, den angenommenen Materialzustand und eine `ruleset_version`. Wie bei `Measurement` reisen die Voraussetzungen mit dem Ergebnis, weil eine Empfehlung ohne ihr Ziel nicht nachvollziehbar ist.

`Suggestion` enthält eine stabile `id`, das Thema, einen Schweregrad, den deutschen Text, die auslösenden Messwerte samt Schwelle, die erwartete Wirkung als Messwert, die Rangfolge und — bei EQ und Kompression — die konkreten Parameter als Zahlen.

`ReferenceCheck` enthält eine Eignungsaussage und die Gründe, die dagegen sprechen.

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
  advice.py       Empfehlungen aus Measurement und Comparison
  report.py       measure() — setzt die Einzelmodule zusammen
  cli.py
tests/
pyproject.toml
```

Schichtung: `models` kennt niemanden. Die Rechenmodule kennen nur `models` und numpy/scipy, nicht einander. `report` und `cli` kennen alles. Ein Rechenmodul, das ein anderes importiert, ist ein Hinweis auf einen falschen Schnitt.

`advice` steht eine Schicht höher: Es kennt `models` und sonst nichts — insbesondere kein `Signal`, kein soundfile, kein scipy. Ein Import von numpy dort ist bereits ein Warnzeichen, ein Zugriff auf Samples ein Fehler. Empfehlungen müssen aus den veröffentlichten Zahlen ableitbar sein, notfalls von Hand auf Papier. Was nur aus dem Signal folgt, ist ein fehlender Kennwert und gehört in ein Rechenmodul.

## Fachliche Regeln

Vor jeder Pegelstatistik und vor allem Spektralen werden Sprechpausen entfernt. Stille mischt dem Spektrum einen Rauschanteil bei und zieht die Pegelverteilung mit einem Schwanz sehr leiser Werte nach unten, was den Median verschiebt. Gating gegen −45 dBFS auf gleitendem RMS, Segmente unter 100 ms verwerfen.

True Peak wird 4-fach oversampled per `resample_poly` berechnet. pyloudnorm liefert keinen True Peak, und der Sample-Peak übersieht Intersample-Spitzen.

LUFS-I braucht mindestens 30 Sekunden, sonst greift das BS.1770-Gating unzuverlässig. Kürzeres Material wird gemessen, aber im Ergebnis als unzuverlässig markiert — nicht stillschweigend geliefert und nicht verweigert.

Der Rauschteppich wird ausschließlich in einem explizit übergebenen Bereich gemessen. Ohne `noise_region` bleibt das Feld `None`. Die Bibliothek sucht sich keine Pause selbst; welcher Abschnitt eine echte Sprechpause ist, weiß nur der Nutzer.

Terzband-Energien werden auf ihren eigenen Mittelwert normiert, damit sie unabhängig vom Aufnahmegain vergleichbar sind. Aussagekräftig ist die Differenzkurve zur Referenz, nicht die Absolutkurve.

Fenster: gleitendes RMS 200 ms bei 50 % Überlappung, Short-Term-Lautheit 3 s gleitend.

Der Median-Sprechpegel und die Spanne P10–P90 werden mitgeliefert, weil daraus der Kompressor-Threshold folgt. Die Messmodule schlagen keinen Threshold vor — die Umrechnung hängt von Ratio und Zielspanne ab und ist eine Entscheidung, keine Messung. Die Entscheidung wird nicht verschwiegen, sondern verlagert: Sie fällt im Empfehlungsteil, gegen ein ausdrücklich übergebenes Ziel und mit genannter Zielspanne. Ein Messwert bleibt ein Messwert, auch wenn eine Schicht darüber ein Vorschlag daraus gerechnet wird.

`Measurement` führt den Short-Term-Pegelverlauf als grobe Kurve mit, nicht nur dessen Kennwerte. Ein wandernder Mikrofonabstand ist allein daran zu erkennen: Er zeigt sich als Drift über Minuten, während eine große P10–P90-Spanne aus lauten und leisen Sätzen dasselbe Streumaß erzeugt. Ohne den Verlauf sind beide Fälle nicht zu trennen, und die Empfehlung wäre geraten.

## Empfehlungen

Empfehlungen sind der zweite Zweck dieser Bibliothek und vom ersten sauber zu trennen. Gemessen wird immer, geraten nur auf Anforderung. `measure` und `batch` bleiben frei von Ratschlägen: Eine Tabelle, in der zwischen den Zahlen Meinungen stehen, ist als Vergleichsmittel verdorben.

Drei Themen, einzeln anforderbar: `position` für die Mikrofonaufstellung, `eq` und `comp` für ReaEQ und ReaComp in Ultraschall. Ohne Angabe kommen alle drei, in fester Reihenfolge.

### Gemeinsame Regeln

Jede Empfehlung nennt drei Dinge: die Messwerte, die sie ausgelöst haben, mit Zahl und Schwelle; die vorgeschlagene Änderung; die erwartete Wirkung, ausgedrückt als Messwert. Der dritte Punkt ist der wichtigste. Er macht die nächste Messung zur Prüfung der Empfehlung — tritt die erwartete Änderung nicht ein, war die Vermutung falsch, und das fällt sofort auf statt nach fünf Takes.

Eine Änderung pro Runde. Wer Abstand und EQ gleichzeitig ändert, kann die Wirkung im nächsten Take keiner Ursache mehr zuordnen und lernt nichts. Die Ausgabe ist deshalb nach Rangfolge sortiert und markiert, was zuerst zu tun ist; alles Weitere ist ausdrücklich als „danach“ gekennzeichnet.

Die Reihenfolge steht fest: Position vor EQ vor Kompression vor Pegelangleichung. Was der Abstand zum Mikrofon behebt, wird nicht per Filter repariert. Ein EQ-Vorschlag, der eine ungelöste Positionsempfehlung überdeckt, wird zurückgehalten und durch den Hinweis darauf ersetzt.

Ohne Bezug keine Empfehlung. Grundlage ist eine Referenzmessung, ein `TargetProfile` oder beides. Aus einer einzelnen Messung ohne Ziel folgt nichts: −18 LUFS sind weder gut noch schlecht, sondern nur eine Zahl.

Empfehlungen sind Hypothesen mit Rangfolge, nicht Diagnosen. Eine dunkle Stimme und ein zu geringer Abstand erzeugen ähnliche Terzbandbilder; Raumhall, Popp-Geräusche und ein schräg stehendes Mikrofon sind aus den vorhandenen Kennwerten nicht sicher auseinanderzuhalten. Wo zwei Ursachen gleich plausibel sind, werden beide genannt, statt eine zu wählen. Der Ton ist „probier das und miss nach“, nicht „dein Mikro steht falsch“.

Jede Empfehlung trägt eine stabile ID nach dem Muster `position.proximity_excess`, `eq.presence_dip`, `comp.threshold`. Die IDs sind Teil des Vertrags wie die Funktionsnamen: Die Webapp hängt Texte daran, und nur damit lässt sich über Wochen sehen, ob dieselbe Empfehlung immer wieder kommt. IDs sind englisch, die ausgegebenen Texte deutsch.

Schweregrad statt Ja/Nein. `low` heißt: fällt in der Messung auf, wahrscheinlich nicht hörbar. `high` heißt: das ist der Grund, warum der Take anders klingt als die Referenz. Die Schwellen stehen im `TargetProfile` und nicht im Code verstreut.

Positionsempfehlungen setzen unbearbeitetes Material voraus — den Rohmitschnitt, nicht den gerenderten Take mit EQ und Kompressor. Die Bibliothek kann Bearbeitung nicht erkennen; der Zustand wird übergeben, die Vorgabe ist „roh“, und die Annahme steht in der Ausgabe. Wer eine bearbeitete Datei als roh ausgibt, bekommt Empfehlungen gegen seine eigene Bearbeitung.

### Position

Grundlage sind Terzband-Differenzkurve, Pegelverlauf, P10–P90 und Rauschabstand.

Überschuss bei 100–250 Hz gegen die Referenz deutet auf zu geringen Abstand — der Nahbesprechungseffekt der Richtmikrofone MV7 und MV7X. Vorschlag: Abstand vergrößern, eine Handbreit als Startwert, neu aufnehmen und messen. Abfall oberhalb 6 kHz bei unauffälligem Grundton deutet auf Sprechen an der Achse vorbei; Winkel prüfen. Zu geringer Rauschabstand bei ansonsten passendem Spektrum deutet auf zu großen Abstand mit hochgedrehter Vorverstärkung. Überschuss bei 5–8 kHz deutet auf Zischlaute; das Mikrofon leicht aus der Achse zu drehen ist die erste Maßnahme, ein De-Esser die zweite. Eine große P10–P90-Spanne zusammen mit driftendem Pegelverlauf deutet auf wechselnden Abstand — das ist eine Frage von Haltung und Stativ und wird nicht durch einen Kompressor gelöst, der die Schwankung nur leiser macht.

Zu Popp-Geräuschen und Raumreflexionen wird nichts empfohlen, solange es dafür keine eigenen Kennwerte gibt — tieffrequente Transienten und eine Nachhallschätzung. Beides ist aus Terzbändern und Pegelstatistik nicht sicher von anderen Ursachen zu trennen. Eine geratene Ursache kostet mehr Zeit als keine Aussage.

### EQ

Grundlage ist die Terzband-Differenzkurve gegen die Referenz.

Vorgeschlagen werden höchstens drei breite Glocken und ein Hochpass. Keine schmalen Kerben: Eine Terzband-Auflösung gibt schmalbandige Korrekturen nicht her, und was in einer gemittelten Kurve als Spitze erscheint, ist oft ein einzelner Vokal. Die Filter werden mit Abstand zueinander gewählt, weil sich überlappende Glocken in ihrer Wirkung addieren und die gerechneten Gains dann nicht mehr stimmen. Grenze ist der Wert aus dem `TargetProfile`, voreingestellt ±4 dB je Filter; wo mehr nötig wäre, ist die Ursache keine Frage des EQ, und die Ausgabe sagt das statt größer zu korrigieren.

Der Hochpass wird aus dem gemessenen Energieanteil unterhalb der Sprechgrundfrequenz vorgeschlagen, nicht pauschal gesetzt. Eine tiefe Stimme verliert bei 100 Hz Fundament, das nicht wiederkommt.

Die Referenz für EQ-Empfehlungen muss ein eigener Take sein. Eine Differenzkurve gegen eine fremde Stimme ist kein Korrekturziel — wer danach filtert, egalisiert seine eigene Stimme weg und hört am Ende wie eine schlechte Kopie des Vorbilds. Die Bibliothek kann das nicht prüfen; der Hinweis steht bei jeder EQ-Ausgabe.

Ausgegeben werden Filtertyp, Frequenz, Gain und Q — direkt in ReaEQ eintragbar.

### Kompression

Grundlage sind Median-Sprechpegel, P10–P90, Crest sowie Peak und True Peak.

Threshold folgt aus dem Median-Sprechpegel, Ratio aus dem Verhältnis der gemessenen Spanne zur Zielspanne des Profils. Beides sind Rechnungen, und beide nennen ihre Eingangswerte in der Ausgabe.

Attack und Release werden nicht gerechnet, sondern aus dem Profil übernommen. Sie folgen aus Sprechtempo und Geschmack, nicht aus Kennwerten. Genau das steht dabei, damit niemand sie für ein Messergebnis hält.

Der Makeup-Gain ist ein Startwert, kein Ergebnis. Kompression ändert die Lautheit, also stimmt der aus der unkomprimierten Messung gerechnete Wert nach dem Rendern nicht mehr. Die Empfehlung sagt ausdrücklich, dass erneut zu messen und `gain_for_target_lufs()` auf das Rendering anzuwenden ist. Die Schleife rendern → messen → nachziehen ist der Normalfall und kein Zeichen eines Fehlers.

Vorgeschlagen wird nur, was Ultraschall ohne Zusatzinstallation mitbringt: ReaEQ, ReaComp und der Ausgangspegel. Liegt der True Peak über der Profilgrenze, ist die Empfehlung, den Ausgangspegel zu senken — nicht, ein weiteres Plugin in die Kette zu hängen.

### Referenz prüfen

`check_reference()` beantwortet eine technische Frage, keine künstlerische: Taugt diese Messung als Maßstab? Geprüft werden Mindestdauer für belastbares LUFS-I, Freiheit von Clipping, True Peak innerhalb der Profilgrenze, das Vorhandensein eines gemessenen Rauschteppichs und die Vergleichbarkeit mit dem Prüfling in Samplerate und Kanalwahl.

Ob ein Take gut klingt, entscheidet der Nutzer. Die Bibliothek sagt nur, ob er als Bezugspunkt brauchbar ist. Beides zusammen ist der Weg: Der Nutzer wählt nach Gehör, die Prüfung wehrt Kandidaten ab, die zu kurz, übersteuert oder aus einer anderen Kette sind. Ein untauglicher Maßstab erzeugt lauter Empfehlungen, die alle in dieselbe falsche Richtung zeigen.

Eine Referenz wird nicht verwaltet. Sie wird bei jedem Aufruf übergeben, als Audiodatei oder als gespeicherte Messung im JSON-Format. Dass die Webapp Referenzen dauerhaft hält, ist ihre Sache und bleibt es.

## CLI

Der Terminalgebrauch ist gleichrangig mit dem Bibliotheksgebrauch, nicht ein Nebenprodukt. Die häufigste Arbeitsweise ist: rendern, `podmetrics batch` auf den Ordner, Zeilen vergleichen, nächste Version. Dafür darf nichts installiert, gestartet oder geöffnet werden müssen außer diesem Paket.

```
podmetrics measure FILE [--noise 12.4:42.4] [--channel 0] [--json]
podmetrics batch DIR --reference take_002.wav [--csv out.csv]
podmetrics compare FILE_A FILE_B --reference FILE_A
podmetrics advise FILE [--reference REF] [--topic position|eq|comp] [--noise 12.4:42.4] [--processed] [--json]
podmetrics check-reference FILE [--noise 12.4:42.4] [--json]
```

`batch` ist der Hauptanwendungsfall: ein Ordner mit Renderversionen, eine Zeile pro Datei, Spalten für Peak, True Peak, LUFS-I, Crest, P10–P90, Rauschteppich. Untereinander stehende Zeilen sind der Zweck — der Vergleich soll eine Subtraktion sein und keine Erinnerung.

`advise` ist der zweite Weg neben `batch`: nicht „welche Version ist näher dran“, sondern „was soll ich als Nächstes anders machen“. `--topic` ist mehrfach angebbar; ohne Angabe kommen alle drei Themen. `--reference` nimmt eine Audiodatei oder eine gespeicherte Messung als `.json`, damit die Referenz nicht bei jedem Aufruf neu gerechnet wird und das Originalmaterial dafür nicht mehr vorliegen muss. `--processed` erklärt das Material als bereits bearbeitet; Positionsempfehlungen entfallen dann mit Begründung, statt still falsch zu sein.

`batch` bleibt ohne Empfehlungen. Wer für zwanzig Dateien Ratschläge ausgibt, bekommt eine Textwand statt einer Tabelle, und die Empfehlungen widersprechen einander, weil jede Datei ihre eigene für sich betrachtet.

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

`Advice.ruleset_version` wird getrennt geführt und erhöht, sobald sich Regeln, Schwellen oder die Bedeutung einer Suggestion-ID ändern. Eine ID wird nie wiederverwendet: Verschwindet eine Regel, bleibt ihre ID verbraucht, damit alte gespeicherte Empfehlungen nicht plötzlich etwas anderes bedeuten.

Geänderte Defaults in `TargetProfile` sind keine Breaking Changes — alte Messungen bleiben gültig —, aber sie ändern Empfehlungen ohne sichtbaren Anlass und gehören deshalb mit Begründung ins Changelog.

## Tests

Jede Rechenfunktion bekommt mindestens einen Test mit synthetischem Signal, dessen Ergebnis analytisch bekannt ist: Sinus bekannter Amplitude, weißes Rauschen bekannter Leistung, Stille, ein Sinus mit definierter Pause für das Gating.

Dazu ein Golden Test: ein deterministisch erzeugtes Signal, dessen vollständiges `Measurement` als JSON im Repository liegt. Er schlägt fehl, sobald sich ein Rechenweg unbeabsichtigt ändert — genau der Fall, der sonst erst Monate später als unerklärliche Abweichung auffällt.

Roundtrip-Test für `to_dict()` / `from_dict()` auf jedem Modell.

Empfehlungsregeln werden nicht aus Audio getestet, sondern aus von Hand konstruierten `Measurement`-Objekten: je Regel eines knapp über der Schwelle, das sie auslöst, und eines knapp darunter, das sie nicht auslöst. Das hält die Tests schnell und macht die Schwellen im Test sichtbar, statt sie im Code zu verstecken. Dazu ein Golden Test auf ein vollständiges `Advice` und ein Test, der die Eindeutigkeit aller Suggestion-IDs prüft.

Ein Test stellt sicher, dass `measure` und `batch` keine Empfehlungen ausgeben. Diese Trennung geht sonst als bequeme Kleinigkeit verloren.

Keine echten Audiodateien im Repository.
