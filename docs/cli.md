# CLI

Der Terminalgebrauch ist gleichrangig mit dem Bibliotheksgebrauch, nicht ein Nebenprodukt.
Dafür darf nichts installiert, gestartet oder geöffnet werden müssen außer diesem Paket.

```
uv tool install podmetrics[cli]
```

Kein Docker, kein Server, kein Browser.

## Befehle

```
podmetrics measure FILE [--noise 12.4:42.4] [--region 11.8:15.0] [--channel 0] [--json]
podmetrics batch DIR --reference take_002.wav [--region 11.8:15.0] [--csv out.csv]
podmetrics compare FILE_A FILE_B --reference FILE_A
podmetrics advise FILE [--reference REF] [--topic position|eq|comp] [--noise 12.4:42.4] [--region 11.8:15.0] [--processed] [--delivery] [--json]
podmetrics check-reference FILE [--against FILE] [--noise 12.4:42.4] [--json]
```

`--region` schränkt die Auswertung auf einen Zeitabschnitt ein und ist für
Spektralvergleiche zweier Takes desselben Textes fast immer richtig. `--noise` markiert
dagegen die Sprechpause, in der der Rauschteppich gemessen wird — zwei verschiedene
Bereiche für zwei verschiedene Zwecke.

## batch

Der Hauptanwendungsfall: ein Ordner mit Renderversionen, eine Zeile pro Datei, Spalten für
Peak, True Peak, LUFS-I, Crest, P10–P90 und Rauschteppich. Untereinander stehende Zeilen
sind der Zweck — der Vergleich soll eine Subtraktion sein und keine Erinnerung.

```
$ podmetrics batch renders/ --reference take_002.wav

Datei              Peak    TruePeak    LUFS-I   Crest   P10–P90   Rauschen
take_002.wav      -8.1       -7.9     -22.4    14.3      11.2      -63.1
take_005.wav      -6.4       -6.0     -20.1    12.8       9.4      -61.7
take_007.wav      -9.7       -9.5     -24.8    15.1      13.9      -58.2
```

`batch` bleibt ohne Empfehlungen. Wer für zwanzig Dateien Ratschläge ausgibt, bekommt eine
Textwand statt einer Tabelle, und die Empfehlungen widersprechen einander, weil jede Datei
für sich betrachtet wird.

## advise

Der zweite Weg neben `batch`: nicht „welche Version ist näher dran", sondern „was soll ich
als Nächstes anders machen".

```
$ podmetrics advise take_007.wav --reference take_002.wav --topic position

Material: unbearbeitet (angenommen)   Referenz: take_002.wav   Profil: raw

1. Abstand vergrößern                                          [high]
   Grund:    Terzbänder 125–200 Hz liegen 5.8 dB über der Referenz
             (Schwelle 3.0 dB)
   Vorschlag: eine Handbreit weiter weg, Gain um 3 dB nachziehen
   Erwartung: Überschuss 125–200 Hz sinkt um etwa 4 dB
             LUFS-I bleibt gleich

   danach:
2. Winkel prüfen                                             [medium]
   ...

Nicht geprüft: comp.noise_headroom (keine --noise angegeben)
```

`--topic` ist mehrfach angebbar; ohne Angabe kommen alle drei Themen in fester Reihenfolge.

`--reference` nimmt eine Audiodatei **oder** eine gespeicherte Messung als `.json`. Der
zweite Weg ist der bequemere: Die Referenz wird nicht bei jedem Aufruf neu gerechnet, und
das Originalmaterial muss dafür nicht mehr vorliegen.

```
$ podmetrics measure take_002.wav --noise 12.4:42.4 --json > referenz.json
$ podmetrics advise take_009.wav --reference referenz.json
```

`--processed` erklärt das Material als bereits bearbeitet. Positionsempfehlungen entfallen
dann mit Begründung, statt still falsch zu sein.

`--delivery` rät gegen `TargetProfile.delivery()` statt gegen `raw()` — also gegen die
Zielwerte der fertigen Folge und nicht der Rohaufnahme. Ohne die Angabe gilt `raw()`, weil
der tägliche Fall die Rohaufnahme ist.

`check-reference` gibt Exit-Code 0 zurück, wenn die Messung als Maßstab taugt, und 1, wenn
nicht — damit lässt sich in einem Skript darauf verzweigen. Mit `--against` wird zusätzlich
geprüft, ob Referenz und Prüfling in Samplerate und Kanalwahl zusammenpassen und ob es
versehentlich dieselbe Datei ist.

## Ausgabe

Zahlen rechtsbündig und monospace, sonst sind die Spalten nicht lesbar.

`--json` gibt maschinenlesbar aus, ohne Tabellenrahmen und ohne Farbcodes, damit die
Ausgabe in `jq` und Skripte fließen kann.

Abweichungen von den Zielwerten werden farblich markiert, aber nur wenn die Ausgabe auf ein
Terminal geht. Bei Umleitung in eine Datei entfallen die Steuerzeichen.
