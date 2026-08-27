# podmetrics

`podmetrics` ist eine Python-Bibliothek mit Kommandozeilenwerkzeug, die Sprachaufnahmen
misst. Sie nimmt Audio und gibt Zahlen zurück. Kein Web, keine Datenbank, kein
persistenter Zustand.

Auf Wunsch leitet sie aus diesen Zahlen Empfehlungen ab: zur Mikrofonposition, zu
EQ- und Kompressoreinstellungen in Ultraschall, und zur Frage, ob eine Aufnahme als
Referenz taugt.

!!! warning "Entwurf — noch keine Zeile Code"

    Dieses Repository enthält bisher nur Konzept und Schnittstellenentwurf. Alle hier
    beschriebenen Funktionen, Datentypen und Befehle sind Absicht, nicht Realität.
    Was schon steht und was noch nicht, sagt der [Projektstand](projektstand.md).

## Wofür

Podcast-Sprachaufnahmen, WAV 24 Bit, aus Shure MV7 / MV7X über einen Zoom PodTrak
P4next nach Ultraschall (REAPER). Die typische Frage ist nicht „wie klingt das", sondern
„ist Version 7 näher am Ziel als Version 2, und woran genau". Diese Frage soll eine
Subtraktion beantworten und keine Erinnerung.

## Zwei Konsumenten

Die CLI für den direkten Gebrauch am Terminal und eine Vue-Webapp in einem separaten
Repository. Beide sind gleichrangig. Weil die Bibliothek von außen benutzt wird, ist ihre
öffentliche API ein Vertrag und keine Sammlung von Implementierungsdetails.

## Der kürzeste Weg durch diese Dokumentation

| Wenn Du wissen willst … | dann lies |
| --- | --- |
| warum die Bibliothek so geschnitten ist | [Konzept](konzept.md) |
| welche LUFS-Werte Du anstreben sollst | [Zielwerte](zielwerte.md) |
| wie die API aussehen wird | [Funktionen](api/funktionen.md) |
| was gemessen wird und in welchem Feld es landet | [Datentypen](api/datentypen.md) |
| wie aus Messwerten Ratschläge werden | [Empfehlungen](api/empfehlungen.md) |
| wie sich das am Terminal anfühlt | [CLI](cli.md) |
| wie eine Aufnahmesitzung praktisch abläuft | [Arbeitsweise](arbeitsweise.md) |
| woher die Schwellen kommen und was sie belegt | [Messreihen](messreihen.md) |

## Zum Mitnehmen

Die vollständige Dokumentation gibt es auch als E-Book:
[podmetrics.epub](https://kaijen.github.io/podmetrics/podmetrics.epub). Es wird bei
jeder Veröffentlichung aus denselben Quellen neu gebaut und ist damit nie älter als
diese Seite.

## Beispiel

```python
from podmetrics import load, measure, compare, advise

m2 = measure(load("take_002.wav"), noise_region=(12.4, 42.4))
m7 = measure(load("take_007.wav"))

cmp = compare([m2, m7], reference=m2)
tipps = advise(m7, reference=m2, topics=("position", "eq"))
```

```
$ podmetrics batch renders/ --reference take_002.wav
$ podmetrics advise take_007.wav --reference take_002.wav --topic position
```
