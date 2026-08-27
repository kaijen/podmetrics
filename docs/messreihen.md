# Messreihen

Die Zielwerte und Empfehlungsregeln dieser Bibliothek stammen nicht aus Lehrbüchern,
sondern aus einer Messreihe an eigenem Material: Shure MV7 am Zoom PodTrak P4next,
bearbeitet in Ultraschall (REAPER 6.83). Das vollständige Protokoll liegt im Repository
unter `previous_dialog/`.

Diese Seite hält fest, was daraus belegt ist — und was daraus für den Code folgt.

## Mikrofonachse

Sechs Versuche, Spektralmessung jeweils im Sprachabschnitt 11,8–15,0 s, Referenz ist
Version 002.

| Version | Position | 4–8 kHz | 8–12 kHz | Rauschteppich |
| --- | --- | ---: | ---: | ---: |
| 002 | zufällig getroffen, Referenz | 0 dB | 0 dB | −57,5 dB |
| 004 | Achse auf die Nase | −5,8 dB | −8,6 dB | −56,4 dB |
| 005 | seitlich versetzt, Achse daneben | −9,1 dB | −13,0 dB | −46,1 dB |
| 006 | korrigiert | −7,0 dB | −6,9 dB | −54,4 dB |

**Was das für die Regel `position.off_axis` bedeutet:** Der Höhenabfall beim Sprechen an
der Achse vorbei ist groß — 6 bis 13 dB, nicht ein bis zwei. Der Grund ist, dass zweimal
Höhen verloren gehen: an der Richtcharakteristik der Niere und an der eigenen Abstrahlung,
denn auch der Mund strahlt oberhalb von 4 kHz gerichtet ab, darunter kugelförmig.

Deshalb werden **zwei Bänder getrennt ausgewiesen**, 4–8 kHz und 8–12 kHz. Fällt das obere
stärker ab als das untere, ist das die Signatur der Achse; ein gleichmäßiger Abfall über
beide Bänder deutet eher auf Abstand oder Windschutz.

Die Schwelle steht damit auf Daten und nicht auf Gefühl: −3 dB in 4–8 kHz ist auffällig,
−6 dB ist der Grund, warum der Take anders klingt.

## Plosive

Version 006, Spitze bei 6,818 s:

| Frequenzbereich | Energieanteil der Spitze | Blockdurchschnitt |
| --- | ---: | ---: |
| 20–60 Hz | 10,1 % | — |
| 60–120 Hz | 85,5 % | — |
| 120–250 Hz | 3,7 % | — |
| über 250 Hz | 0,4 % | — |
| **unter 120 Hz gesamt** | **95,6 %** | **28,7 %** |

Ein Hochpass bei 80 Hz senkt dieselbe Spitze von −0,16 auf −2,23 dBFS, ohne hörbaren
Verlust an der Stimme.

**Was das für den Code bedeutet:** Ein Plosiv ist messbar und braucht keine geratene
Ursache. Das Kriterium ist der Vergleich des Tieftonanteils einer Spitze mit dem
Tieftonanteil des umgebenden Sprachblocks. Liegt er um ein Vielfaches darüber, ist die
Spitze ein Luftstoß und kein lauter Laut.

Daraus folgen zwei Dinge, die vorher fehlten: Plosivspitzen werden aus der
Peak-Bewertung herausgerechnet, statt eine Übersteuerungswarnung auszulösen. Und die
Empfehlung bei zu hohem Peak lautet dann „Hochpass setzen", nicht „Gain zurücknehmen".

## Kompressor

Die längste Einstellarbeit der Reihe, mit den lehrreichsten Sackgassen.

| Version | Einstellung | Peak | LUFS | Rauschteppich | P10–P90 |
| --- | --- | ---: | ---: | ---: | ---: |
| 010 | ohne Kompressor | −4,23 | −20,86 | −60,5 | 18,5 dB |
| 012 | Threshold −21, Lowpass korrigiert | 0,00 | −17,89 | **−32,5** | 13,5 dB |
| 015 | Threshold −16 | 0,00 | −16,90 | −55,5 | 17,7 dB |
| 016 | Kompressor aus (Kontrolle) | −0,74 | −17,78 | −57,5 | 18,7 dB |
| 017 | Ratio 4:1 | −0,12 | −17,14 | −55,5 | 17,6 dB |
| 018 | Ratio 3:1, Threshold −20 | −1,43 | −18,60 | −55,5 | 17,2 dB |
| 019 | Threshold −30 (Extremtest) | −5,89 | −24,72 | −60,1 | 13,6 dB |
| **020** | **Threshold −24, Wet nachgezogen** | **−1,51** | **−19,85** | −55,2 | **15,4 dB** |

### Der Denkfehler, der die Formel festlegt

Der Median-Sprechpegel lag bei etwa −21 dBFS. Ein Threshold von −16 liegt damit
**oberhalb** des Medians — der Kompressor sah nur die obere Hälfte der Sprache, und
zwischen −16 und −20 bewegte sich kaum etwas. Erst der Extremtest bei −30 zeigte, dass
die Kette überhaupt funktioniert, und lieferte den Bezugspunkt.

**Daraus folgt die Regel `comp.threshold`:** Der Threshold gehört rund 3 dB **unter** den
Median-Sprechpegel. Die Richtung ist der eigentliche Inhalt der Regel; sie war vorher
offen, und ohne sie ist die Empfehlung wertlos.

Der Threshold ist außerdem der einzige Wert, der bei jeder neuen Aufnahme geprüft werden
muss — er ist absolut und hängt vom Aufnahmepegel ab. Alle anderen Werte bleiben.

### Der zuverlässigste Kontrollwert

Version 012 hatte einen ordentlichen Lautheitswert und eine schöne Dynamikspanne — und
war trotzdem unbrauchbar, weil der Rauschteppich auf −32,5 dB hochgezogen war. Der
Rauschteppich ist damit das objektive Maß für „zu stark komprimiert", zuverlässiger als
das Gehör: Stärkere Kompression klingt zunächst voller, der Preis fällt erst in den
Pausen auf.

### Endstand

| Parameter | Wert |
| --- | --- |
| Ratio | 3:1 |
| Attack | 8 ms |
| Release | 100–120 ms |
| Knee size | 3 dB |
| RMS size | 5 ms |
| Pre-comp | 0 ms |
| Highpass / Lowpass des Detektors | 63 Hz / 20000 Hz |
| Detector input | Main Inputs |
| Auto release, Weird knee, Auto make-up | aus |
| Threshold | ca. 3 dB unter dem Median-Sprechpegel |
| Wet | so, dass die Spur bei −1,5 dBFS landet |

!!! warning "Zwei Fallen aus der Reihe, die keine Messfehler waren"

    Der Lowpass des Detektors stand auf 2000 Hz — der Kompressor sah nur 63 bis 2000 Hz
    und reagierte kaum. Und die Zahl unter dem Reduktionsbalken ist der gehaltene
    Maximalwert, nicht der laufende Wert.

## EQ

Das Profil „Kai MV7", das die Reihe hervorgebracht hat:

| Band | Typ | Frequenz | Gain | Bandbreite |
| --- | --- | ---: | ---: | ---: |
| 1 | High Pass | 80 Hz | — | Standard |
| 2 | Band | ca. 200 Hz | +3 dB | 1,2 |
| 3 | Band | 350 Hz | −3 dB | 1,0 |
| 4 | Band | ca. 4 kHz | +4 dB | 1,5 |
| 5 | Band | 9,8 kHz | +0,9 dB | 2,0 |

Ausgangs-Gain −2 dB.

**Drei Folgen für den Code:**

ReaEQ arbeitet mit **Bandbreite in Oktaven**, nicht mit Q. Die Ausgabe muss Bandbreite
nennen, sonst ist sie nicht eintragbar.

Es sind **vier Glocken**, nicht drei. Die Obergrenze im Profil steht deshalb auf vier.
Alle Gains liegen innerhalb von ±4 dB, was die bisherige Grenze bestätigt.

**Jede Anhebung erhöht den Spitzenpegel.** Version 007 clippte an 54 Samples, weil der
Ausgangs-Gain nicht nachgezogen war. Ein EQ-Vorschlag ohne die zugehörige
Ausgangspegel-Korrektur ist deshalb unvollständig, und die Bibliothek gibt ihn nicht ohne
sie aus.

Der diagnostische Befund dahinter ist ebenfalls festgehalten: „flach" bedeutete nicht
„zu leise überall", sondern fehlender Kontrast — nur Mitten vorhanden. Die Abhilfe war
Fundament anheben, untere Mitten absenken, Präsenz anheben, nicht alles gleichmäßig
lauter machen.

## Kammfilter

Der teuerste Fehler der ganzen Reihe, und der einzige, den keine der bisherigen Regeln
gefunden hätte. Die Aufnahme klang „wie durch ein Rohr". Ursache war eine
Rückkopplungsschleife: Das Monitorsignal gelangte über Luftschall aus den Ohrmuscheln und
über Körperschall durch Bügel und Schwanenhals zurück in die Kapsel. Die Durchlaufzeit
des P4next von ein bis drei Millisekunden schob den ersten Einbruch auf 170 bis 500 Hz,
also mitten ins Sprachband.

**Was das für den Code bedeutet:** Ein Kammfilter hat eine eindeutige Signatur — Einbrüche
in gleichmäßigem Frequenzabstand, bei einer Verzögerung von 1 ms also alle 1000 Hz. Das
ist messbar, aber **nicht in Terzbändern**: Deren Auflösung mittelt die Einbrüche weg.
Der Nachweis braucht die feiner aufgelöste Welch-PSD und eine Prüfung auf Periodizität
über der Frequenz.

Die Tiefe der Einbrüche verrät zugleich den Pegelabstand der verzögerten Kopie: bei 6 dB
Abstand schwankt das Spektrum um rund 9 dB, bei 20 dB Abstand um weniger als 2 dB.

## Was noch fehlt

Die Reihe belegt einen Kennwert, den podmetrics noch nicht hat und der ohne Audio nicht
zu haben ist: eine **Nachhallschätzung**. Sie bleibt zurückgestellt — anders als Plosive
und Kammfilter ist bisher kein robustes Verfahren aus dem vorhandenen Material
abgeleitet.

Offen ist außerdem, ob die hier genannten Schwellen für eine zweite Stimme tragen. Alle
Zahlen stammen aus **einer** Stimme an **einem** Mikrofon. Das ist genug, um die
Richtungen festzulegen, und zu wenig, um die Schwellen für andere Sprecher zu behaupten.
