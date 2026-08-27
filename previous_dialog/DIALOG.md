# Gesprächsprotokoll: Vom Rohrklang zum fertigen Jingle

Aufzeichnung eines Arbeitsgesprächs über Podcast-Aufnahme und -Bearbeitung.
Setup: Superlux HMD-660X → Shure MV7 → Zoom PodTrak P4next → Ultraschall (REAPER 6.83).

Dies ist kein wörtliches Transkript, sondern ein geordnetes Protokoll: Fragen,
Befunde, Messwerte, Entscheidungen und die Stellen, an denen ich falsch lag.

---

## 1. Das Ausgangsproblem: „hallig"

**Frage:** Aufnahme mit zwei HMD-660 am P4next klingt hallig.

Erste Diagnose ging von einem Sennheiser-Broadcast-Headset mit
geräuschkompensierender Gradientenkapsel aus — falsch. Es war ein Superlux HMD-660X
mit einfacher Nierenkapsel (PRA20, 150–10.000 Hz, niedrige Empfindlichkeit).

Damit fiel das Argument „Headsetmikro ist immun gegen Diffusschall" weg.

**Präzisierung durch Nachfrage:** Der Klang war nicht hallig im Sinne von Nachhall,
sondern „wie durch ein Rohr" — und er wurde besser bei mehr Gain und weniger Monitor.

**Befund:** Kammfilter durch eine Rückkopplungsschleife. Das Monitorsignal gelangt
über zwei Wege zurück in die Kapsel — als Luftschall aus den Ohrmuscheln und als
Körperschall über Bügel und Schwanenhals. Die Durchlaufzeit des P4next von ein bis
drei Millisekunden dominiert dabei und schiebt den ersten Einbruch auf 170 bis
500 Hz, also mitten ins Sprachband.

**Lösung:** Mikrofonkanäle während der Aufnahme muten. Der P4next zeichnet die
Einzelspuren unabhängig vom Mute-Status auf.

---

## 2. Hardware-Entscheidungen

| Frage | Ergebnis |
|---|---|
| HMC-660C (Kondensator) als Upgrade? | Nein. Kapsel für 1,5–9 V spezifiziert, P4next liefert nur 48 V. Kompatibilitätsrisiko, und die Rückkopplungsgeometrie bleibt identisch. |
| MV7 oder MV7X als zweites Mikro? | MV7X kaufen, für den eigenen Platz. Das vorhandene MV7 wandert auf die Gastposition und behält seine USB-Fähigkeit für Termine ohne P4next. |
| MD 42? | Kugelcharakteristik, für Interviews unterwegs richtig, für sitzendes Gespräch im Raum ungeeignet. Gegenstück mit Niere wäre MD 46. |
| Gaststativ | Bodenstativ mit Galgen statt Tischstativ, weil der Gast auf dem Sofa sitzt. TAMA MS736BK: 5,4 kg, 975–1650 mm, vibrationsisolierende Füße — passt. |
| Externe Spinne nötig? | Nein. MV7 und MV7X haben eine interne Kapselaufhängung. Meine ursprüngliche Empfehlung war überzogen. |
| Mobil | Vorerst bei den vorhandenen HMD-660X bleiben. Unterwegs ist der fremde Raum das größere Problem als die begrenzte Bandbreite. |

---

## 3. Die Mikrofonachse — die längste Fehlersuche

Sechs Versuche, jeweils mit Spektralmessung im Sprachabschnitt 11,8–15,0 s.
Referenz ist Version 002.

| Version | Position | 4–8 kHz | 8–12 kHz | Rauschteppich |
|---|---|---|---|---|
| 002 | zufällig getroffen, Referenz | 0 dB | 0 dB | −57,5 dB |
| 004 | Achse auf die Nase | −5,8 dB | −8,6 dB | −56,4 dB |
| 005 | seitlich versetzt, Achse daneben | −9,1 dB | −13,0 dB | −46,1 dB |
| 006 | korrigiert | −7,0 dB | −6,9 dB | −54,4 dB |

**Das Muster:** Viel Bass bei wenig Höhen ist die Signatur einer Niere, die außerhalb
ihrer Achse besprochen wird. Tiefe Frequenzen nimmt sie aus allen Richtungen auf,
hohe fast nur von vorn.

**Der zweite Effekt:** Auch der Mund strahlt gerichtet ab. Oberhalb von 4 kHz in einer
nach vorn gerichteten Keule, darunter kugelförmig. Beim Vorbeisprechen verliert man
deshalb zweimal Höhen — an der Mikrofonachse und an der eigenen Abstrahlung. Deshalb
kamen 8,6 dB zusammen und nicht ein bis zwei.

**Wichtige Unterscheidung:** Seitlicher Versatz gegen Plosive heißt nicht, die Achse
wegzudrehen. Man verschiebt die eigene Position, dreht die Kapsel aber auf den Mund
zurück. Auf die Nase zu zielen ist eine gängige Empfehlung — nur nicht zusätzlich zum
seitlichen Versatz.

**Kontrolle:** Handy vor die Lippen halten, Foto Richtung Mikrofon. Die Stirnfläche
muss als Kreis erscheinen, nicht als Ellipse. Ein Selfie aus der Seitenansicht
beantwortet die Frage nicht, weil es aus der Kameraposition fotografiert und nicht
aus der Schallquelle.

**Abstandsgrenze:** Näher als etwa eine Handbreit ging nicht, weil Barthaare den Korb
berühren. Kratzgeräusche direkt an der Kapsel sind schlimmer als jeder Nachteil des
größeren Abstands — also bleibt der Abstand, und die Dynamik wird über den Kompressor
geregelt.

---

## 4. Aussteuerung und Plosive

Der Mikrofonwechsel machte die alte Gaineinstellung ungültig. Version 001 clippte an
48 Samples, weil das MV7 bei gleichem Gain erheblich mehr Pegel liefert als die
Superlux-Kapsel.

**Plosiv-Analyse, Version 006, Spitze bei 6,818 s:**

| Frequenzbereich | Energieanteil |
|---|---|
| 20–60 Hz | 10,1 % |
| 60–120 Hz | 85,5 % |
| 120–250 Hz | 3,7 % |
| über 250 Hz | 0,4 % |

Im Blockdurchschnitt liegen dagegen nur 28,7 % unter 120 Hz. Die Spitze ist also kein
lauter Laut, sondern ein Luftstoß.

Ein Hochpass bei 80 Hz senkt sie von −0,16 auf −2,23 dBFS, ohne dass an der Stimme
etwas fehlt. Daraus folgt: Plosivspitzen sind kein Maßstab für den Gain.

---

## 5. Der Equalizer

Ultraschall lädt auf den Spuren ein Preset („Ultraschall3") mit fünf Bändern:
Tiefenfilter als Band bei 23,9 Hz mit −120 dB, Einschnitt bei 1 kHz, kontinuierlicher
Anstieg ab 2 kHz, High Shelf bei 11,5 kHz. Das ist eine drastische Kurve und nicht auf
eine bestimmte Stimme abgestimmt.

**Ersetzt durch das Profil „Kai MV7":**

| Band | Typ | Frequenz | Gain | Bandbreite |
|---|---|---|---|---|
| 1 | High Pass | 80 Hz | — | Standard |
| 2 | Band | ca. 200 Hz | +3 dB | 1,2 |
| 3 | Band | 350 Hz | −3 dB | 1,0 |
| 4 | Band | ca. 4 kHz | +4 dB | 1,5 |
| 5 | Band | 9,8 kHz | +0,9 dB | 2,0 |

Ausgangs-Gain −2 dB.

**Zwischenstand mit „flach":** Die Partnerin beschrieb die Stimme als flach. Auf
Nachfrage: Mischung aus fehlendem Volumen und fehlender Präsenz — also nur Mitten
vorhanden. Die Abhilfe war nicht, alles anzuheben, sondern Kontrast zu erzeugen:
Fundament anheben, untere Mitten absenken, Präsenz anheben.

Band 5 mit +0,9 dB kam von dir und war die richtige Entscheidung. Der Typwechsel bei
Band 4 von Shelf auf Glocke hatte Luftigkeit gekostet; das schmale Band holt sie
zurück, ohne die Präsenzspitze aufzugeben.

**Regel:** Jede Anhebung im EQ erhöht den Spitzenpegel. Version 007 clippte an
54 Samples, weil der Ausgangs-Gain nicht nachgezogen war.

---

## 6. Der Kompressor

Die längste Einstellarbeit, mit mehreren Sackgassen.

| Version | Einstellung | Peak | LUFS | Rauschteppich | Dynamikspanne |
|---|---|---|---|---|---|
| 010 | ohne Kompressor | −4,23 | −20,86 | −60,5 | 18,5 dB |
| 011 | erste Fassung | 0,00 | −17,16 | −53,5 | 17,0 dB |
| 012 | Lowpass korrigiert, Threshold −21 | 0,00 | −17,89 | −32,5 | 13,5 dB |
| 015 | Threshold −16 | 0,00 | −16,90 | −55,5 | 17,7 dB |
| 016 | Kompressor aus (Kontrolltest) | −0,74 | −17,78 | −57,5 | 18,7 dB |
| 017 | Ratio 4:1 | −0,12 | −17,14 | −55,5 | 17,6 dB |
| 018 | Ratio 3:1, Threshold −20 | −1,43 | −18,60 | −55,5 | 17,2 dB |
| 019 | Threshold −30 (Extremtest) | −5,89 | −24,72 | −60,1 | 13,6 dB |
| 020 | Threshold −24, Wet nachgezogen | −1,51 | −19,85 | −55,2 | 15,4 dB |

**Falle 1:** Lowpass stand auf 2000 Hz. Der Kompressor sah damit nur den Bereich
63–2000 Hz und reagierte kaum. Muss auf 20000 stehen.

**Falle 2:** Die Zahl unten am Reduktionsbalken ist der gehaltene Maximalwert, nicht
der laufende. −10,7 dort bedeutete nicht, dass der Kompressor durchgehend so stark
eingreift.

**Falle 3 — der eigentliche Denkfehler:** Der Medianpegel der Sprache lag bei etwa
−21 dB. Ein Threshold von −16 liegt also *oberhalb* des Medians; der Kompressor sah
nur die obere Hälfte der Sprache. Deshalb bewegte sich zwischen −16 und −20 kaum etwas.
Erst der Extremtest bei −30 zeigte, dass alles funktioniert, und lieferte den
Bezugspunkt für den richtigen Wert.

**Kontrollwert Rauschteppich:** Ein Kompressor hebt Raum, Rauschen und Atem mit an.
Steigt der Rauschteppich über etwa −48 dB, ist der Eingriff zu stark. Das ist ein
objektives Kriterium und zuverlässiger als das Gefühl, weil stärkere Kompression
zunächst voller klingt.

**Endstand:** Ratio 3:1, Attack 8 ms, Release 100 ms, Pre-comp 0, Knee 3 dB,
RMS size 5 ms, Lowpass 20000, Highpass 63, Detector Main Inputs, Auto make-up und
Weird knee aus, Threshold −24, Wet so, dass die Spur bei −1,5 dBFS landet.

---

## 7. Musik und Ducking

Beim Jingle mit fünf bekannten Einsätzen ist die Lautstärke-Hüllkurve dem
Sidechain-Kompressor überlegen: volle Kontrolle über jeden Übergang, kein Pumpen.

Der Sidechain lohnt sich, wenn Sprache und Musik unvorhersehbar ineinanderlaufen —
Live-Betrieb mit Soundboard, durchgehende Hintergrundmusik.

**Zwei Größen, die man leicht verwechselt:**

- Zwischen den Abschnitten: Musik-allein und Sprache sollen gleich laut wirken,
  innerhalb von etwa 1 dB.
- Musik unter der Sprache: 10 bis 15 dB Abstand.

Ich hatte diese beiden zwischenzeitlich vermischt und −19,5 LUFS für die abgesenkte
Musik genannt — das war falsch, bei gleicher Lautheit deckt die Musik die Stimme zu.

---

## 8. Wo ich falsch lag

Vollständigkeitshalber, weil die Korrekturen Teil des Lernwegs waren.

| Behauptung | Richtigstellung |
|---|---|
| „Edit → Select all items" | Heißt „Select all items/tracks/envelope points", Strg+A, und markiert alles im Projekt. |
| Lasso durch Linksziehen | Linksziehen erzeugt eine Time-Selection. Das Marquee liegt auf der rechten Maustaste. |
| Die Spur ist nicht auf den Master geroutet | Matrix falsch gelesen, um eine Zeile verschoben. Das Routing war korrekt. |
| Version 013 sei die alte Datei | Aus übereinstimmenden Kennwerten auf Identität geschlossen — unzulässig. Die md5-Prüfung zeigte unterschiedliche Dateien. |
| MV7X braucht eine externe Spinne | Hat eine interne Kapselaufhängung. |
| DT-770-Polster als Verbesserung | Nur die Kunstleder-Variante. Velours dichtet schlechter ab und verstärkt das Problem. |
| Musik bei −19,5 LUFS unter der Sprache | Verwechslung zweier Größen, siehe oben. |
| Sennheiser-Headset mit Gradientenkapsel | Es war ein Superlux mit einfacher Niere. |

---

## 9. Bewertung eines fremden Vorschlags

**Kompressor als „akustisches Mikroskop"** (Ratio 20:1, schneller Attack, viel
Make-up Gain auf dem Monitorkanal):

Richtig für Raumhall, Lüfterrauschen und Mundgeräusche — ein Kompressor hebt alles
Leise gegenüber dem Lauten an.

Falsch für Plosive: Ein Kompressor mit hoher Ratio und schnellem Attack senkt genau
die Spitzen ab, aus denen ein Plosiv besteht. Er versteckt, was man finden will.

Falsch für den Nahbesprechungseffekt: Das ist eine Verschiebung in der
Frequenzverteilung, kein Pegelunterschied. Bei sehr schnellem Attack folgt der
Kompressor zusätzlich den einzelnen Schwingungen tiefer Frequenzen und erzeugt eigene
Verzerrungen — man beurteilt dann ein Artefakt.

Für die beiden Fälle ist Friture das passende Werkzeug: Terzband-Analysator für die
spektrale Balance, Spektrogramm für Kammfilter. Und es arbeitet visuell, braucht also
keinen Kopfhörer und öffnet keinen Rückkopplungsweg.

---

## 10. Das Format

Wöchentliche Reflexion zu zweit, drei bis vier Themen der Woche, sachlich statt
persönlich.

- Themen im Lauf der Woche sammeln, nicht am Aufnahmetag.
- Wer ein Thema einträgt, moderiert es an. Das verteilt die Vorbereitung.
- Vorher festlegen, wer eröffnet.
- Kurz anfangen: 15 bis 20 Minuten, zwei Themen. Der Engpass ist das Nachhören, nicht
  das Aufnehmen.
- Auf die Redeanteile achten. Bei 80 zu 20 ist aus dem Gespräch ein Wechsel zweier
  Monologe geworden.

---

## 11. Entstandene Dokumente

- `podcast-cheatsheet.md` — Kurzreferenz mit Zielwerten, FX-Ketten und Fehlerbildern
- `tonbearbeitung-grundlagen.typ` — Typst-Quelle des Konzeptdokuments
- `vom-mikrofon-zur-folge.epub` — Buchfassung, 18 Kapitel, 10 Abbildungen
- `DIALOG.md` — dieses Protokoll

---

## 12. Offener nächster Schritt

Aufnahme in der bestätigten Position, Spektralvergleich gegen Version 002. Liegen die
Bänder zwischen 4 und 12 kHz wieder auf Referenzniveau, kann die Höhenanhebung im EQ
zurückgenommen werden — sie war nur die Kompensation eines Positionsfehlers.
