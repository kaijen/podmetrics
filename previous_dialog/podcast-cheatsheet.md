# Podcast-Cheat-Sheet

Setup: Shure MV7 / MV7X → Zoom PodTrak P4next → Ultraschall (REAPER 6.83)

## Vor jeder Aufnahme

- Mikrofonabstand 5–10 cm zur Stirnseite. Bei Bart: seitlich versetzt, nicht näher.
- Achse zeigt auf den Mund. Kontrolle: Handy vor die Lippen halten, Foto Richtung Mikro. Die Stirnfläche muss als Kreis erscheinen, nicht als Ellipse.
- Seitlicher Versatz gegen Plosive — aber die Kapsel dabei auf den Mund zurückdrehen. Wegdrehen kostet Höhen.
- Kein Schaumstoff-Windschutz im Innenraum. Kostet Höhen ab 5 kHz.
- Phantomspeisung aus (dynamische Mikrofone).
- AI Noise Reduction, Tone, Comp am P4next aus. Gerätebearbeitung ist unwiderruflich.
- Testaufnahme 30 s mit normalem Sprechen und einer bewusst lauten Stelle.
- Gain so, dass laute Stellen zwischen −12 und −6 dBFS liegen.
- Am Ende 30 s Stille aufnehmen als Rauschprofil.

Jede Änderung an Mikrofon, Position, Sprecher oder Sitzhaltung macht die alte Gaineinstellung ungültig.

## Grundregeln

- Zu leise aufnehmen ist ein kleiner Fehler, zu laut ein großer. Lautheit lässt sich nachträglich herstellen, abgeschnittene Spitzen nicht.
- Plosivspitzen sind kein Maßstab für den Gain. Sie sitzen unter 120 Hz und werden vom Hochpass entfernt. Auf den Sprachpegel achten, nicht auf Einzelausschläge.
- Beim Beurteilen die Abhörlautstärke nicht verändern.
- Immer nur eine Größe ändern, dann messen.
- Vor Vorher-Nachher-Vergleichen die Lautstärke angleichen. Lauter klingt fast immer besser.

## Zielwerte

| Kennwert | Ziel |
|---|---|
| Spitzen bei der Aufnahme | −12 bis −6 dBFS |
| Spitzen der bearbeiteten Sprachspur | ca. −1,5 dBFS |
| Dynamikspanne (P10–P90) | 14–15,5 dB |
| Rauschteppich | nicht über −48 dB |
| Blockbalance (Lautheitsunterschied zwischen Abschnitten) | unter 1 dB |
| Endlautheit der fertigen Datei | −16 LUFS |
| Limiter beim Rendern | −1 dB |

## FX-Kette (Reihenfolge zählt)

ReaEQ → ReaComp. Hochpass immer als erstes Glied, sonst reagiert der Kompressor auf Plosivenergie, die später wegfällt.

### ReaEQ — Profil „Kai MV7“

| Band | Typ | Frequenz | Gain | Bandbreite |
|---|---|---|---|---|
| 1 | High Pass | 80 Hz | — | Standard |
| 2 | Band | ca. 200 Hz | +3 dB | 1,2 |
| 3 | Band | 350 Hz | −3 dB | 1,0 |
| 4 | Band | ca. 4 kHz | +4 dB | 1,5 |
| 5 | Band | 9,8 kHz | +0,9 dB | 2,0 |

Ausgangs-Gain: −2 dB. Jede Anhebung im EQ erhöht den Spitzenpegel und muss am Ausgang ausgeglichen werden.

Ein eigenes Profil pro Kombination aus Sprecher und Mikrofon. Ultraschall-Presets sind fremde Vorannahmen, nicht auf die eigene Stimme abgestimmt.

### ReaComp

| Parameter | Wert |
|---|---|
| Ratio | 3:1 |
| Attack | 8 ms |
| Release | 100–120 ms |
| Pre-comp | 0 ms |
| Knee size | 3 dB |
| RMS size | 5 ms |
| Lowpass | 20000 Hz |
| Highpass | 63 Hz |
| Detector input | Main Inputs |
| Auto release / Weird knee / Auto make-up | aus |
| Threshold | ca. 3 dB unter dem Medianpegel der Sprache |
| Wet | so, dass die Spur bei −1,5 dBFS landet |

Der Threshold ist der einzige Wert, der bei jeder neuen Aufnahme geprüft werden muss — er ist absolut und hängt vom Aufnahmepegel ab. Alle anderen Werte bleiben.

Prüfung: Chain laden, 30 s normale Sprache abspielen, Reduktionsbalken beobachten. Ziel sind 4–6 dB im Mittel, höchstens 8 bei Ausreißern. Der Wert unten am Balken ist der gehaltene Maximalwert, nicht der laufende — vor jedem Durchgang durch Klick zurücksetzen.

## Rendern

- Source: Master mix, Bounds: Entire project
- WAV 24 Bit für Material, das weiterverarbeitet wird
- Normalize aktivieren, Modus LUFS-I, Ziel −16
- Brickwall-Limit auf −1 dB, sonst Intersample-Peaks bei späterer MP3-Kodierung
- Masterfader auf 0.0 kontrollieren (Strg-Klick setzt zurück)
- Uhrzeit oder Nummer an den Dateinamen hängen, um Versionen unterscheiden zu können
- Ergebnis einmal komplett anhören

## Fehlerbilder

| Symptom | Ursache | Abhilfe |
|---|---|---|
| Klingt wie durch ein Rohr | Kammfilter: Signal trifft auf verzögerte Kopie | Monitorweg schließen, Tischreflexion dämpfen, 3:1-Regel einhalten |
| Wenig Höhen, viel Bass | Mikrofonachse zeigt am Mund vorbei | Achse auf den Mund richten |
| Dumpf und entfernt | Zu großer Abstand | Näher heran, Gain zurück |
| Flach, ohne Kontur | Nur Mitten vorhanden | Volumen bei 150–200 Hz und Präsenz bei 3–4 kHz anheben, 350 Hz absenken |
| Rauschen in den Pausen | Kompression zu stark | Threshold anheben |
| Pumpen, Atmen im Hintergrund | Release zu kurz | Auf 150 ms erhöhen |
| Stumpfe Konsonanten | Attack zu kurz | Auf 8 ms setzen |
| Leblos, monoton | Threshold zu tief oder Ratio zu hoch | Zurücknehmen |
| Clipping nach EQ-Änderung | Anhebung nicht ausgeglichen | Ausgangs-Gain um denselben Betrag senken |

## Aufnahme zu zweit

- 3:1-Regel: Mikrofonabstand mindestens dreimal so groß wie der Sprechabstand.
- Rückseite der Niere zur jeweils anderen Person.
- Filz oder Handtuch unter Stativfüße gegen Körperschall und Tischreflexion.
- Kontrolle: eine Person spricht, die andere schweigt. Der stumme Kanal muss deutlich unter der Hälfte des Ausschlags bleiben.
- Bei Headsets: Mikrofonkanäle während der Aufnahme muten. Der P4next zeichnet die Einzelspuren unabhängig vom Mute-Status auf.

## Messen

- SWS-Lautheitsanalyse in Ultraschall: Items markieren, Actions-Liste, Filter „loudness“. Liefert Peak, True Peak, LUFS-I, Loudness Range.
- Youlean Loudness Meter als kostenloses Plugin auf dem Master für laufende Anzeige mit Verlaufskurve.
- Rauschteppich: eine Sprechpause markieren und dort die Lautheitsanalyse laufen lassen.

## Sprechtechnik

- Abstand konstant halten. Zurücklehnen kostet 6 dB und Bassanteil.
- Pegel bis zum Satzende halten. Absacken am Satzende ist der häufigste Fehler.
- Pausen stehen lassen. Eine Sekunde Stille fühlt sich beim Sprechen endlos an und klingt normal.
- Zum Mikrofon sprechen, die andere Person ansehen.
- Aufnahmen durchhören, nicht nur abhaken. Das ist der Schritt, an dem sich entscheidet, ob man besser wird.
