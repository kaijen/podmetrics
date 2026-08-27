"""Empfehlungen aus Measurement und Comparison.

Diese Schicht kennt ``models`` und sonst nichts — insbesondere kein
``Signal``, kein soundfile, kein scipy und kein numpy. Empfehlungen müssen aus
den veröffentlichten Zahlen ableitbar sein, notfalls von Hand auf Papier. Was
nur aus dem Signal folgt, ist ein fehlender Kennwert und gehört in ein
Rechenmodul.
"""

from __future__ import annotations

from .models import (
    Advice,
    Evidence,
    Expectation,
    Measurement,
    ReferenceCheck,
    Suggestion,
    TargetProfile,
)

TOPIC_ORDER = ("position", "eq", "comp")

# Bänder, an denen die Positionsregeln hängen. Die Achse braucht zwei: Beim
# Sprechen an der Achse vorbei gehen zweimal Höhen verloren, an der
# Richtcharakteristik der Niere und an der eigenen Abstrahlung. Deshalb fällt
# 8–12 kHz stärker ab als 4–8 kHz.
BAND_PROXIMITY = (100.0, 250.0)
BAND_PRESENCE = (4000.0, 8000.0)
BAND_AIR = (8000.0, 12000.0)
BAND_SIBILANCE = (5000.0, 8000.0)


def _band_mean(hz: list[float], values: list[float], low: float, high: float) -> float | None:
    picked = [v for f, v in zip(hz, values, strict=True) if low <= f <= high]
    if not picked:
        return None
    return sum(picked) / len(picked)


def _difference_curve(
    measurement: Measurement, reference: Measurement
) -> tuple[list[float], list[float]]:
    known = dict(zip(reference.third_octave_hz, reference.third_octave_db, strict=True))
    hz: list[float] = []
    diff: list[float] = []
    for f, v in zip(measurement.third_octave_hz, measurement.third_octave_db, strict=True):
        if f in known:
            hz.append(f)
            diff.append(v - known[f])
    return hz, diff


def _drift_db(measurement: Measurement) -> float:
    """Steigung des Short-Term-Verlaufs mal Dauer, in dB.

    Kleinste Quadrate von Hand — hier ist kein numpy erlaubt, und für eine
    Gerade durch ein paar Dutzend Punkte braucht es auch keins.
    """
    xs = measurement.short_term_times_s
    ys = measurement.short_term_lufs
    n = len(xs)
    if n < 4:
        return 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    denominator = sum((x - mean_x) ** 2 for x in xs)
    if denominator == 0.0:
        return 0.0
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True)) / denominator
    return abs(slope) * (xs[-1] - xs[0])


def _severity(value: float, threshold: float, profile: TargetProfile) -> str:
    magnitude = abs(value)
    if magnitude >= threshold * profile.band_strong_factor:
        return "high"
    if magnitude >= threshold * 1.4:
        return "medium"
    return "low"


def _position_rules(
    measurement: Measurement,
    reference: Measurement | None,
    profile: TargetProfile,
    skipped: list[str],
) -> list[Suggestion]:
    out: list[Suggestion] = []

    if measurement.comb_spacing_hz is not None:
        spacing = measurement.comb_spacing_hz
        depth = measurement.comb_depth_db or 0.0
        delay_ms = 1000.0 / spacing
        out.append(
            Suggestion(
                id="position.comb_filter",
                topic="position",
                severity="high",
                order=0,
                title="Kammfilter — verzögerte Kopie des Signals",
                detail=(
                    f"Das Spektrum zeigt Einbrüche alle {spacing:.0f} Hz, das entspricht "
                    f"einer Verzögerung von rund {delay_ms:.1f} ms. Hörbar ist das als "
                    "hohler Klang, meist beschrieben als „wie durch ein Rohr“. Typische "
                    "Wege: Monitorsignal aus dem Kopfhörer zurück ins Mikrofon, Reflexion "
                    "an der Tischplatte, ein zweites Mikrofon im selben Raum. Monitorweg "
                    "schließen, Tischreflexion dämpfen, 3:1-Regel einhalten — und erst "
                    "danach alles Weitere, denn dieser Fehler überdeckt jeden anderen "
                    "Befund."
                ),
                evidence=[
                    Evidence(field="comb_spacing_hz", value=spacing, threshold=0.0, unit="Hz"),
                    Evidence(
                        field="comb_depth_db",
                        value=depth,
                        threshold=measurement.params.comb_min_depth_db,
                        unit="dB",
                    ),
                ],
                expected=[
                    Expectation(
                        field="comb_spacing_hz", direction="verschwindet", amount=0.0, unit=""
                    )
                ],
            )
        )

    if measurement.plosives:
        worst = max(measurement.plosives, key=lambda p: p.low_energy_share)
        gap = measurement.peak_dbfs - measurement.peak_speech_dbfs
        out.append(
            Suggestion(
                id="position.plosives",
                topic="position",
                severity="medium" if gap >= 2.0 else "low",
                order=0,
                title=f"{len(measurement.plosives)} Plosivspitze(n) — seitlich versetzen",
                detail=(
                    "Bei P und B trifft ein Luftstoß die Membran. Setz Dich seitlich "
                    "versetzt vor das Mikrofon und dreh die Kapsel dabei auf den Mund "
                    "zurück — die Achse wegzudrehen kostet Höhen. Ein Hochpass bei "
                    f"{profile.eq_highpass_hz:.0f} Hz entfernt den Rest. Wichtig für den "
                    f"Gain: Der Spitzenpegel liegt bei {measurement.peak_dbfs:.2f} dBFS, "
                    f"der Sprachanteil aber nur bei {measurement.peak_speech_dbfs:.2f} dBFS. "
                    "Steuere gegen den zweiten Wert aus, sonst nimmst Du zu leise auf."
                ),
                evidence=[
                    Evidence(
                        field="plosives[0].low_energy_share",
                        value=worst.low_energy_share,
                        threshold=worst.block_share,
                        unit="Anteil",
                    ),
                    Evidence(
                        field="peak_dbfs - peak_speech_dbfs",
                        value=gap,
                        threshold=2.0,
                        unit="dB",
                    ),
                ],
                expected=[
                    Expectation(
                        field="plosives",
                        direction="sinkt",
                        amount=len(measurement.plosives),
                        unit="Anzahl",
                    )
                ],
            )
        )

    if reference is None:
        skipped.append(
            "position.proximity_excess, position.off_axis, position.sibilance: "
            "ohne Referenzmessung nicht prüfbar"
        )
    else:
        hz, diff = _difference_curve(measurement, reference)
        if not hz:
            skipped.append("Terzband-Differenzkurve: keine gemeinsamen Bänder")
        else:
            low = _band_mean(hz, diff, *BAND_PROXIMITY)
            presence = _band_mean(hz, diff, *BAND_PRESENCE)
            air = _band_mean(hz, diff, *BAND_AIR)
            sibilance = _band_mean(hz, diff, *BAND_SIBILANCE)

            if low is not None and low >= profile.band_low_threshold_db:
                out.append(
                    Suggestion(
                        id="position.proximity_excess",
                        topic="position",
                        severity=_severity(low, profile.band_low_threshold_db, profile),
                        order=0,
                        title="Zu geringer Abstand — Nahbesprechungseffekt",
                        detail=(
                            f"Die Bänder von {BAND_PROXIMITY[0]:.0f} bis "
                            f"{BAND_PROXIMITY[1]:.0f} Hz liegen {low:.1f} dB über der "
                            "Referenz. Gerichtete Mikrofone heben tiefe Frequenzen an, "
                            "wenn man nah herangeht. Vergrößere den Abstand, eine "
                            "Handbreit als Startwert, und nimm neu auf. Denk daran, den "
                            "Gain nachzuziehen: Doppelter Abstand kostet etwa 6 dB."
                        ),
                        evidence=[
                            Evidence(
                                field="third_octave_diff_db[100-250 Hz]",
                                value=low,
                                threshold=profile.band_low_threshold_db,
                                unit="dB",
                            )
                        ],
                        expected=[
                            Expectation(
                                field="third_octave_diff_db[100-250 Hz]",
                                direction="sinkt",
                                amount=round(low * 0.7, 1),
                                unit="dB",
                            )
                        ],
                    )
                )

            if (
                presence is not None
                and air is not None
                and presence <= -profile.band_high_threshold_db
                and air < presence
            ):
                out.append(
                    Suggestion(
                        id="position.off_axis",
                        topic="position",
                        severity=_severity(air, profile.band_high_threshold_db, profile),
                        order=0,
                        title="Achse zeigt am Mund vorbei",
                        detail=(
                            f"4–8 kHz liegen {presence:.1f} dB unter der Referenz, "
                            f"8–12 kHz sogar {air:.1f} dB. Dass der obere Bereich stärker "
                            "abfällt, ist die Signatur einer Niere, die außerhalb ihrer "
                            "Achse besprochen wird: Höhen gehen zweimal verloren, an der "
                            "Richtcharakteristik und an der eigenen Abstrahlung, denn auch "
                            "der Mund strahlt oberhalb von 4 kHz gerichtet ab. Richte die "
                            "Kapsel auf den Mund. Kontrolle: Handy vor die Lippen halten, "
                            "Foto Richtung Mikrofon — die Stirnfläche muss als Kreis "
                            "erscheinen, nicht als Ellipse."
                        ),
                        evidence=[
                            Evidence(
                                field="third_octave_diff_db[4-8 kHz]",
                                value=presence,
                                threshold=-profile.band_high_threshold_db,
                                unit="dB",
                            ),
                            Evidence(
                                field="third_octave_diff_db[8-12 kHz]",
                                value=air,
                                threshold=presence,
                                unit="dB",
                            ),
                        ],
                        expected=[
                            Expectation(
                                field="third_octave_diff_db[8-12 kHz]",
                                direction="steigt",
                                amount=round(abs(air) * 0.7, 1),
                                unit="dB",
                            )
                        ],
                    )
                )

            if sibilance is not None and sibilance >= profile.band_high_threshold_db:
                out.append(
                    Suggestion(
                        id="position.sibilance",
                        topic="position",
                        severity=_severity(sibilance, profile.band_high_threshold_db, profile),
                        order=0,
                        title="Zischlaute treten hervor",
                        detail=(
                            f"5–8 kHz liegen {sibilance:.1f} dB über der Referenz. Erste "
                            "Maßnahme ist, das Mikrofon leicht aus der Achse zu drehen; "
                            "ein De-Esser ist die zweite und nicht die erste."
                        ),
                        evidence=[
                            Evidence(
                                field="third_octave_diff_db[5-8 kHz]",
                                value=sibilance,
                                threshold=profile.band_high_threshold_db,
                                unit="dB",
                            )
                        ],
                        expected=[
                            Expectation(
                                field="third_octave_diff_db[5-8 kHz]",
                                direction="sinkt",
                                amount=round(sibilance * 0.6, 1),
                                unit="dB",
                            )
                        ],
                    )
                )

            snr = measurement.snr_db
            if (
                snr is not None
                and low is not None
                and snr < profile.snr_min_db
                and abs(low) < profile.band_low_threshold_db
            ):
                out.append(
                    Suggestion(
                        id="position.distance_excess",
                        topic="position",
                        severity="medium",
                        order=0,
                        title="Zu großer Abstand mit hochgedrehter Vorverstärkung",
                        detail=(
                            f"Der Rauschabstand beträgt {snr:.1f} dB, gefordert sind "
                            f"{profile.snr_min_db:.0f} dB — das Spektrum ist dabei "
                            "unauffällig. Geh näher heran und nimm den Gain zurück."
                        ),
                        evidence=[
                            Evidence(
                                field="snr_db",
                                value=snr,
                                threshold=profile.snr_min_db,
                                unit="dB",
                            )
                        ],
                        expected=[
                            Expectation(
                                field="snr_db",
                                direction="steigt",
                                amount=round(profile.snr_min_db - snr, 1),
                                unit="dB",
                            )
                        ],
                    )
                )

    span = measurement.p10_p90_db
    drift = _drift_db(measurement)
    if span > profile.p10_p90_range_db[1] and drift >= profile.drift_threshold_db:
        out.append(
            Suggestion(
                id="position.drift",
                topic="position",
                severity="high" if drift >= 2 * profile.drift_threshold_db else "medium",
                order=0,
                title="Wechselnder Abstand während der Aufnahme",
                detail=(
                    f"Die Spanne P10–P90 liegt bei {span:.1f} dB, und der "
                    f"Short-Term-Verlauf driftet über die Aufnahme um {drift:.1f} dB. "
                    "Eine große Spanne allein käme auch von lauten und leisen Sätzen; "
                    "erst die Drift macht daraus einen Abstandsbefund. Das ist eine Frage "
                    "von Haltung und Stativ und wird nicht durch einen Kompressor gelöst, "
                    "der die Schwankung nur leiser macht."
                ),
                evidence=[
                    Evidence(
                        field="p10_p90_db",
                        value=span,
                        threshold=profile.p10_p90_range_db[1],
                        unit="dB",
                    ),
                    Evidence(
                        field="short_term_lufs (Drift)",
                        value=drift,
                        threshold=profile.drift_threshold_db,
                        unit="dB",
                    ),
                ],
                expected=[
                    Expectation(
                        field="short_term_lufs (Drift)",
                        direction="sinkt",
                        amount=round(drift * 0.7, 1),
                        unit="dB",
                    )
                ],
            )
        )
    return out


def _eq_rules(
    measurement: Measurement,
    reference: Measurement | None,
    profile: TargetProfile,
    skipped: list[str],
) -> list[Suggestion]:
    out: list[Suggestion] = []

    low_energy = _band_mean(
        measurement.third_octave_hz, measurement.third_octave_db, 0.0, profile.eq_highpass_hz
    )
    if low_energy is not None and low_energy > 0.0:
        out.append(
            Suggestion(
                id="eq.highpass",
                topic="eq",
                severity="medium",
                order=0,
                title=f"Hochpass bei {profile.eq_highpass_hz:.0f} Hz",
                detail=(
                    f"Unterhalb von {profile.eq_highpass_hz:.0f} Hz liegt "
                    f"{low_energy:.1f} dB mehr Energie als im Bandmittel. Dort steht kein "
                    "Sprachsignal, sondern Trittschall, Körperschall und Plosivenergie. "
                    "Der Hochpass gehört als erstes Glied in die Kette, noch vor die "
                    "Glocken und vor den Kompressor — sonst reagiert der Kompressor auf "
                    "Energie, die anschließend ohnehin entfernt wird."
                ),
                evidence=[
                    Evidence(
                        field=f"third_octave_db[<{profile.eq_highpass_hz:.0f} Hz]",
                        value=low_energy,
                        threshold=0.0,
                        unit="dB",
                    )
                ],
                expected=[
                    Expectation(field="peak_dbfs", direction="sinkt", amount=1.0, unit="dB")
                ],
                parameters={"frequency_hz": profile.eq_highpass_hz, "type_highpass": 1.0},
            )
        )

    if reference is None:
        skipped.append("eq.bells: ohne Referenzmessung nicht prüfbar")
        return out

    hz, diff = _difference_curve(measurement, reference)
    if not hz:
        return out

    # Kandidaten sind die Bänder mit der größten Abweichung. Filter werden mit
    # Abstand zueinander gewählt, weil sich überlappende Glocken in ihrer
    # Wirkung addieren und die gerechneten Gains dann nicht mehr stimmen.
    candidates = sorted(
        ((f, d) for f, d in zip(hz, diff, strict=True) if f >= profile.eq_highpass_hz),
        key=lambda item: abs(item[1]),
        reverse=True,
    )
    chosen: list[tuple[float, float]] = []
    for frequency, deviation in candidates:
        if abs(deviation) < profile.band_high_threshold_db:
            break
        if any(0.5 <= frequency / other <= 2.0 for other, _ in chosen):
            continue
        chosen.append((frequency, deviation))
        if len(chosen) >= profile.eq_max_filters:
            break

    boost_total = 0.0
    for frequency, deviation in sorted(chosen):
        gain = max(-profile.eq_max_gain_db, min(profile.eq_max_gain_db, -deviation))
        capped = abs(deviation) > profile.eq_max_gain_db
        boost_total = max(boost_total, gain)
        out.append(
            Suggestion(
                id=f"eq.band_{int(frequency)}hz",
                topic="eq",
                severity=_severity(deviation, profile.band_high_threshold_db, profile),
                order=0,
                title=f"Glocke bei {frequency:.0f} Hz, {gain:+.1f} dB",
                detail=(
                    f"Bei {frequency:.0f} Hz weicht die Aufnahme um {deviation:+.1f} dB "
                    "von der Referenz ab. Trag in ReaEQ eine Glocke mit Bandbreite 1,2 "
                    "Oktaven ein."
                    + (
                        f" Die Abweichung übersteigt die Profilgrenze von "
                        f"{profile.eq_max_gain_db:.0f} dB; mehr zu korrigieren ist keine "
                        "Frage des EQ, sondern der Ursache."
                        if capped
                        else ""
                    )
                    + " Die Referenz muss ein eigener Take sein — eine Differenzkurve "
                    "gegen eine fremde Stimme ist kein Korrekturziel."
                ),
                evidence=[
                    Evidence(
                        field=f"third_octave_diff_db[{frequency:.0f} Hz]",
                        value=deviation,
                        threshold=profile.band_high_threshold_db,
                        unit="dB",
                    )
                ],
                expected=[
                    Expectation(
                        field=f"third_octave_diff_db[{frequency:.0f} Hz]",
                        direction="sinkt" if deviation > 0 else "steigt",
                        amount=abs(gain),
                        unit="dB",
                    )
                ],
                parameters={
                    "frequency_hz": round(frequency, 1),
                    "gain_db": round(gain, 1),
                    "bandwidth_octaves": 1.2,
                },
            )
        )

    if boost_total > 0.0:
        # Jede Anhebung erhöht den Spitzenpegel. In der Messreihe clippte
        # Version 007 an 54 Samples, weil der Ausgangs-Gain fehlte.
        out.append(
            Suggestion(
                id="eq.output_gain",
                topic="eq",
                severity="high",
                order=0,
                title=f"Ausgangspegel um {-boost_total:.1f} dB nachziehen",
                detail=(
                    f"Die größte Anhebung beträgt {boost_total:+.1f} dB und hebt den "
                    f"Spitzenpegel von {measurement.peak_dbfs:.2f} dBFS auf etwa "
                    f"{measurement.peak_dbfs + boost_total:.2f} dBFS. Senk den Ausgangs-Gain "
                    f"in ReaEQ um denselben Betrag. Ohne diesen Schritt clippt die Spur — "
                    "das ist kein Randfall, sondern die Regel bei jeder Anhebung."
                ),
                evidence=[
                    Evidence(
                        field="peak_dbfs",
                        value=measurement.peak_dbfs,
                        threshold=profile.peak_max_dbfs,
                        unit="dBFS",
                    )
                ],
                expected=[
                    Expectation(field="peak_dbfs", direction="bleibt", amount=0.0, unit="dB")
                ],
                parameters={"output_gain_db": round(-boost_total, 1)},
            )
        )
    return out


def _comp_rules(
    measurement: Measurement, profile: TargetProfile, material: str
) -> list[Suggestion]:
    out: list[Suggestion] = []
    median = measurement.speech_median_dbfs
    threshold = median - profile.comp_threshold_below_median_db
    span = measurement.p10_p90_db
    ratio = max(
        1.5, min(6.0, span / max(profile.comp_target_range_db, 1.0) * profile.comp_ratio)
    )

    out.append(
        Suggestion(
            id="comp.threshold",
            topic="comp",
            severity="high",
            order=0,
            title=f"ReaComp Threshold {threshold:.1f} dB",
            detail=(
                f"Der Median-Sprechpegel liegt bei {median:.1f} dBFS. Der Threshold gehört "
                f"{profile.comp_threshold_below_median_db:.0f} dB darunter, also auf "
                f"{threshold:.1f} dB. Die Richtung ist wichtiger als der Zahlenwert: Ein "
                "Threshold oberhalb des Medians lässt den Kompressor nur die obere Hälfte "
                "der Sprache sehen, und dann bewegt sich fast nichts. Der Threshold ist "
                "der einzige Wert, den Du bei jeder neuen Aufnahme neu prüfen musst — er "
                "ist absolut und hängt vom Aufnahmepegel ab."
            ),
            evidence=[
                Evidence(
                    field="speech_median_dbfs",
                    value=median,
                    threshold=threshold,
                    unit="dBFS",
                )
            ],
            expected=[
                Expectation(
                    field="p10_p90_db",
                    direction="sinkt",
                    amount=round(max(0.0, span - profile.comp_target_range_db), 1),
                    unit="dB",
                )
            ],
            parameters={"threshold_db": round(threshold, 1)},
        )
    )

    out.append(
        Suggestion(
            id="comp.ratio",
            topic="comp",
            severity="medium",
            order=0,
            title=f"ReaComp Ratio {ratio:.1f}:1, Attack {profile.comp_attack_ms:.0f} ms, "
            f"Release {profile.comp_release_ms:.0f} ms",
            detail=(
                f"Die gemessene Spanne beträgt {span:.1f} dB, die Zielspanne des Profils "
                f"{profile.comp_target_range_db:.1f} dB — daraus folgt eine Ratio von etwa "
                f"{ratio:.1f}:1. Geh über den Wet-Anteil ans Ziel und nicht über eine höhere "
                "Ratio: Parallele Kompression erhält die Betonung, die eine hohe Ratio "
                f"wegnimmt. Attack und Release werden nicht gerechnet, sondern aus dem "
                f"Profil übernommen ({profile.comp_attack_ms:.0f} ms und "
                f"{profile.comp_release_ms:.0f} ms) — sie folgen aus Sprechtempo und "
                "Geschmack, nicht aus Kennwerten. Knee "
                f"{profile.comp_knee_db:.0f} dB, Detector-Lowpass auf 20000 Hz."
            ),
            evidence=[
                Evidence(
                    field="p10_p90_db",
                    value=span,
                    threshold=profile.comp_target_range_db,
                    unit="dB",
                )
            ],
            expected=[
                Expectation(
                    field="p10_p90_db",
                    direction="sinkt",
                    amount=round(max(0.0, span - profile.comp_target_range_db), 1),
                    unit="dB",
                )
            ],
            parameters={
                "ratio": round(ratio, 1),
                "attack_ms": profile.comp_attack_ms,
                "release_ms": profile.comp_release_ms,
                "knee_db": profile.comp_knee_db,
            },
        )
    )

    if measurement.true_peak_dbtp > profile.true_peak_max_dbtp:
        out.append(
            Suggestion(
                id="comp.true_peak",
                topic="comp",
                severity="high",
                order=0,
                title="Ausgangspegel senken — True Peak über der Grenze",
                detail=(
                    f"Der True Peak liegt bei {measurement.true_peak_dbtp:.2f} dBTP, die "
                    f"Profilgrenze bei {profile.true_peak_max_dbtp:.1f} dBTP. Senk den "
                    "Ausgangspegel; häng kein weiteres Plugin in die Kette."
                ),
                evidence=[
                    Evidence(
                        field="true_peak_dbtp",
                        value=measurement.true_peak_dbtp,
                        threshold=profile.true_peak_max_dbtp,
                        unit="dBTP",
                    )
                ],
                expected=[
                    Expectation(
                        field="true_peak_dbtp",
                        direction="sinkt",
                        amount=round(
                            measurement.true_peak_dbtp - profile.true_peak_max_dbtp, 1
                        ),
                        unit="dB",
                    )
                ],
                parameters={
                    "output_gain_db": round(
                        profile.true_peak_max_dbtp - measurement.true_peak_dbtp, 1
                    )
                },
            )
        )

    noise = measurement.noise_floor_dbfs
    if (
        noise is not None
        and material == "processed"
        and noise > profile.noise_floor_compressed_max_dbfs
    ):
        out.append(
            Suggestion(
                id="comp.noise_lift",
                topic="comp",
                severity="high",
                order=0,
                title="Kompression zu stark — Rauschteppich hochgezogen",
                detail=(
                    f"Der Rauschteppich liegt bei {noise:.1f} dBFS, die Grenze bei "
                    f"{profile.noise_floor_compressed_max_dbfs:.0f} dB. Ein Kompressor "
                    "unterscheidet nicht zwischen Sprache und allem anderen; er hebt Raum, "
                    "Rauschen und Atem mit an. Das ist der zuverlässigste Kontrollwert für "
                    "zu starke Kompression — zuverlässiger als das Gehör, denn stärkere "
                    "Kompression klingt zunächst voller, und der Preis fällt erst in den "
                    "Pausen auf. Nimm den Threshold zurück."
                ),
                evidence=[
                    Evidence(
                        field="noise_floor_dbfs",
                        value=noise,
                        threshold=profile.noise_floor_compressed_max_dbfs,
                        unit="dBFS",
                    )
                ],
                expected=[
                    Expectation(
                        field="noise_floor_dbfs",
                        direction="sinkt",
                        amount=round(noise - profile.noise_floor_compressed_max_dbfs, 1),
                        unit="dB",
                    )
                ],
            )
        )

    out.append(
        Suggestion(
            id="comp.makeup",
            topic="comp",
            severity="low",
            order=0,
            title="Makeup-Gain ist ein Startwert, kein Ergebnis",
            detail=(
                f"Aus der unkomprimierten Messung ergäbe sich ein Gain von "
                f"{profile.lufs_i - measurement.lufs_i:+.1f} dB auf {profile.lufs_i:.0f} LUFS. "
                "Kompression ändert aber die Lautheit, also stimmt dieser Wert nach dem "
                "Rendern nicht mehr. Rendere, miss erneut und wende dann "
                "gain_for_target_lufs() auf das Rendering an. Die Schleife rendern → messen "
                "→ nachziehen ist der Normalfall und kein Zeichen eines Fehlers."
            ),
            evidence=[
                Evidence(
                    field="lufs_i",
                    value=measurement.lufs_i,
                    threshold=profile.lufs_i,
                    unit="LUFS",
                )
            ],
            expected=[
                Expectation(
                    field="lufs_i",
                    direction="steigt",
                    amount=round(profile.lufs_i - measurement.lufs_i, 1),
                    unit="dB",
                )
            ],
            parameters={"start_gain_db": round(profile.lufs_i - measurement.lufs_i, 1)},
        )
    )
    return out


def advise(
    measurement: Measurement,
    *,
    reference: Measurement | None = None,
    profile: TargetProfile | None = None,
    topics: tuple[str, ...] = TOPIC_ORDER,
    material: str = "raw",
) -> Advice:
    """Leitet Empfehlungen ab. Sieht keine Samples.

    Ohne ``reference`` und ohne abweichendes ``profile`` gibt es nichts zu
    raten: Aus einer einzelnen Messung ohne Ziel folgt nichts.
    """
    if material not in ("raw", "processed"):
        raise ValueError('material muss "raw" oder "processed" sein.')
    unknown = set(topics) - set(TOPIC_ORDER)
    if unknown:
        raise ValueError(f"Unbekannte Themen: {sorted(unknown)}")

    profile = profile or TargetProfile.raw()
    skipped: list[str] = []
    collected: list[Suggestion] = []

    if "position" in topics:
        if material == "processed":
            skipped.append(
                "position.*: Material ist als bearbeitet angegeben. "
                "Positionsempfehlungen setzen den Rohmitschnitt voraus, sonst raten sie "
                "gegen die eigene Bearbeitung."
            )
        else:
            collected += _position_rules(measurement, reference, profile, skipped)

    position_blocking = [s for s in collected if s.topic == "position" and s.severity == "high"]

    if "eq" in topics:
        if position_blocking:
            # Was der Abstand zum Mikrofon behebt, wird nicht per Filter repariert.
            collected.append(
                Suggestion(
                    id="eq.blocked_by_position",
                    topic="eq",
                    severity="low",
                    order=0,
                    title="EQ-Vorschläge zurückgehalten",
                    detail=(
                        "Es steht mindestens eine Positionsempfehlung mit Schweregrad "
                        "„high“ offen: "
                        + ", ".join(s.id for s in position_blocking)
                        + ". Ein EQ-Vorschlag würde sie überdecken, statt die Ursache zu "
                        "beheben. Position zuerst ändern, neu aufnehmen, dann erneut "
                        "fragen."
                    ),
                )
            )
            skipped.append("eq.bells: durch offene Positionsempfehlung zurückgehalten")
        else:
            collected += _eq_rules(measurement, reference, profile, skipped)

    if "comp" in topics:
        collected += _comp_rules(measurement, profile, material)

    severity_rank = {"high": 0, "medium": 1, "low": 2}
    collected.sort(key=lambda s: (TOPIC_ORDER.index(s.topic), severity_rank[s.severity], s.id))
    # Rangfolge vergeben: was zuerst zu tun ist, steht oben.
    ordered = [
        Suggestion(
            id=s.id,
            topic=s.topic,
            severity=s.severity,
            order=index + 1,
            title=s.title,
            detail=s.detail,
            evidence=s.evidence,
            expected=s.expected,
            parameters=s.parameters,
        )
        for index, s in enumerate(collected)
    ]

    return Advice(
        profile=profile,
        material=material,
        had_reference=reference is not None,
        suggestions=ordered,
        skipped=skipped,
    )


def check_reference(
    measurement: Measurement,
    *,
    profile: TargetProfile | None = None,
    against: Measurement | None = None,
) -> ReferenceCheck:
    """Taugt diese Messung als Maßstab?

    Eine technische Frage, keine künstlerische. Ob ein Take gut klingt,
    entscheidet der Nutzer; die Bibliothek sagt nur, ob er als Bezugspunkt
    brauchbar ist.
    """
    profile = profile or TargetProfile.raw()
    reasons: list[str] = []
    checked = [
        "Mindestdauer für belastbares LUFS-I",
        "Clipping",
        "True Peak innerhalb der Profilgrenze",
        "gemessener Rauschteppich vorhanden",
    ]

    if not measurement.lufs_i_reliable:
        reasons.append(
            f"Zu kurz für belastbares LUFS-I: {measurement.duration_s:.1f} s, "
            f"gefordert sind {measurement.params.lufs_min_duration_s:.0f} s."
        )
    if measurement.clipped_samples > 0:
        reasons.append(
            f"Übersteuert: {measurement.clipped_samples} Samples an der Vollaussteuerung."
        )
    if measurement.true_peak_dbtp > profile.true_peak_max_dbtp:
        reasons.append(
            f"True Peak {measurement.true_peak_dbtp:.2f} dBTP über der Profilgrenze "
            f"von {profile.true_peak_max_dbtp:.1f} dBTP."
        )
    if measurement.noise_floor_dbfs is None:
        reasons.append(
            "Kein Rauschteppich gemessen. Ohne --noise fehlt der Referenz ein Kennwert, "
            "an dem sich Abstand und Kompression prüfen lassen."
        )
    if not measurement.third_octave_hz:
        reasons.append(
            "Keine Terzbänder gemessen; ohne sie ist kein Spektralvergleich möglich."
        )

    if against is not None:
        checked.append("Vergleichbarkeit mit dem Prüfling")
        if against.sample_rate != measurement.sample_rate:
            reasons.append(
                f"Samplerate weicht ab: Referenz {measurement.sample_rate} Hz, "
                f"Prüfling {against.sample_rate} Hz."
            )
        if against.channel != measurement.channel:
            reasons.append(
                f"Kanalwahl weicht ab: Referenz Kanal {measurement.channel}, "
                f"Prüfling Kanal {against.channel}."
            )
        if against.source_sha256 == measurement.source_sha256:
            reasons.append("Referenz und Prüfling sind dieselbe Datei.")

    return ReferenceCheck(suitable=not reasons, reasons=reasons, checked=checked)
