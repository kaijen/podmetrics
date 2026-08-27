# Projektstand

Version 0.1.0, Stand August 2026.

## Was existiert

Die Bibliothek ist implementiert und getestet. Alle Namen, die unter
[Funktionen](api/funktionen.md) und [Datentypen](api/datentypen.md) stehen, gibt es
wirklich.

| Baustein | Stand |
| --- | --- |
| `models` | vollständig, alle Modelle mit `to_dict()` / `from_dict()` |
| `io` | laden, Kanalwahl, Resampling, Prüfsumme der Quelle |
| `gating` | gleitendes RMS, Sprachsegmente, Sprachanteil |
| `levels` | Peak, True Peak, Crest, Perzentile, Clipping, Plosiverkennung |
| `loudness` | LUFS-I, Short-Term-Verlauf, Blockbalance, `gain_for_target_lufs()` |
| `spectrum` | Welch-PSD, Terzbänder, Kammfilternachweis |
| `compare` | Deltas, Differenzkurven, Drift |
| `advice` | 16 Regeln über drei Themen, Referenzprüfung |
| `report` | `measure()` als Zusammenbau |
| `cli` | `measure`, `batch`, `compare`, `advise`, `check-reference` |

## Installation

Ein Release auf PyPI gibt es noch nicht. Aus dem Quelltext:

```
uv tool install "git+https://github.com/kaijen/podmetrics#egg=podmetrics[cli]"
```

Als Bibliothek, ohne Terminal-Ballast:

```
uv pip install "git+https://github.com/kaijen/podmetrics"
```

## Entwicklung

```
uv venv && . .venv/bin/activate
uv pip install -e ".[cli]" pytest ruff mypy

pytest              # Tests
ruff check .        # Linter
ruff format .       # Formatierung
mypy                # Typprüfung, strict
```

Jeder Push und jeder Pull Request lässt alle vier gegen Python 3.11 bis 3.14 laufen. Ein
roter Lauf blockiert nichts automatisch, aber er ist gemeint.

Die Untergrenze 3.11 kommt nicht vom eigenen Code — der läuft nachweislich auch unter
3.10 —, sondern von numpy und scipy: Deren aktuelle Fassungen verlangen 3.11. Unter 3.10
bekäme man ältere numpy- und scipy-Versionen untergeschoben und damit womöglich andere
Zahlen aus denselben Daten. Für eine Messbibliothek ist das der eigentliche Einwand.

## Tests

89 Tests, alle ohne echte Audiodateien.

Jede Rechenfunktion hat mindestens einen Test mit synthetischem Signal, dessen Ergebnis
analytisch bekannt ist: Ein Sinus mit Amplitude 0,5 muss −6,02 dBFS Peak und −9,03 dBFS
RMS ergeben, weißes Rauschen mit σ = 0,1 muss auf −20 dB kommen, halbe Amplitude muss
genau 6,02 dB weniger LUFS ergeben.

Dazu ein **Golden Test**: ein deterministisch erzeugtes Signal, dessen vollständiges
`Measurement` als JSON unter `tests/data/` liegt. Er schlägt fehl, sobald sich ein
Rechenweg unbeabsichtigt ändert — genau der Fall, der sonst erst Monate später als
unerklärliche Abweichung auffällt. Nach einer *beabsichtigten* Änderung wird er mit
`python tests/test_golden.py` neu erzeugt, und der neue Stand gehört in den Commit.

Die **Empfehlungsregeln** werden nicht aus Audio getestet, sondern aus von Hand
konstruierten `Measurement`-Objekten: je Regel eines knapp über der Schwelle, das sie
auslöst, und eines knapp darunter, das sie nicht auslöst. Das hält die Tests schnell und
macht die Schwellen im Test sichtbar, statt sie im Code zu verstecken.

Eigene Tests sichern die **Trennung von Messung und Meinung**: dass `Measurement` kein
Empfehlungsfeld trägt, dass `measure` und `batch` keine Empfehlungsoptionen haben, und
dass `advice` weder numpy noch scipy noch soundfile importiert. Diese Trennung geht sonst
als bequeme Kleinigkeit verloren.

## Was noch fehlt

| Frage | Stand |
| --- | --- |
| Nachhallschätzung | zurückgestellt; unsicher, ob robust genug machbar |
| Tragen die Schwellen für eine zweite Stimme? | offen — alle Zahlen stammen aus einer Stimme an einem Mikrofon |
| Kammfilternachweis an echtem Material | offen — belegt ist er bisher nur an synthetischen Signalen mit bekannter Verzögerung |
| Plosiverkennung an echtem Material | offen — dieselbe Einschränkung |
| Release auf PyPI | offen |
| `.RfxChain`-Export für Ultraschall | bewusst nicht — würde REAPER-Versionen ins Paket holen |

Die beiden mittleren Zeilen sind die wichtigsten. Beide Verfahren rechnen an
synthetischen Signalen richtig, an denen die Antwort vorher feststand. Ob sie an einer
echten Aufnahme dasselbe leisten — und ob sie normale laute Silben in Ruhe lassen —, ist
damit noch nicht gezeigt.

## Diese Dokumentation

Sie wird bei jedem Push auf `main` neu gebaut und nach GitHub Pages veröffentlicht. Der
Bau läuft mit `mkdocs build --strict`; ein toter Verweis bricht den Bau, statt still
online zu gehen.

Aus denselben Quellen entsteht dabei ein EPUB. Die Kapitelreihenfolge kommt aus der
Navigation in `mkdocs.yml` — es gibt keine zweite Kapitelliste, die auseinanderlaufen
könnte. Der EPUB-Bau prüft die Querverweise noch einmal für sich und bricht bei einem
toten Anker ab; in einer Datei, die schon beim Leser liegt, wiegt ein solcher Verweis
schwerer als auf einer Webseite.

Lokal:

```
pip install -r docs/requirements.txt
mkdocs serve

mkdocs build && python scripts/build_epub.py site/podmetrics.epub
```
