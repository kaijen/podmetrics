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

!!! info "Warum im Cheat-Sheet trotzdem −16 steht"

    Der REAPER-Render normalisiert den **Master**, und der ist stereo. Dort ist −16 LUFS
    richtig. podmetrics misst danach eine **Spur**, und die zeigt für dieselbe Folge rund
    −19. Beide Zahlen sind korrekt und meinen denselben Höreindruck; sie beziehen sich nur
    auf verschiedene Signale. Die Messreihe bestätigt das: Version 020 wurde als Spur mit
    −19,85 LUFS gemessen und als fertig befunden.

!!! warning "Grenze der Messung"

    Bei echtem Stereo — gepannte Sprecher, Musikbett nur auf einer Seite — bildet ein
    einzelner Kanal die Lautheit der Folge nicht mehr ab. Dafür ist podmetrics das falsche
    Werkzeug; nimm den Lautheitsmesser in Ultraschall/REAPER für den Endcheck. podmetrics
    misst Deine Sprachspuren, nicht Deine Mischung.

## Zielwerte für die fertige Folge

Gemessen mit podmetrics, also einkanalig:

| Kennwert | Ziel | Herkunft |
| --- | ---: | --- |
| LUFS-I | −19 LUFS ±1 | Apple Podcasts, mono-Bezug; Messreihe v020: −19,85 |
| True Peak / Limiter beim Rendern | ≤ −1 dBTP | Spezifikation, Reserve gegen Intersample-Peaks |
| Peak der bearbeiteten Sprachspur | ca. −1,5 dBFS | Messreihe, Endstand |
| P10–P90 nach Kompression | 14–15,5 dB | Messreihe v020: 15,4 dB |
| Crest nach Kompression | 10–15 dB | Messreihe |
| Rauschteppich nach Kompression | **nicht über −48 dB** | Messreihe, siehe unten |
| Blockbalance | < 1 dB | Messreihe |

Die Zeile zum Rauschteppich ist die wichtigste und die am wenigsten offensichtliche.
Ein Kompressor unterscheidet nicht zwischen Sprache und allem anderen — er hebt Raum,
Rauschen und Atem mit an. Steigt der Rauschteppich über −48 dB, war der Eingriff zu
stark. Das ist ein objektives Kriterium und zuverlässiger als das Gehör, denn stärkere
Kompression klingt zunächst voller; der Preis fällt erst in den Pausen auf.

In der Messreihe ist genau das passiert: Version 012 landete bei −32,5 dB Rauschteppich
und war damit unbrauchbar, obwohl die Lautheit stimmte.

## Zielwerte für die Rohaufnahme

Das ist der Satz Werte, den Du täglich misst — pro Spur, pro Sprecher, direkt aus der
Aufnahme, ohne EQ und ohne Kompressor.

| Kennwert | Ziel | Herkunft |
| --- | ---: | --- |
| Sample-Peak der Sprache | −12 bis −6 dBFS | Cheat-Sheet; Headroom ist knapper als Rauschreserve |
| True Peak | ≤ −3 dBTP | Abstand zur Wandlergrenze, überlebt Intersample-Spitzen |
| Clipping | 0 Samples | Messreihe v001: 48 Samples nach Mikrofonwechsel |
| LUFS-I | −24 bis −20 LUFS | Messreihe v010: −20,86 |
| P10–P90 | 15–19 dB | Messreihe v010: 18,5 dB |
| Crest | 12–18 dB | Messreihe v010: 18,7 dB |
| Rauschteppich | −55 dBFS oder besser | Messreihe: −57,5 dB in guten Takes |
| Rauschabstand (Median − Rauschteppich) | ≥ 35 dB | Messreihe: Median −21, Rauschen −57,5 → 36,5 dB |

!!! danger "Plosivspitzen sind kein Maßstab für den Gain"

    Bei P und B trifft ein Luftstoß die Membran. Die Messreihe zeigt, wohin diese Energie
    geht: bei der Spitze in Version 006 lagen **85,5 %** zwischen 60 und 120 Hz, während
    im Blockdurchschnitt nur 28,7 % unterhalb von 120 Hz liegen. Ein Hochpass bei 80 Hz
    senkte dieselbe Spitze von −0,16 auf −2,23 dBFS, ohne dass an der Stimme etwas fehlte.

    Wer den Gain so einstellt, dass auch diese Ausschläge Platz haben, nimmt die Sprache
    mehrere Dezibel zu leise auf. Maßgeblich ist der Sprechpegel, nicht der Einzelausschlag
    — deshalb misst podmetrics Plosive getrennt und rechnet sie aus der Peak-Bewertung
    heraus, statt sie als Übersteuerungswarnung auszugeben.

**Nimm nicht bei −19 LUFS auf.** Das ist der Wert der fertigen Folge, nicht der Aufnahme.
Wer roh so laut aufnimmt, hat bei einem Lacher keinen Headroom mehr und übersteuert. Die
Lautheit kommt am Ende durch die Pegelangleichung dazu, nicht am Anfang durch den
Vorverstärker.

## Woher diese Werte kommen

Die Zahlen auf dieser Seite sind keine Schätzungen. Sie stammen aus einer Messreihe von
rund zwanzig Versionen desselben Materials, aufgenommen mit Shure MV7 am PodTrak P4next
und bearbeitet in Ultraschall. Das Protokoll liegt im Repository unter
`previous_dialog/`, eine Zusammenfassung der belegten Punkte steht unter
[Messreihen](messreihen.md).

Wo eine Zahl aus einer Spezifikation kommt, steht das in der Spalte „Herkunft". Wo sie
aus der Messreihe kommt, steht die Version dabei. Beides ist besser als der frühere
Zustand dieser Seite, in der einige Zeilen Faustwerte ohne Beleg waren — zwei davon lagen
deutlich daneben und sind inzwischen korrigiert.

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
- Eigene Messreihe, `previous_dialog/DIALOG.md` und `previous_dialog/podcast-cheatsheet.md` im Repository
