#import "@preview/cetz:0.3.4": *

#set document(title: "Grundlagen der Sprachbearbeitung", author: "Kai")
#set text(font: "New Computer Modern", size: 11pt, lang: "de")
#set page(
  paper: "a4",
  margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 2.5cm),
  numbering: "1",
)
#set heading(numbering: "1.1")
#set par(justify: true, leading: 0.65em)
#show heading: set block(above: 1.4em, below: 0.8em)

// ── Kopf ──────────────────────────────────────────────────────────────────
#text(size: 20pt, weight: "bold")[Grundlagen der Sprachbearbeitung]
#v(0.2cm)
#line(length: 100%)
#v(0.3cm)
#grid(
  columns: (auto, 1fr),
  gutter: 0.5cm,
  [*Version:*], [1.0],
  [*Datum:*], [#datetime.today().display()],
  [*Kontext:*], [Shure MV7 an Zoom PodTrak P4next, Ultraschall/REAPER],
)
#v(0.8cm)

#outline(indent: auto, depth: 2)
#pagebreak()

= Überblick

Dieses Dokument erklärt die Konzepte hinter den Werkzeugen, die in Ultraschall
zur Verfügung stehen. Es ist von unten nach oben aufgebaut: Erst kommt die
Frage, wie Schall überhaupt zu Zahlen wird, dann wie man diese Zahlen misst,
dann was ein Mikrofon aus einer Stimme macht, und erst danach die
Bearbeitungswerkzeuge Equalizer und Kompressor.

Diese Reihenfolge ist nicht zufällig. Fast jeder Fehler in der
Sprachbearbeitung entsteht dadurch, dass eine Stufe repariert werden soll,
deren Problem eine Stufe tiefer sitzt. Ein Equalizer kann eine schlecht
positionierte Mikrofonachse nur kaschieren, nicht beheben. Ein Kompressor kann
abgeschnittene Signalspitzen nicht zurückholen. Wer weiß, welche Stufe wofür
zuständig ist, spart sich das Suchen an der falschen Stelle.

Ein Leitsatz zieht sich durch alle Kapitel: Ändere immer nur eine Größe, dann
miss oder höre. Wer zwei Regler gleichzeitig bewegt, weiß hinterher nicht,
welcher gewirkt hat.

= Vom Schall zur Datei

== Was eine Schallwelle ist

Sprache ist eine Folge von Luftdruckschwankungen. Deine Stimmlippen erzeugen
sie, die Luft trägt sie weiter, die Mikrofonmembran folgt ihnen. Zwei
Eigenschaften beschreiben eine solche Schwingung vollständig.

Die *Amplitude* ist die Größe des Ausschlags, also wie stark der Druck vom
Ruhewert abweicht. Sie entspricht dem, was wir als Lautstärke wahrnehmen.

Die *Frequenz* ist die Anzahl der Schwingungen pro Sekunde, gemessen in Hertz.
Sie entspricht der Tonhöhe. Der Grundton einer männlichen Sprechstimme liegt
meist zwischen 85 und 155 Hz, der einer weiblichen zwischen 165 und 255 Hz.
Über diesem Grundton liegen Obertöne und Konsonantengeräusche, die bis über
10.000 Hz reichen.

Sprache besteht immer aus vielen Frequenzen gleichzeitig. Genau das macht sie
für einen Equalizer zugänglich: Man kann einzelne Bereiche anheben oder
absenken, ohne die übrigen zu berühren.

== Wie daraus Zahlen werden

Der Wandler im PodTrak misst den Spannungsverlauf des Mikrofonsignals in
regelmäßigen Abständen und schreibt jeden Messwert als Zahl. Zwei Größen
bestimmen, wie genau das geschieht.

Die *Abtastrate* ist die Anzahl der Messungen pro Sekunde. Bei deinen Aufnahmen
sind es 48.000, geschrieben als 48 kHz. Eine Faustregel besagt, dass die höchste
darstellbare Frequenz bei der Hälfte der Abtastrate liegt, hier also bei
24.000 Hz. Das reicht für das gesamte menschliche Hörvermögen.

Die *Bittiefe* bestimmt, wie fein die einzelnen Messwerte abgestuft sind. Bei
24 Bit stehen rund 16,7 Millionen Stufen zur Verfügung. Je mehr Stufen, desto
größer der Abstand zwischen dem leisesten darstellbaren Signal und der
Aussteuerungsgrenze.

#figure(
  cetz.canvas({
    import cetz.draw: *
    line((-0.3, 0), (8.5, 0), stroke: 0.5pt + gray)
    let kurve = ()
    for i in range(0, 161) {
      let x = i / 20
      kurve.push((x, calc.sin(x * 1.1) * 1.4))
    }
    line(..kurve, stroke: 1pt + rgb("#2b6cb0"))
    for i in range(0, 18) {
      let x = i * 0.48
      let y = calc.sin(x * 1.1) * 1.4
      line((x, 0), (x, y), stroke: 0.4pt + gray)
      circle((x, y), radius: 0.07, fill: rgb("#c0392b"), stroke: none)
    }
    content((8.5, -0.45))[Zeit]
  }),
  caption: [Abtastung: Die durchgehende Kurve ist der Luftdruckverlauf, die
  Punkte sind die einzelnen Messwerte. Bei 48 kHz liegen 48.000 solcher Punkte
  in einer Sekunde.],
)

= Pegel messen

== Die Skala dBFS

Digitale Systeme haben eine harte Obergrenze: den größten Zahlenwert, den die
Bittiefe hergibt. Diese Grenze heißt *0 dBFS*, ausgesprochen null Dezibel Full
Scale. Alles, was darunter liegt, bekommt einen negativen Wert. Es gibt in
dieser Skala keine positiven Zahlen.

Dezibel ist ein logarithmisches Maß. Praktisch heißt das: Eine Differenz von
6 dB entspricht ungefähr einer Verdopplung oder Halbierung der Amplitude, eine
Differenz von 10 dB wird als etwa doppelt oder halb so laut empfunden. Weil das
Gehör selbst logarithmisch arbeitet, passt diese Skala gut zum Hören.

Der Abstand vom aktuellen Signal bis zur Grenze heißt *Headroom* oder
Aussteuerungsreserve.

== Spitze, Durchschnitt und der Abstand dazwischen

Eine Aufnahme hat nicht einen Pegel, sondern viele gleichzeitig relevante.

Der *Spitzenpegel* ist der höchste Momentanwert im gesamten Signal. Er
entscheidet darüber, ob etwas anschlägt.

Der *Durchschnittspegel* beschreibt, wie laut es sich im Mittel anfühlt.

Der Abstand zwischen beiden heißt *Crest-Faktor*. Bei Sprache liegt er
typischerweise zwischen 12 und 18 dB. Ein hoher Wert bedeutet: einzelne sehr
laute Momente über einem deutlich leiseren Mittel. Die praktische Folge ist
unangenehm — man kann den Durchschnitt nicht anheben, ohne dass die Spitzen
anschlagen. Genau dieses Problem löst der Kompressor.

Der *Rauschteppich* ist der Pegel in den Sprechpausen. Er kommt vom
Vorverstärker, vom Raum und von der Mikrofonkapsel. Je größer der Abstand
zwischen Rauschteppich und Sprache, desto sauberer klingt die Aufnahme.

== LUFS: Lautheit statt Pegel

Zwei Signale mit identischem Spitzenpegel können unterschiedlich laut klingen,
weil das Gehör mittlere Frequenzen stärker gewichtet als sehr tiefe und sehr
hohe. Ein reiner Pegelwert bildet das nicht ab.

*LUFS* misst deshalb die empfundene Lautheit. Die Skala ist wie dBFS negativ,
die Gewichtung entspricht aber dem Hörempfinden. Das Kürzel *LUFS-I* steht für
den über die gesamte Dauer gemittelten Wert.

Für Podcasts hat sich ein Zielwert von rund #sym.minus 16 LUFS eingebürgert.
Er sorgt dafür, dass Folgen verschiedener Produzenten ähnlich laut wirken.

#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    table.header([*Größe*], [*Was sie misst*], [*Zielwert*]),
    [Spitzenpegel Aufnahme], [Höchster Momentanwert], [#sym.minus 12 bis #sym.minus 6 dBFS],
    [Spitzenpegel bearbeitet], [Nach EQ und Kompressor], [ca. #sym.minus 1,5 dBFS],
    [Crest-Faktor], [Abstand Spitze zu Mittel], [10 bis 15 dB],
    [Rauschteppich], [Pegel in den Pausen], [unter #sym.minus 48 dB],
    [Endlautheit], [Empfundene Lautheit der Datei], [#sym.minus 16 LUFS],
  ),
  caption: [Kennwerte und ihre Zielbereiche.],
)

= Aussteuerung

== Warum zu laut schlimmer ist als zu leise

Überschreitet das Signal 0 dBFS, kann das System den Wert nicht darstellen. Die
Spitze wird abgeschnitten, aus der runden Wellenform wird eine flache Kante.
Das heißt *Clipping* und erzeugt hörbare Verzerrung. Es ist nicht reparabel,
weil die Information nicht mehr vorhanden ist.

Eine zu leise Aufnahme dagegen lässt sich später beliebig anheben. Man holt
sich dabei etwas mehr Rauschen mit, aber bei 24 Bit ist der Spielraum groß.

Daraus folgt die wichtigste Regel der Aufnahmetechnik: Zu leise aufnehmen ist
ein kleiner Fehler, zu laut aufnehmen ein großer.

#figure(
  cetz.canvas({
    import cetz.draw: *
    // linke Darstellung: sauber
    let a = ()
    for i in range(0, 121) {
      let x = i / 20
      a.push((x, calc.sin(x * 2.2) * 1.0))
    }
    line((-0.2, 1.35), (6.2, 1.35), stroke: (dash: "dashed", paint: gray, thickness: 0.5pt))
    line((-0.2, -1.35), (6.2, -1.35), stroke: (dash: "dashed", paint: gray, thickness: 0.5pt))
    line((-0.2, 0), (6.2, 0), stroke: 0.4pt + gray)
    line(..a, stroke: 1pt + rgb("#2b6cb0"))
    content((3, -2.1))[korrekt ausgesteuert]
    content((7.2, 1.35))[0 dBFS]

    // rechte Darstellung: geclippt
    let b = ()
    for i in range(0, 121) {
      let x = i / 20
      let v = calc.sin(x * 2.2) * 1.9
      b.push((x + 9, calc.max(calc.min(v, 1.35), -1.35)))
    }
    line((8.8, 1.35), (15.2, 1.35), stroke: (dash: "dashed", paint: gray, thickness: 0.5pt))
    line((8.8, -1.35), (15.2, -1.35), stroke: (dash: "dashed", paint: gray, thickness: 0.5pt))
    line((8.8, 0), (15.2, 0), stroke: 0.4pt + gray)
    line(..b, stroke: 1pt + rgb("#c0392b"))
    content((12, -2.1))[geclippt]
  }),
  caption: [Links bleibt die Wellenform unterhalb der Grenze. Rechts wurde zu
  hoch ausgesteuert; die Spitzen sind zu waagerechten Kanten geworden.],
)

== Plosive sind kein Maßstab

Bei den Lauten P und B verlässt ein Luftstoß den Mund und trifft die Membran.
Das erzeugt einen sehr hohen Ausschlag, dessen Energie fast vollständig
unterhalb von 120 Hz liegt. Zur Verständlichkeit trägt er nichts bei, und ein
Hochpassfilter entfernt ihn später ohnehin.

Wer den Gain so einstellt, dass auch diese Ausschläge Platz haben, nimmt die
eigentliche Sprache mehrere Dezibel zu leise auf. Maßstab ist der Pegel der
normalen Sprache, nicht der einzelne Ausschlag.

= Das Mikrofon

== Richtcharakteristik

Ein Mikrofon nimmt nicht aus allen Richtungen gleich auf. Die
*Nierencharakteristik* des MV7 nimmt von vorn voll auf, von der Seite
gedämpft und von hinten am schwächsten. Die Form dieser Empfindlichkeitsverteilung
ähnelt einer Niere, daher der Name.

Wichtig ist dabei ein Effekt, der oft übersehen wird: Die Dämpfung außerhalb der
Achse ist frequenzabhängig. Tiefe Frequenzen werden aus allen Richtungen
ähnlich gut aufgenommen, hohe fast nur von vorn. Ein Mikrofon, dessen Achse am
Mund vorbeizeigt, liefert deshalb nicht einfach ein leiseres Signal, sondern ein
bassbetontes und höhenarmes.

#figure(
  cetz.canvas({
    import cetz.draw: *
    let pts = ()
    for i in range(0, 73) {
      let a = i * 5deg
      let r = 2.2 * 0.5 * (1 + calc.cos(a))
      pts.push((r * calc.cos(a), r * calc.sin(a)))
    }
    line(..pts, close: true, stroke: 1pt + rgb("#2b6cb0"))
    circle((0, 0), radius: 0.12, fill: black, stroke: none)
    line((0, 0), (2.9, 0), stroke: (dash: "dashed", paint: gray, thickness: 0.5pt))
    content((3.6, 0))[Achse]
    content((0, -0.5))[Kapsel]
    content((1.3, 1.6))[voll]
    content((-1.5, 1.0))[gedämpft]
    content((-1.9, -0.9))[stark gedämpft]
  }),
  caption: [Nierencharakteristik. Die Achse muss auf den Mund zeigen; die
  Rückseite gehört zur Störquelle oder zur zweiten sprechenden Person.],
)

== Abstand

Der Abstand bestimmt drei Dinge gleichzeitig.

Erstens den Pegel: Eine Verdopplung des Abstands kostet etwa 6 dB.

Zweitens das Verhältnis von Direkt- zu Diffusschall. Direktschall kommt auf
kürzestem Weg von deinem Mund, Diffusschall über Wände und Möbel. Je näher das
Mikrofon, desto stärker überwiegt der Direktschall und desto weniger hört man
den Raum. Deshalb ist Nähe wirksamer gegen Halligkeit als jede
Raumbedämpfung.

Drittens den *Nahbesprechungseffekt*: Gerichtete Mikrofone heben tiefe
Frequenzen an, wenn man nah heranrückt. Das gibt Fülle, kann aber wummern.

Für Sprache sind 5 bis 10 cm der übliche Bereich. Entscheidend ist, den Abstand
konstant zu halten — schwankender Abstand erzeugt schwankenden Pegel und
schwankende Klangfarbe zugleich.

== Kammfilter

Trifft ein Signal auf eine leicht verzögerte Kopie seiner selbst, addieren sich
beide. Bei manchen Frequenzen liegen die Wellenberge übereinander und verstärken
sich, bei anderen trifft Berg auf Tal und sie löschen sich aus. Über das
Spektrum ergibt das ein regelmäßiges Muster aus Überhöhungen und Einbrüchen, das
wie ein Kamm aussieht.

Hörbar ist das als hohler Klang, meist beschrieben als "wie durch ein Rohr".
Typische Ursachen sind das Monitorsignal aus einem Kopfhörer, das ins Mikrofon
zurückläuft, die Reflexion an einer harten Tischplatte, oder ein zweites
Mikrofon im selben Raum.

Die Tiefe der Einbrüche hängt davon ab, wie laut die verzögerte Kopie gegenüber
dem Original ankommt. Bei 6 dB Abstand schwankt das Spektrum um rund 9 dB, bei
20 dB Abstand um weniger als 2 dB. Daraus leitet sich die *3:1-Regel* ab: Der
Abstand zwischen zwei Mikrofonen soll mindestens dreimal so groß sein wie der
jeweilige Sprechabstand.

#figure(
  cetz.canvas({
    import cetz.draw: *
    let tau = 0.001
    let pts = ()
    for i in range(0, 241) {
      let f = i * 20
      let v = calc.abs(2 * calc.cos(calc.pi * f * tau))
      let d = if v < 0.05 { -18 } else { calc.max(20 * calc.log(v), -18) }
      pts.push((f / 400, d / 5 + 1.6))
    }
    line((-0.2, 0), (12.4, 0), stroke: 0.4pt + gray)
    line((-0.2, 1.6), (12.4, 1.6), stroke: (dash: "dashed", paint: gray, thickness: 0.5pt))
    line(..pts, stroke: 1pt + rgb("#c0392b"))
    content((13.4, 1.6))[unverändert]
    content((6, -0.55))[Frequenz]
    content((1.25, -0.55))[500]
    content((3.75, -0.55))[1500]
    content((8.75, -0.55))[3500]
  }),
  caption: [Kammfilter bei einer Verzögerung von einer Millisekunde. Die
  Einbrüche liegen bei 500, 1500, 2500 und 3500 Hz, also alle 1000 Hz.],
)

= Frequenzbearbeitung mit dem Equalizer

== Was ein Equalizer tut

Ein Equalizer hebt oder senkt einzelne Frequenzbereiche. Er kann nur verändern,
was vorhanden ist — wo ein Mikrofon nichts liefert, lässt sich auch nichts
anheben. Der Versuch verstärkt dann nur das Rauschen.

Jede Anhebung erhöht den Gesamtpegel. Wer im EQ vier Dezibel hinzufügt, muss den
Ausgang um denselben Betrag zurücknehmen, sonst schlägt das Signal später an.

== Die Bandtypen

#figure(
  cetz.canvas({
    import cetz.draw: *
    // Hochpass
    line((0, 0), (3.4, 0), stroke: 0.4pt + gray)
    line((0, 0.8), (0.5, 0.8), (0.9, 0.75), (1.2, 0.55), (1.4, 0.1), (1.5, -0.6),
      stroke: 1pt + rgb("#2b6cb0"))
    line((1.5, 0.8), (3.4, 0.8), stroke: 1pt + rgb("#2b6cb0"))
    content((1.7, -1.2))[Hochpass]

    // Glocke
    line((5, 0), (8.4, 0), stroke: 0.4pt + gray)
    line((5, 0.4), (5.9, 0.4), (6.3, 0.5), (6.7, 1.15), (7.1, 0.5), (7.5, 0.4), (8.4, 0.4),
      stroke: 1pt + rgb("#2b6cb0"))
    content((6.7, -1.2))[Glocke (Band)]

    // Shelf
    line((10, 0), (13.4, 0), stroke: 0.4pt + gray)
    line((10, 0.4), (11.2, 0.4), (11.8, 0.6), (12.4, 1.05), (13.4, 1.1),
      stroke: 1pt + rgb("#2b6cb0"))
    content((11.7, -1.2))[Shelf]
  }),
  caption: [Die drei Bandtypen. Der Hochpass entfernt alles unterhalb einer
  Grenze. Die Glocke wirkt gezielt um eine Mittenfrequenz herum, ihre Breite
  regelt der Parameter Bandbreite. Der Shelf hebt oder senkt alles oberhalb
  beziehungsweise unterhalb eines Punktes gemeinsam.],
)

Der *Hochpass* ist bei Sprache immer sinnvoll. Unterhalb von etwa 80 Hz liegt
bei einer Sprechstimme nichts Nützliches, wohl aber Trittschall, Rumpeln und
Plosivenergie. Diese wegzunehmen macht die Stimme nicht dünner, sondern schafft
Platz.

Die *Glocke* ist das Arbeitspferd für gezielte Korrekturen. Die *Bandbreite*
bestimmt, wie breit der Eingriff wirkt: kleine Werte für schmale Korrekturen,
große Werte für sanfte Formung.

Der *Shelf* eignet sich, wenn ein ganzer Randbereich zu schwach oder zu stark
ist, etwa um Luftigkeit oberhalb von 10 kHz hinzuzufügen.

== Was in welchem Bereich passiert

#figure(
  table(
    columns: (auto, auto, auto),
    align: (left, left, left),
    table.header([*Bereich*], [*Trägt bei*], [*Zu viel klingt*]),
    [unter 80 Hz], [nichts Nützliches], [wummerig, rumpelnd],
    [80–200 Hz], [Fundament, Volumen], [dröhnend],
    [200–500 Hz], [Körper der Stimme], [kastig, muffig],
    [500–1500 Hz], [Kern, Substanz], [nasal, telefonig],
    [2–5 kHz], [Präsenz, Verständlichkeit], [hart, anstrengend],
    [5–10 kHz], [Zischlaute, Detail], [scharf, zischelnd],
    [über 10 kHz], [Luftigkeit], [rauschig],
  ),
  caption: [Orientierung für Sprache. Die Grenzen sind fließend und
  stimmabhängig.],
)

Eine Stimme, die als "flach" beschrieben wird, hat meist nur Mitten: Es fehlt
gleichzeitig unten das Fundament und oben die Präsenz. Die Abhilfe ist nicht,
alles anzuheben, sondern Kontrast zu erzeugen — Fundament anheben, untere Mitten
absenken, Präsenz anheben.

= Dynamikbearbeitung mit dem Kompressor

== Das Prinzip

Ein Kompressor senkt alles ab, was eine einstellbare Schwelle überschreitet, und
lässt alles darunter unberührt. Der Abstand zwischen laut und leise wird dadurch
kleiner. Anschließend hebt man das gesamte Signal wieder an — und weil die
Spitzen jetzt tiefer liegen, geht das weiter als vorher.

Das Ergebnis: Die leisen Stellen sind lauter geworden, die lauten sind gleich
geblieben. Bei Sprache heißt das konkret, dass abgesackte Satzenden wieder
stehen und Abstandsschwankungen weniger auffallen.

#figure(
  cetz.canvas({
    import cetz.draw: *
    // Achsen
    line((0, 0), (0, 5), stroke: 0.5pt + gray)
    line((0, 0), (5, 0), stroke: 0.5pt + gray)
    // 1:1-Linie
    line((0, 0), (4.8, 4.8), stroke: (dash: "dashed", paint: gray, thickness: 0.5pt))
    // Kennlinie mit Threshold bei 2.5
    line((0, 0), (2.5, 2.5), stroke: 1.2pt + rgb("#2b6cb0"))
    line((2.5, 2.5), (4.8, 3.27), stroke: 1.2pt + rgb("#2b6cb0"))
    // Threshold-Markierung
    line((2.5, 0), (2.5, 2.5), stroke: (dash: "dotted", paint: gray, thickness: 0.5pt))
    content((2.5, -0.45))[Threshold]
    content((5.6, 4.8))[ohne Kompressor]
    content((5.6, 3.27))[mit 3:1]
    content((-0.9, 2.5))[Ausgang]
    content((2.4, -1.1))[Eingang]
  }),
  caption: [Kennlinie eines Kompressors. Unterhalb der Schwelle bleibt alles
  unverändert. Oberhalb ergeben drei Dezibel Eingangszuwachs nur noch ein
  Dezibel am Ausgang.],
)

== Die Parameter

Der *Threshold* legt fest, ab welchem Pegel der Kompressor eingreift. Er ist ein
absoluter Wert und hängt damit vom Aufnahmepegel ab. Als Orientierung: Er sollte
einige Dezibel unterhalb des mittleren Sprachpegels liegen, sonst erwischt er nur
die Ausreißer und die normale Sprache bleibt unbearbeitet.

Die *Ratio* bestimmt, wie stark oberhalb der Schwelle abgesenkt wird. 3:1
bedeutet, dass drei Dezibel Überschreitung am Ausgang nur noch ein Dezibel
ergeben. Für Sprache ist dieser Wert unauffällig.

Der *Attack* ist die Verzögerung, bevor der Kompressor greift. Acht Millisekunden
lassen den Anschlag von Konsonanten durch; ohne diese Verzögerung klingen T und K
stumpf.

Der *Release* ist die Zeit, bis er wieder loslässt. Zu kurz erzeugt Pumpen, weil
er zwischen Silben ständig auf- und zumacht. Zu lang zieht leise Passagen mit
herunter.

Das *Knee* bestimmt, wie weich der Übergang an der Schwelle verläuft. Ein Wert
um drei Dezibel lässt den Eingriff allmählich einsetzen statt abrupt.

== Wie viel ist genug

Die Reduktionsanzeige des Kompressors sollte bei normaler Sprache vier bis sechs
Dezibel zeigen, bei den lautesten Stellen höchstens acht.

Die verlässlichere Kontrolle ist aber der Rauschteppich. Der Kompressor
unterscheidet nicht zwischen Sprache und allem anderen — er hebt Raum, Rauschen
und Atemgeräusche mit an. Steigt der Rauschteppich über etwa
#sym.minus 48 dB, ist der Eingriff zu stark. Das ist ein objektives Kriterium
und damit zuverlässiger als das Gefühl, denn stärkere Kompression klingt
zunächst voller und präsenter; der Preis fällt erst in den Pausen auf.

Der zweite Preis betrifft die Betonung. Wer einen Satz durch Lautstärke betont,
bekommt genau diese Betonung teilweise weggenommen. Bei Sprache ist deshalb
weniger Kompression fast immer besser als mehr.

= Die Reihenfolge der Kette

Effekte wirken nacheinander, und jeder sieht das Ergebnis des vorherigen. Die
Reihenfolge ist damit kein Detail, sondern Teil der Einstellung.

#figure(
  cetz.canvas({
    import cetz.draw: *
    let kasten(x, titel) = {
      rect((x, 0), (x + 3, 1.1), stroke: 0.7pt + rgb("#2b6cb0"), radius: 0.1)
      content((x + 1.5, 0.55))[#titel]
    }
    kasten(0, [Aufnahme])
    kasten(3.9, [Hochpass])
    kasten(7.8, [Equalizer])
    kasten(11.7, [Kompressor])
    line((3.05, 0.55), (3.85, 0.55), mark: (end: ">"), stroke: 0.7pt)
    line((6.95, 0.55), (7.75, 0.55), mark: (end: ">"), stroke: 0.7pt)
    line((10.85, 0.55), (11.65, 0.55), mark: (end: ">"), stroke: 0.7pt)
  }),
  caption: [Die Bearbeitungsreihenfolge auf der Sprachspur.],
)

Der Hochpass steht ganz vorn. Stünde der Kompressor davor, würde er auf
Plosivenergie reagieren, die anschließend ohnehin entfernt wird — er würde die
Stimme also genau an den Stellen absenken, an denen gar kein lautes Sprachsignal
vorliegt.

Der Kompressor steht hinter dem Equalizer, weil dieser den Pegel verändert. Ein
Threshold, der vor dem EQ eingestellt wurde, passt danach nicht mehr.

= Am Ende: Lautheit herstellen

Erst wenn die Bearbeitung steht, wird die Endlautheit gesetzt. Beim Rendern
übernimmt das die *Normalisierung*: Sie misst die Lautheit der fertigen Mischung
und verschiebt das gesamte Signal so, dass der Zielwert erreicht wird.

Weil dabei auch die Spitzen mitwandern, gehört ein *Limiter* dazu, der bei etwa
#sym.minus 1 dB begrenzt. Der Sicherheitsabstand zur Null ist nötig wegen der
*Intersample-Peaks*: Zwischen zwei Abtastwerten kann die rekonstruierte
Wellenform höher ausschlagen als beide Werte, und eine spätere MP3-Kodierung
macht diese Überschreitungen hörbar.

Wichtig ist die Reihenfolge auch hier. Ohne vorherige Kompression bringt die
Normalisierung wenig, weil die hohen Spitzen sofort an die Grenze stoßen und der
Rest leise bleibt. Erst der kleinere Crest-Faktor macht Lautheit möglich.

= Arbeitsweise

Vier Gewohnheiten ersparen den größten Teil aller Fehlersuche.

*Nur eine Größe ändern, dann messen oder hören.* Zwei gleichzeitig bewegte Regler
ergeben ein Ergebnis, das sich nicht mehr zuordnen lässt.

*Die Abhörlautstärke beim Beurteilen nicht verändern.* Lautstärkeverhältnisse
wirken bei jedem Abhörpegel anders.

*Vor jedem Vorher-Nachher-Vergleich die Lautstärke angleichen.* Die lautere
Version klingt fast immer besser, unabhängig davon, ob sie es ist. Wer das nicht
ausgleicht, wählt systematisch das Lautere statt des Besseren.

*Der Fehler sitzt meistens eine Stufe tiefer als vermutet.* Wer an einem
Equalizer stundenlang nichts erreicht, sollte die Mikrofonposition prüfen. Wer
mit einem Kompressor kämpft, sollte den Aufnahmepegel prüfen. Der Weg von unten
nach oben ist auch der Weg der Fehlersuche.

= Glossar

#table(
  columns: (auto, 1fr),
  align: (left, left),
  table.header([*Begriff*], [*Bedeutung*]),
  [Amplitude], [Größe des Ausschlags einer Schwingung, entspricht der Lautstärke],
  [Attack], [Verzögerung, bevor der Kompressor eingreift],
  [Bittiefe], [Anzahl der Abstufungen je Messwert, hier 24 Bit],
  [Clipping], [Abschneiden von Spitzen oberhalb von 0 dBFS, nicht reparabel],
  [Crest-Faktor], [Abstand zwischen Spitzen- und Durchschnittspegel],
  [dBFS], [Pegel bezogen auf die digitale Aussteuerungsgrenze, immer negativ],
  [Diffusschall], [Schall, der über Reflexionen ankommt, im Gegensatz zum Direktschall],
  [Ducking], [Absenken der Musik, sobald jemand spricht],
  [Headroom], [Abstand vom aktuellen Pegel bis zur Grenze],
  [Hochpass], [Filter, der alles unterhalb einer Grenzfrequenz entfernt],
  [Intersample-Peak], [Überschreitung zwischen zwei Abtastwerten],
  [Kammfilter], [Regelmäßige Auslöschungen durch ein verzögertes Doppelsignal],
  [Knee], [Weichheit des Übergangs an der Kompressorschwelle],
  [Kompression], [Absenkung oberhalb einer Schwelle, verkleinert den Crest-Faktor],
  [LUFS], [Maß für die empfundene Lautheit],
  [Nahbesprechungseffekt], [Bassanhebung gerichteter Mikrofone bei geringem Abstand],
  [Niere], [Richtcharakteristik mit Aufnahme von vorn und Dämpfung nach hinten],
  [Normalisierung], [Verschieben des Signals auf einen definierten Zielwert],
  [Plosiv], [Luftstoß bei P und B, Energie fast vollständig unter 120 Hz],
  [Ratio], [Verhältnis zwischen Eingangs- und Ausgangszuwachs oberhalb der Schwelle],
  [Rauschteppich], [Pegel in den Sprechpausen],
  [Release], [Zeit, bis der Kompressor wieder loslässt],
  [Shelf], [Filter, der einen ganzen Randbereich gemeinsam anhebt oder absenkt],
  [Threshold], [Schwelle, ab der der Kompressor eingreift],
  [3:1-Regel], [Mikrofonabstand mindestens dreimal so groß wie der Sprechabstand],
)
