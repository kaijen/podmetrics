# Konzept

## Was hineingehört

Alles, was aus Audio Zahlen macht: Gating, Pegelstatistik, Lautheit, Spektrum, die
Vergleichsrechnung zweier Messungen, die Berechnung des Gainfaktors für eine
Pegelangleichung.

Dazu alles, was aus diesen Zahlen folgt: Empfehlungen zur Mikrofonposition, zu EQ- und
Kompressoreinstellungen, die Eignungsprüfung einer Referenz. Diese Rechnungen sehen keine
Samples, sondern nur fertige Messwerte. Sie gehören hierher, weil sie dieselben Kennwerte
lesen, die hier entstehen — und weil eine Empfehlung, die anderswo gerechnet wird, die
Schwellen dorthin kopiert und damit zwei Wahrheiten schafft.

## Was nicht hineingehört

Dateiverwaltung über den Einzelaufruf hinaus, Datenbank, HTTP, Take-Identitäten,
Referenzverwaltung als Zustand, Bedienoberfläche, das Ausspielen von Audio, das Anwenden
einer Empfehlung, das Schreiben von REAPER- oder Ultraschall-Dateien wie FX-Chains und
Trackvorlagen.

Zwei Grenzfälle zeigen, wo die Linie liegt:

`gain_for_target_lufs()` gehört hierher, weil es eine Rechnung ist. Das Anwenden dieses
Faktors und das Streamen der Datei an einen Browser gehört in die Webapp.

Eine ReaComp-Einstellung zu berechnen gehört hierher. Sie in ein Ultraschall-Projekt zu
schreiben nicht. Die Werte stehen in der Ausgabe und werden von Hand eingetragen; der Weg
ist kurz genug, und die Bibliothek bleibt frei von Projektwissen. Wer eine `.RfxChain`
schreibt, hat eine Dateiübernahme gebaut und pflegt ab dann REAPER-Versionen hinterher.

Braucht die Webapp eine Zahl, die es hier noch nicht gibt, wird sie hier ergänzt und nicht
dort gerechnet. Doppelte DSP-Logik in zwei Repositories ist der Fehler, den diese Trennung
verhindern soll.

## Schichtung

```
models          kennt niemanden
  ↑
io  gating  levels  loudness  spectrum  compare     kennen models, numpy/scipy —
  ↑                                                  aber nicht einander
advice          kennt models, sonst nichts
  ↑
report  cli     kennen alles
```

`models` kennt niemanden. Die Rechenmodule kennen nur `models` und numpy/scipy, nicht
einander; ein Rechenmodul, das ein anderes importiert, ist ein Hinweis auf einen falschen
Schnitt.

`advice` steht eine Schicht höher und kennt `models` und sonst nichts — insbesondere kein
`Signal`, kein soundfile, kein scipy. Ein Import von numpy dort ist bereits ein
Warnzeichen, ein Zugriff auf Samples ein Fehler. Empfehlungen müssen aus den
veröffentlichten Zahlen ableitbar sein, notfalls von Hand auf Papier. Was nur aus dem
Signal folgt, ist ein fehlender Kennwert und gehört in ein Rechenmodul.

## Messregeln

Diese Regeln sind Festlegungen, keine Vorschläge. Sie stehen hier, weil eine Messung ohne
ihre Regeln nicht vergleichbar ist.

**Sprechpausen werden entfernt, bevor gemessen wird.** Vor jeder Pegelstatistik und vor
allem Spektralen. Stille mischt dem Spektrum einen Rauschanteil bei und zieht die
Pegelverteilung mit einem Schwanz sehr leiser Werte nach unten, was den Median verschiebt.
Gating gegen −45 dBFS auf gleitendem RMS, Segmente unter 100 ms werden verworfen.

**True Peak wird 4-fach oversampled berechnet**, per `scipy.signal.resample_poly`.
pyloudnorm liefert keinen True Peak, und der Sample-Peak übersieht Intersample-Spitzen.

**LUFS-I braucht mindestens 30 Sekunden**, sonst greift das Gating nach ITU-R BS.1770
unzuverlässig. Kürzeres Material wird gemessen, aber als unzuverlässig markiert — nicht
stillschweigend geliefert und nicht verweigert.

**Der Rauschteppich wird nur in einem ausdrücklich übergebenen Bereich gemessen.** Ohne
`noise_region` bleibt das Feld leer. Die Bibliothek sucht sich keine Pause selbst; welcher
Abschnitt eine echte Sprechpause ist und nicht ein Atmer oder das Rascheln von Papier,
weiß nur der Nutzer.

**Terzband-Energien werden auf ihren eigenen Mittelwert normiert**, damit sie unabhängig
vom Aufnahmegain vergleichbar sind. Aussagekräftig ist die Differenzkurve zur Referenz,
nicht die Absolutkurve.

**Mehrkanaliges Material wird beim Laden auf einen Kanal reduziert**, und der Kanal ist
ausdrücklich anzugeben statt zu mischen. Die Summierung zweier Sprecherkanäle erzeugt
Kammfiltereffekte, die als Spektrum-Auffälligkeit im Messergebnis landen und dort nach
einem Aufnahmefehler aussehen. Diese Entscheidung hat eine Folge für die Lautheit, die
in den [Zielwerten](zielwerte.md#der-3-db-fehler) steht.

**Fenster:** gleitendes RMS 200 ms bei 50 % Überlappung, Short-Term-Lautheit 3 s gleitend.

## Was gemessen wird und was entschieden bleibt

Der Median-Sprechpegel und die Spanne P10–P90 werden mitgeliefert, weil daraus der
Kompressor-Threshold folgt. Die Messmodule schlagen keinen Threshold vor — die Umrechnung
hängt von Ratio und Zielspanne ab und ist eine Entscheidung, keine Messung.

Diese Entscheidung wird nicht verschwiegen, sondern verlagert: Sie fällt im
Empfehlungsteil, gegen ein ausdrücklich übergebenes Ziel und mit genannter Zielspanne. Ein
Messwert bleibt ein Messwert, auch wenn eine Schicht darüber ein Vorschlag daraus
gerechnet wird.

## Versionierung

SemVer für das Paket. Daneben zwei getrennt geführte Zähler:

`Measurement.schema_version` steigt, wenn Felder wegfallen oder ihre Bedeutung sich ändert.
Die Webapp speichert Messungen dauerhaft und muss alte Datensätze erkennen können.

`Advice.ruleset_version` steigt, sobald sich Regeln, Schwellen oder die Bedeutung einer
Suggestion-ID ändern. Eine ID wird nie wiederverwendet: Verschwindet eine Regel, bleibt
ihre ID verbraucht, damit alte gespeicherte Empfehlungen nicht plötzlich etwas anderes
bedeuten.

Änderungen an Default-Werten in `AnalysisParams` sind Breaking Changes, auch wenn sich
keine Signatur ändert — jede solche Änderung entwertet alle früheren Vergleiche. Geänderte
Defaults in `TargetProfile` sind keine Breaking Changes, alte Messungen bleiben gültig;
sie ändern aber Empfehlungen ohne sichtbaren Anlass und gehören deshalb mit Begründung
ins Changelog.

## Abhängigkeiten

numpy, scipy, soundfile, pyloudnorm. Für die CLI zusätzlich typer und rich als Extra
`podmetrics[cli]`, damit die Bibliothek als Webapp-Dependency ohne Terminal-Ballast
installierbar bleibt.

Kein librosa: zu viel Ballast für Funktionen, die hier nicht gebraucht werden. Jede
zusätzliche Abhängigkeit verlängert die Startzeit eines Aufrufs, der zwanzigmal am Tag
vorkommt.
