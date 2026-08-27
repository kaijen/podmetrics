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

| Beobachtung | Wahrscheinliche Ursache | Vorschlag |
| --- | --- | --- |
| Überschuss 100–250 Hz gegen Referenz | Nahbesprechungseffekt, zu geringer Abstand | Abstand vergrößern, eine Handbreit als Startwert |
| Abfall über 6 kHz bei unauffälligem Grundton | an der Achse vorbei gesprochen | Winkel prüfen, Mikrofon auf den Mund richten |
| Überschuss 5–8 kHz | Zischlaute | Mikrofon leicht aus der Achse drehen — erst danach ein De-Esser |
| Rauschabstand zu klein, Spektrum unauffällig | zu großer Abstand mit hochgedrehter Vorverstärkung | näher heran, Gain zurück |
| Große P10–P90-Spanne **und** driftender Short-Term-Verlauf | wechselnder Abstand | Haltung und Stativ, nicht der Kompressor |

Die letzte Zeile ist der Grund, warum der Verlauf im `Measurement` steht. Eine große Spanne
allein kann auch von lauten und leisen Sätzen kommen — das ist Sprechweise und kein
Aufbaufehler. Erst die Drift über Minuten macht daraus einen Abstandsbefund.

!!! note "Wozu nichts gesagt wird"

    Zu Popp-Geräuschen und Raumreflexionen wird nichts empfohlen, solange es dafür keine
    eigenen Kennwerte gibt — tieffrequente Transienten und eine Nachhallschätzung. Beides
    ist aus Terzbändern und Pegelstatistik nicht sicher von anderen Ursachen zu trennen.
    Eine geratene Ursache kostet mehr Zeit als keine Aussage.

## EQ

Grundlage ist die Terzband-Differenzkurve gegen die Referenz.

Vorgeschlagen werden höchstens drei breite Glocken und ein Hochpass. **Keine schmalen
Kerben:** Eine Terzband-Auflösung gibt schmalbandige Korrekturen nicht her, und was in
einer gemittelten Kurve als Spitze erscheint, ist oft ein einzelner Vokal.

Die Filter werden mit Abstand zueinander gewählt, weil sich überlappende Glocken in ihrer
Wirkung addieren und die gerechneten Gains dann nicht mehr stimmen.

Grenze ist `eq_max_gain_db` aus dem Profil, voreingestellt ±4 dB je Filter. Wo mehr nötig
wäre, ist die Ursache keine Frage des EQ, und die Ausgabe sagt das, statt größer zu
korrigieren.

Der Hochpass wird aus dem gemessenen Energieanteil unterhalb der Sprechgrundfrequenz
vorgeschlagen, nicht pauschal gesetzt. Eine tiefe Stimme verliert bei 100 Hz Fundament, das
nicht wiederkommt.

Ausgegeben werden Filtertyp, Frequenz, Gain und Q — direkt in ReaEQ eintragbar.

!!! danger "Die Referenz muss ein eigener Take sein"

    Eine Differenzkurve gegen eine fremde Stimme ist kein Korrekturziel. Wer danach
    filtert, egalisiert seine eigene Stimme weg und klingt am Ende wie eine schlechte Kopie
    des Vorbilds. Die Bibliothek kann das nicht prüfen; der Hinweis steht bei jeder
    EQ-Ausgabe.

## Kompression

Grundlage sind Median-Sprechpegel, P10–P90, Crest sowie Peak und True Peak.

**Threshold** folgt aus dem Median-Sprechpegel, **Ratio** aus dem Verhältnis der gemessenen
Spanne zur Zielspanne `comp_target_range_db` des Profils. Beides sind Rechnungen, und beide
nennen ihre Eingangswerte in der Ausgabe.

**Attack und Release** werden nicht gerechnet, sondern aus dem Profil übernommen. Sie
folgen aus Sprechtempo und Geschmack, nicht aus Kennwerten. Genau das steht dabei, damit
niemand sie für ein Messergebnis hält.

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
