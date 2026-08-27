# Empfehlungen

Empfehlungen sind der zweite Zweck dieser Bibliothek und vom ersten sauber getrennt.
Gemessen wird immer, geraten nur auf Anforderung. `measure` und `batch` bleiben frei von
Ratschlägen: Eine Tabelle, in der zwischen den Zahlen Meinungen stehen, ist als
Vergleichsmittel verdorben.

Drei Themen, einzeln anforderbar: `position` für die Mikrofonaufstellung, `eq` und `comp`
für ReaEQ und ReaComp in Ultraschall.

## Gemeinsame Regeln

### Jede Empfehlung nennt ihre erwartete Wirkung

Drei Dinge stehen in jeder Empfehlung: die Messwerte, die sie ausgelöst haben, mit Zahl und
Schwelle; die vorgeschlagene Änderung; die erwartete Wirkung, ausgedrückt als Messwert.

Der dritte Punkt ist der wichtigste. Er macht die nächste Messung zur Prüfung der
Empfehlung — tritt die erwartete Änderung nicht ein, war die Vermutung falsch, und das
fällt sofort auf statt nach fünf Takes. Ohne diesen Punkt ist Beratung nicht
falsifizierbar.

### Eine Änderung pro Runde

Wer Abstand und EQ gleichzeitig ändert, kann die Wirkung im nächsten Take keiner Ursache
mehr zuordnen und lernt nichts. Die Ausgabe ist nach Rangfolge sortiert und markiert, was
zuerst zu tun ist; alles Weitere ist ausdrücklich als „danach" gekennzeichnet.

### Feste Reihenfolge

**Position → EQ → Kompression → Pegelangleichung.**

Was der Abstand zum Mikrofon behebt, wird nicht per Filter repariert. Ein EQ-Vorschlag, der
eine offene Positionsempfehlung überdeckt, wird zurückgehalten und durch den Hinweis darauf
ersetzt.

### Ohne Bezug keine Empfehlung

Grundlage ist eine Referenzmessung, ein abweichendes `TargetProfile` oder beides. Aus einer
einzelnen Messung ohne Ziel folgt nichts: −18 LUFS sind weder gut noch schlecht, sondern
nur eine Zahl.

### Hypothesen, keine Diagnosen

Eine dunkle Stimme und ein zu geringer Abstand erzeugen ähnliche Terzbandbilder. Raumhall,
Popp-Geräusche und ein schräg stehendes Mikrofon sind aus den vorhandenen Kennwerten nicht
sicher auseinanderzuhalten. Wo zwei Ursachen gleich plausibel sind, werden beide genannt,
statt eine zu wählen.

Der Ton ist „probier das und miss nach", nicht „dein Mikro steht falsch".

### Stabile IDs

Jede Empfehlung trägt eine ID nach dem Muster `position.proximity_excess`,
`eq.presence_dip`, `comp.threshold`. Die IDs sind Teil des Vertrags wie die
Funktionsnamen: Die Webapp hängt Texte daran, und nur damit lässt sich über Wochen sehen,
ob dieselbe Empfehlung immer wiederkommt. IDs sind englisch, die ausgegebenen Texte
deutsch.

Eine ID wird nie wiederverwendet. Verschwindet eine Regel, bleibt ihre ID verbraucht.

### Schweregrad statt Ja/Nein

`low` heißt: fällt in der Messung auf, wahrscheinlich nicht hörbar. `high` heißt: das ist
der Grund, warum der Take anders klingt als die Referenz. Die Schwellen stehen im
`TargetProfile` und nicht im Code verstreut.

### Rohmaterial vorausgesetzt

Positionsempfehlungen setzen unbearbeitetes Material voraus — den Rohmitschnitt, nicht den
gerenderten Take mit EQ und Kompressor. Die Bibliothek kann Bearbeitung nicht erkennen; der
Zustand wird über `material=` übergeben, die Vorgabe ist `"raw"`, und die Annahme steht in
der Ausgabe. Wer eine bearbeitete Datei als roh ausgibt, bekommt Empfehlungen gegen seine
eigene Bearbeitung.

## Position

Grundlage sind Terzband-Differenzkurve, Short-Term-Verlauf, P10–P90 und Rauschabstand.

| ID | Beobachtung | Wahrscheinliche Ursache | Vorschlag |
| --- | --- | --- | --- |
| `position.proximity_excess` | Überschuss 100–250 Hz gegen Referenz | Nahbesprechungseffekt, zu geringer Abstand | Abstand vergrößern, eine Handbreit als Startwert |
| `position.off_axis` | Abfall 4–8 kHz, **stärkerer** Abfall 8–12 kHz | an der Achse vorbei gesprochen | Achse auf den Mund richten |
| `position.sibilance` | Überschuss 5–8 kHz | Zischlaute | Mikrofon seitlich versetzen, Kapsel auf den Mund zurückdrehen |
| `position.distance_excess` | Rauschabstand zu klein, Spektrum unauffällig | zu großer Abstand mit hochgedrehter Vorverstärkung | näher heran, Gain zurück |
| `position.drift` | Große P10–P90-Spanne **und** driftender Short-Term-Verlauf | wechselnder Abstand | Haltung und Stativ, nicht der Kompressor |
| `position.plosives` | Spitzen mit weit überdurchschnittlichem Tieftonanteil | Luftstoß trifft die Membran | seitlich versetzen und Hochpass bei 80 Hz |
| `position.comb_filter` | Periodische Einbrüche gleichen Frequenzabstands | verzögerte Kopie des Signals | Monitorweg schließen, Tischreflexion dämpfen, 3:1-Regel |

Zwei Zeilen verdienen eine Erklärung, weil sie aus der Messreihe stammen und nicht aus
einer Faustregel.

**Die Achse** wird an zwei Bändern erkannt, nicht an einem. Beim Sprechen an der Achse
vorbei gehen zweimal Höhen verloren: an der Richtcharakteristik der Niere und an der
eigenen Abstrahlung, denn auch der Mund strahlt oberhalb von 4 kHz gerichtet ab. Deshalb
fällt 8–12 kHz stärker ab als 4–8 kHz, und deshalb sind die gemessenen Werte groß — 6 bis
13 dB, nicht ein bis zwei. Ein gleichmäßiger Abfall über beide Bänder ist ein anderer
Befund und deutet eher auf Abstand oder einen Schaumstoff-Windschutz.

**Der Drift** ist der Grund, warum der Short-Term-Verlauf im `Measurement` steht. Eine
große Spanne allein kann auch von lauten und leisen Sätzen kommen — das ist Sprechweise
und kein Aufbaufehler. Erst die Drift über Minuten macht daraus einen Abstandsbefund.

!!! warning "Seitlicher Versatz heißt nicht, die Achse wegzudrehen"

    Gegen Plosive versetzt man die eigene Position seitlich — dreht die Kapsel dabei aber
    auf den Mund zurück. Beides zu tun kostet genau die Höhen, die `position.off_axis`
    anschließend anzeigt. Die Empfehlungstexte sagen das ausdrücklich, weil „auf die Nase
    zielen" eine verbreitete Empfehlung ist, die zusätzlich zum Versatz falsch wird.

!!! note "Wozu weiterhin nichts gesagt wird"

    Zu Raumreflexionen wird nichts empfohlen, solange es dafür keine Nachhallschätzung
    gibt. Aus Terzbändern und Pegelstatistik ist Hall nicht sicher von anderen Ursachen
    zu trennen, und eine geratene Ursache kostet mehr Zeit als keine Aussage.

    Popp-Geräusche standen früher in dieser Liste. Sie stehen jetzt in der Tabelle
    darüber, weil die Messreihe ein Kriterium geliefert hat — siehe
    [Messreihen](../messreihen.md#plosive).

## EQ

Grundlage ist die Terzband-Differenzkurve gegen die Referenz.

Vorgeschlagen werden höchstens vier breite Glocken und ein Hochpass. **Keine schmalen
Kerben:** Eine Terzband-Auflösung gibt schmalbandige Korrekturen nicht her, und was in
einer gemittelten Kurve als Spitze erscheint, ist oft ein einzelner Vokal.

Die Filter werden mit Abstand zueinander gewählt, weil sich überlappende Glocken in ihrer
Wirkung addieren und die gerechneten Gains dann nicht mehr stimmen.

Grenze ist `eq_max_gain_db` aus dem Profil, voreingestellt ±4 dB je Filter. Wo mehr nötig
wäre, ist die Ursache keine Frage des EQ, und die Ausgabe sagt das, statt größer zu
korrigieren.

Der Hochpass wird aus dem gemessenen Energieanteil unterhalb der Sprechgrundfrequenz
vorgeschlagen, nicht pauschal gesetzt. Eine tiefe Stimme verliert bei 100 Hz Fundament, das
nicht wiederkommt. Er steht als **erstes** Glied der Kette, noch vor den Glocken und vor
dem Kompressor — sonst reagiert der Kompressor auf Plosivenergie, die anschließend ohnehin
entfernt wird.

Ausgegeben werden Filtertyp, Frequenz, Gain und **Bandbreite in Oktaven** — so, wie ReaEQ
sie entgegennimmt. Nicht Q: Die Umrechnung wäre eine Fehlerquelle an einer Stelle, an der
der Nutzer Zahlen abtippt.

!!! danger "Jede Anhebung erhöht den Spitzenpegel"

    Ein EQ-Vorschlag ohne die zugehörige Korrektur des Ausgangspegels ist unvollständig,
    und die Bibliothek gibt ihn nicht ohne sie aus. In der Messreihe clippte Version 007
    an 54 Samples, weil der Ausgangs-Gain nach einer Anhebung nicht nachgezogen worden
    war. Jede `eq.*`-Suggestion nennt deshalb den erwarteten Peak-Zuwachs und den
    Ausgangspegel, der ihn ausgleicht.

!!! danger "Die Referenz muss ein eigener Take sein"

    Eine Differenzkurve gegen eine fremde Stimme ist kein Korrekturziel. Wer danach
    filtert, egalisiert seine eigene Stimme weg und klingt am Ende wie eine schlechte Kopie
    des Vorbilds. Die Bibliothek kann das nicht prüfen; der Hinweis steht bei jeder
    EQ-Ausgabe.

## Kompression

Grundlage sind Median-Sprechpegel, P10–P90, Crest sowie Peak und True Peak.

**Threshold** liegt rund 3 dB **unter** dem Median-Sprechpegel. Die Richtung ist der
eigentliche Inhalt der Regel. Ein Threshold oberhalb des Medians lässt den Kompressor nur
die obere Hälfte der Sprache sehen; in der Messreihe bewegte sich zwischen −16 und −20
deshalb fast nichts, obwohl die Kette in Ordnung war. Der Median lag bei −21, der
brauchbare Threshold bei −24.

Der Threshold ist außerdem der einzige Wert, der bei jeder neuen Aufnahme neu zu prüfen
ist: Er ist absolut und hängt vom Aufnahmepegel ab. Alle anderen Parameter bleiben stehen.

**Ratio** folgt aus dem Verhältnis der gemessenen Spanne zur Zielspanne
`comp_target_range_db` des Profils; 3:1 ist der belegte Startwert. Beides sind Rechnungen,
und beide nennen ihre Eingangswerte in der Ausgabe.

**Wet** ist Teil des Vorschlags, nicht Beiwerk. Die Messreihe erreichte ihr Ergebnis über
den Wet-Anteil, nicht über eine höhere Ratio — parallele Kompression hält die Betonung
erhalten, die eine hohe Ratio wegnimmt.

!!! tip "Der verlässlichste Kontrollwert ist der Rauschteppich"

    Ein Kompressor unterscheidet nicht zwischen Sprache und allem anderen; er hebt Raum,
    Rauschen und Atem mit an. `comp.noise_lift` vergleicht deshalb den Rauschteppich der
    bearbeiteten Fassung mit dem der Rohaufnahme und schlägt an, sobald er über −48 dB
    steigt. In der Messreihe war Version 012 an genau dieser Stelle unbrauchbar —
    Lautheit und Dynamikspanne stimmten, der Rauschteppich stand bei −32,5 dB.

    Das ist ein objektives Kriterium und zuverlässiger als das Gehör: Stärkere Kompression
    klingt zunächst voller, der Preis fällt erst in den Pausen auf.

**Attack und Release** werden nicht gerechnet, sondern aus dem Profil übernommen: 8 ms und
100–120 ms, aus der Messreihe. Sie folgen aus Sprechtempo und Geschmack, nicht aus
Kennwerten. Genau das steht dabei, damit niemand sie für ein Messergebnis hält.

**Der Makeup-Gain ist ein Startwert, kein Ergebnis.** Kompression ändert die Lautheit, also
stimmt der aus der unkomprimierten Messung gerechnete Wert nach dem Rendern nicht mehr. Die
Empfehlung sagt ausdrücklich, dass erneut zu messen und `gain_for_target_lufs()` auf das
Rendering anzuwenden ist. Die Schleife rendern → messen → nachziehen ist der Normalfall und
kein Zeichen eines Fehlers.

Vorgeschlagen wird nur, was Ultraschall ohne Zusatzinstallation mitbringt: ReaEQ, ReaComp
und der Ausgangspegel. Liegt der True Peak über der Profilgrenze, ist die Empfehlung, den
Ausgangspegel zu senken — nicht, ein weiteres Plugin in die Kette zu hängen.

## Referenz prüfen

Eine Referenz wird nicht verwaltet. Sie wird bei jedem Aufruf übergeben, als Audiodatei
oder als gespeicherte Messung im JSON-Format. Dass die Webapp Referenzen dauerhaft hält,
ist ihre Sache und bleibt es.

`check_reference()` prüft die technische Eignung. Die künstlerische Wahl bleibt beim
Nutzer. Siehe [check_reference](funktionen.md#check_reference).
