# Arbeitsweise

Diese Seite beschreibt, wie podmetrics gedacht ist zu benutzen. Sie ist die Antwort auf
„ich habe jetzt Zahlen, und nun?".

## Einmal: einen Maßstab schaffen

Ohne Referenz sagen Zahlen wenig. Der erste Schritt ist deshalb, eine Aufnahme zu
bestimmen, die als Maßstab gilt.

1. Nimm mehrere Takes auf, in denen Du bewusst etwas variierst — Abstand, Winkel, Gain.
2. Hör sie ab und wähle den, der Dir am besten gefällt. **Das ist Deine Entscheidung, und
   sie kann Dir niemand abnehmen.**
3. Lass die technische Eignung prüfen:

   ```
   $ podmetrics check-reference take_002.wav --noise 12.4:42.4
   ```

   Ist der Take zu kurz für belastbares LUFS-I, übersteuert oder ohne gemessenen
   Rauschteppich, taugt er nicht als Maßstab — auch wenn er gut klingt. Ein untauglicher
   Maßstab erzeugt lauter Empfehlungen, die alle in dieselbe falsche Richtung zeigen.

4. Friere die Messung ein:

   ```
   $ podmetrics measure take_002.wav --noise 12.4:42.4 --json > referenz-kai.json
   ```

   Diese Datei ist ab jetzt Dein Bezugspunkt. Sie ist klein, sie altert nicht, und Du
   brauchst das Originalmaterial nicht mehr.

!!! warning "Eine Referenz pro Stimme und Mikrofon"

    Beim Aufbau mit zwei MV7 am P4next brauchst Du zwei Referenzen. Eine Differenzkurve
    gegen die Stimme des anderen ist kein Korrekturziel — wer danach filtert, egalisiert
    seine eigene Stimme weg.

## Bei jeder Aufnahme: der Regelkreis

```
aufnehmen → messen → eine Empfehlung umsetzen → wieder aufnehmen → messen
```

```
$ podmetrics advise take_009.wav --reference referenz-kai.json --topic position
```

Setze **eine** Empfehlung um, die oberste. Nimm neu auf. Miss wieder.

Trat die erwartete Änderung ein? Dann war die Vermutung richtig, weiter zur nächsten.
Trat sie nicht ein, war sie falsch — und Du weißt das nach einer Runde statt nach fünf.

Wer Abstand und EQ gleichzeitig ändert, kann die Wirkung keiner Ursache mehr zuordnen und
lernt nichts. Das ist der einzige Grund, warum die Ausgabe sortiert ist.

## Reihenfolge, die nicht verhandelbar ist

**Position → EQ → Kompression → Pegelangleichung.**

Ein EQ, der einen zu geringen Mikrofonabstand kompensiert, hinterlässt eine Stimme, die
dünn klingt, sobald Du Dich einmal richtig hinsetzt. Erst die Aufnahme in Ordnung bringen,
dann die Bearbeitung.

## Beim Rendern: die Nachziehschleife

```
$ podmetrics advise take_009.wav --reference referenz-kai.json --topic eq --topic comp
```

Trage die Werte in ReaEQ und ReaComp ein, rendere, und miss das Ergebnis erneut:

```
$ podmetrics measure render-v1.wav --json
```

Der Makeup-Gain aus der Empfehlung ist ein Startwert. Kompression ändert die Lautheit, also
stimmt der aus der unkomprimierten Messung gerechnete Wert danach nicht mehr. Die
Pegelangleichung auf den Zielwert passiert **nach** dem Rendern, gegen die neue Messung.
Das ist der Normalfall und kein Zeichen eines Fehlers.

## Beim Vergleichen von Versionen

```
$ podmetrics batch renders/ --reference take_002.wav --csv verlauf.csv
```

Untereinander stehende Zeilen sind der Zweck. Der Vergleich soll eine Subtraktion sein und
keine Erinnerung.

## Was Du am Anfang messen solltest

Zwei Messungen lohnen sich, bevor Du überhaupt eine Folge aufnimmst:

**Der Raum ohne Dich.** Nimm 30 Sekunden Stille auf, mit laufender Kette und normalem Gain,
und miss sie als Rauschbereich:

```
$ podmetrics measure raum.wav --noise 0:30
```

Der Wert ist die Untergrenze, die Du je erreichen kannst. Liegt er über −60 dBFS, ist das
ein Ketten- oder Raumproblem, das keine Mikrofonposition löst.

**Dieselbe Passage aus drei Abständen.** Zehn, zwanzig, dreißig Zentimeter, sonst nichts
verändert. Vergleiche die Terzbandkurven. Danach weißt Du, wie der Nahbesprechungseffekt
Deines MV7 bei Deiner Stimme aussieht — und liest jede spätere Empfehlung mit anderen
Augen.
