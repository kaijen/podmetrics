# Projektstand

Stand: August 2026.

## Was existiert

- Konzept, Abgrenzung und Schichtung — festgelegt
- Entwurf der öffentlichen API — festgelegt, aber noch nicht erprobt
- Zielwerte für Rohaufnahme und Veröffentlichung — aus einer eigenen Messreihe belegt
- Das Protokoll dieser Messreihe unter `previous_dialog/`, ausgewertet unter
  [Messreihen](messreihen.md)
- Diese Dokumentation

## Was nicht existiert

**Der Code.** Kein Modul, keine Funktion, kein Test. Jede Signatur auf diesen Seiten ist
eine Absicht.

## Reihenfolge des Bauens

Die Empfehlungsschicht ist von allen die einfachste — reine Wenn-Dann-Logik auf Zahlen.
Sie ist aber wertlos, solange die Kennwerte darunter nicht stimmen. Deshalb von unten nach
oben:

1. `models` — die Dataclasses, mit Roundtrip-Tests für `to_dict()` und `from_dict()`
2. `io` — laden, Kanalwahl, Resampling
3. `levels` und `gating` — Peak, True Peak, Crest, RMS-Perzentile, Sprachsegmente,
   Plosiverkennung
4. `loudness` — LUFS-I, Short-Term, `gain_for_target_lufs()`
5. `spectrum` — Welch-PSD, Terzbänder
6. `report.measure()` — der Zusammenbau
7. CLI `measure`, dann `batch` — ab hier ist das Werkzeug im Alltag benutzbar
8. `compare` und CLI `compare`
9. `advice` und CLI `advise`, `check-reference`

Schritt 7 ist der erste, an dem das Paket Nutzen stiftet. Alles davor ist Vorarbeit, alles
danach ist Komfort.

## Tests

Jede Rechenfunktion bekommt mindestens einen Test mit synthetischem Signal, dessen Ergebnis
analytisch bekannt ist: Sinus bekannter Amplitude, weißes Rauschen bekannter Leistung,
Stille, ein Sinus mit definierter Pause für das Gating.

Dazu ein **Golden Test**: ein deterministisch erzeugtes Signal, dessen vollständiges
`Measurement` als JSON im Repository liegt. Er schlägt fehl, sobald sich ein Rechenweg
unbeabsichtigt ändert — genau der Fall, der sonst erst Monate später als unerklärliche
Abweichung auffällt.

Empfehlungsregeln werden nicht aus Audio getestet, sondern aus von Hand konstruierten
`Measurement`-Objekten: je Regel eines knapp über der Schwelle, das sie auslöst, und eines
knapp darunter, das sie nicht auslöst. Das hält die Tests schnell und macht die Schwellen
im Test sichtbar, statt sie im Code zu verstecken.

Ein Test stellt sicher, dass `measure` und `batch` keine Empfehlungen ausgeben. Diese
Trennung geht sonst als bequeme Kleinigkeit verloren.

Für die Regeln, die aus der Messreihe stammen, ist der Test bereits geschrieben, bevor der
Code existiert: Die dort protokollierten Werte sind die Fixtures. Ein `Measurement` mit
Median −21 dBFS muss `comp.threshold` mit −24 vorschlagen; eine Terzband-Differenzkurve mit
−5,8 dB bei 4–8 kHz und −8,6 dB bei 8–12 kHz muss `position.off_axis` auslösen und nicht
`position.distance_excess`.

**Keine echten Audiodateien im Repository.** Die WAV-Dateien der Messreihe bleiben
außerhalb; was von ihnen gebraucht wird, sind die Messwerte, und die stehen im
Protokoll.

## Offene Entscheidungen

| Frage | Stand |
| --- | --- |
| Formel für Threshold und Ratio | **geschlossen.** Threshold = Median − 3 dB, Ratio 3:1 als Startwert, belegt durch die [Messreihe](messreihen.md#der-denkfehler-der-die-formel-festlegt) |
| Kennwert für Plosive | **geschlossen.** Tieftonanteil der Spitze gegen den Blockdurchschnitt |
| Kammfilter-Nachweis | **festgelegt**, noch nicht erprobt: Periodizität der Einbrüche in der Welch-PSD |
| Nachhallschätzung | zurückgestellt; unsicher, ob robust genug machbar |
| Tragen die Schwellen für eine zweite Stimme? | offen — alle Zahlen stammen aus einer Stimme an einem Mikrofon |
| `.RfxChain`-Export für Ultraschall | bewusst nicht — würde REAPER-Versionen ins Paket holen |

## Diese Dokumentation

Sie wird bei jedem Push auf `main` neu gebaut und nach GitHub Pages veröffentlicht. Der
Bau läuft mit `mkdocs build --strict`; ein toter Verweis bricht den Bau, statt still online
zu gehen.

Aus denselben Quellen entsteht dabei ein EPUB. Die Kapitelreihenfolge kommt aus der
Navigation in `mkdocs.yml` — es gibt keine zweite Kapitelliste, die auseinanderlaufen
könnte. Der EPUB-Bau prüft die Querverweise noch einmal für sich und bricht bei einem
toten Anker ab; in einer Datei, die schon beim Leser liegt, wiegt ein solcher Verweis
schwerer als auf einer Webseite.

Lokal:

```
python -m venv .venv && . .venv/bin/activate
pip install -r docs/requirements.txt
mkdocs serve

mkdocs build && python scripts/build_epub.py site/podmetrics.epub
```
