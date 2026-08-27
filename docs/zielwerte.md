# Zielwerte

Diese Seite beantwortet zwei Fragen: Welchen Lautheitswert soll eine fertige Folge haben,
und welche Werte soll die Rohaufnahme treffen, damit dieser Wert überhaupt erreichbar ist.
Beides sind verschiedene Ziele, und sie zu verwechseln ist der häufigste Anfängerfehler.

## Warum „Plattform"

Apple Podcasts, Spotify, YouTube und jeder andere Anbieter regeln die Lautheit beim
Abspielen selbst nach. Sie messen die Folge, vergleichen sie mit ihrem eigenen Zielwert
und drehen den Wiedergabepegel entsprechend. Das ist der Grund, warum Zielwerte
plattformabhängig genannt werden — nicht, weil eine Datei technisch anders sein müsste,
sondern weil jeder Anbieter einen anderen Bezugspunkt gewählt hat.

Die praktische Folge ist wichtiger als die Zahlen: **Lauter zu produzieren bringt nichts.**
Wer über den Zielwert hinaus komprimiert und limitiert, wird beim Abspielen wieder
heruntergeregelt — und hat dann eine leise Aufnahme mit zerdrückter Dynamik. Der Wettlauf
um Lautheit ist auf normalisierenden Plattformen verloren, bevor er beginnt.

| Plattform | Bezugswert | True Peak |
| --- | ---: | ---: |
| Apple Podcasts | −16 LUFS (Stereo), −19 LUFS (Mono) | ≤ −1 dBTP |
| Spotify | −14 LUFS | ≤ −1 dBTP |
| YouTube | ≈ −14 LUFS | ≤ −1 dBTP |
| AES TD1004 (Sprache, Streaming) | Fenster −16 bis −20 LUFS | ≤ −1 dBTP |
| EBU R128 (Rundfunk) | −23 LUFS | ≤ −1 dBTP |

## Ergibt −16 LUFS Sinn?

Ja, mit einer Einschränkung, die für Dich gilt.

−16 LUFS ist der Wert von Apple Podcasts und liegt im Fenster, das die AES für
Sprachinhalte im Streaming empfiehlt. Die Begründung für das Fenster ist beidseitig: Über
−16 LUFS hinaus braucht man Limiting, das der Sprache hörbar schadet; unter −20 LUFS wird
die Folge auf einem Telefon in der U-Bahn zu leise. Für gesprochenes Wort ist −16 LUFS
damit eine gute, konservative Wahl.

Spotify normalisiert auf −14 LUFS. Eine Folge mit −16 LUFS wird dort um 2 dB angehoben
und klingt genauso laut wie alles andere. Das ist kein Problem und kein Grund, lauter zu
produzieren.

Die Einschränkung: **−16 LUFS gilt für Stereo.** Und das ist genau der Punkt, an dem
podmetrics anders misst, als Du vielleicht erwartest.

## Der 3-dB-Fehler

podmetrics reduziert jedes Material beim Laden auf **einen Kanal** — das ist eine bewusste
Entscheidung, damit die Summierung zweier Sprecherspuren keine Kammfilter ins Messergebnis
mischt. Jeder LUFS-Wert, den podmetrics ausgibt, ist deshalb ein **Mono-Wert**.

Die Lautheitsmessung nach ITU-R BS.1770 summiert die Kanalenergien. Dasselbe Signal auf
zwei Kanälen misst rund 3 dB lauter als auf einem. Deshalb nennt Apple zwei Zahlen für
denselben Höreindruck: −19 LUFS mono und −16 LUFS stereo.

!!! tip "Die Regel, die Du Dir merken musst"

    Wenn podmetrics **−19 LUFS** anzeigt, ist Deine Folge richtig — egal ob Du sie als
    Mono-Datei veröffentlichst oder als Stereo-Datei mit identischem linken und rechten
    Kanal. Ein Kanal einer solchen Datei misst −19; die Datei als Ganzes misst −16.

    Wer die podmetrics-Anzeige gegen −16 prüft, veröffentlicht 3 dB zu laut.

!!! warning "Grenze der Messung"

    Bei echtem Stereo — gepannte Sprecher, Musikbett nur auf einer Seite — bildet ein
    einzelner Kanal die Lautheit der Folge nicht mehr ab. Dafür ist podmetrics das falsche
    Werkzeug; nimm den Lautheitsmesser in Ultraschall/REAPER für den Endcheck. podmetrics
    misst Deine Sprachspuren, nicht Deine Mischung.

## Zielwerte für die fertige Folge

Gemessen mit podmetrics, also einkanalig:

| Kennwert | Ziel | Toleranz |
| --- | ---: | ---: |
| LUFS-I | −19 LUFS | ±1 dB |
| True Peak | ≤ −1 dBTP | — |
| P10–P90 (nach Kompression) | 6–9 dB | — |
| Crest (nach Kompression) | 9–12 dB | — |

Die ersten beiden Zeilen sind Spezifikation. Die letzten beiden sind Faustwerte: Sie
beschreiben, wie stark die Dynamik nach Kompression üblicherweise eingeengt ist, wenn das
Ergebnis noch natürlich klingt. Unter 6 dB Spanne wird es gleichförmig und anstrengend.

## Zielwerte für die Rohaufnahme

Das ist der Satz Werte, den Du täglich misst — pro Spur, pro Sprecher, direkt aus der
Aufnahme, ohne EQ und ohne Kompressor.

| Kennwert | Ziel | Warum |
| --- | ---: | --- |
| Sample-Peak | −12 bis −6 dBFS | Reserve für Plosive und Lacher; 24 Bit hat Rauschreserve im Überfluss, Headroom ist die knappere Ressource |
| True Peak | ≤ −3 dBTP | Abstand zur Wandlergrenze, der auch Intersample-Spitzen überlebt |
| LUFS-I | −24 bis −20 LUFS | folgt aus dem Peak-Ziel und einem typischen Sprech-Crest |
| Rauschabstand | ≥ 50 dB unter dem Median-Sprechpegel | darunter hört man den Raum in den Pausen |
| Rauschteppich absolut | ≤ −60 dBFS | Kontrolle für die Kette, nicht für die Stimme |
| Crest | 12–18 dB | unter 12 dB ist etwas schon komprimiert, über 18 dB schwankt der Abstand |
| P10–P90 | ≤ 12 dB | Maß für gleichmäßige Mikrofontechnik |

!!! note "Herkunft dieser Werte"

    Die Zeilen zu Peak, True Peak und LUFS-I sind aus dem Zielwert der fertigen Folge
    zurückgerechnet und in der Praxis unstrittig. Die Zeilen zu Crest, P10–P90 und
    Rauschabstand sind **Faustwerte**, keine Norm. Sie stehen hier, damit überhaupt ein
    Bezugspunkt existiert. Sobald Du zwanzig eigene Messungen hast, ersetze sie durch das,
    was Deine gute Aufnahme tatsächlich zeigt — das ist der bessere Maßstab.

**Nimm nicht bei −19 LUFS auf.** Das ist der Wert der fertigen Folge, nicht der Aufnahme.
Wer roh so laut aufnimmt, hat bei einem Lacher keinen Headroom mehr und übersteuert. Die
Lautheit kommt am Ende durch die Pegelangleichung dazu, nicht am Anfang durch den
Vorverstärker.

## Zwei Profile

Diese beiden Wertesätze werden im Code zu zwei `TargetProfile`-Vorgaben:

```python
from podmetrics import TargetProfile, advise

TargetProfile.raw()       # Rohaufnahme, pro Spur
TargetProfile.delivery()  # fertige Folge, einkanalig gemessen

advise(m, reference=ref, profile=TargetProfile.raw())
```

`advise()` ohne `profile` nimmt `TargetProfile.raw()`, weil der tägliche Fall die
Rohaufnahme ist. Jeder Defaultwert steht im Quelltext mit einer Zeile Begründung: Ein
Zielwert ohne Herkunft wird nach drei Monaten nicht mehr hinterfragt, sondern geglaubt.

## Quellen

- [AES TD1004.1.15-10 — Recommendation for Loudness of Audio Streaming and Network File Playback](https://aes2.org/wp-content/uploads/2024/01/AESTD1004_1_15_10.pdf)
- [Production Advice: Streaming Loudness — AES Recommendations](https://productionadvice.co.uk/td1008/)
- [Critical Listening Lab: Podcast Loudness Standards — LUFS für Apple Podcasts & Spotify](https://www.criticallisteninglab.com/en/learn/loudness/podcast)
