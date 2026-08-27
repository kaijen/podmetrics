"""Empfehlungsregeln.

Getestet wird aus von Hand konstruierten Measurement-Objekten und nicht aus
Audio: je Regel eines knapp über der Schwelle, das sie auslöst, und eines
knapp darunter, das sie nicht auslöst. Das hält die Tests schnell und macht
die Schwellen im Test sichtbar, statt sie im Code zu verstecken.
"""

from __future__ import annotations

import pytest

from helpers import a_plosive, bands, make_measurement
from podmetrics import advise, check_reference
from podmetrics.models import TargetProfile

PROFILE = TargetProfile.raw()


def ids(result) -> set[str]:
    return {s.id for s in result.suggestions}


def reference():
    return make_measurement()


# --- Position ---------------------------------------------------------------


def test_proximity_excess_fires_above_threshold():
    # Schwelle ist 3 dB im Mittel über 100–250 Hz.
    take = make_measurement(
        third_octave_db=bands(hz_100=3.5, hz_125=3.5, hz_160=3.5, hz_200=3.5, hz_250=3.5)
    )
    assert "position.proximity_excess" in ids(advise(take, reference=reference()))


def test_proximity_excess_silent_below_threshold():
    take = make_measurement(
        third_octave_db=bands(hz_100=2.5, hz_125=2.5, hz_160=2.5, hz_200=2.5, hz_250=2.5)
    )
    assert "position.proximity_excess" not in ids(advise(take, reference=reference()))


def test_off_axis_needs_the_upper_band_to_fall_further():
    # 4–8 kHz fällt ab, 8–12 kHz stärker: die Signatur der Achse.
    take = make_measurement(
        third_octave_db=bands(hz_5000=-4.0, hz_6300=-4.0, hz_8000=-7.0, hz_10000=-7.0)
    )
    assert "position.off_axis" in ids(advise(take, reference=reference()))


def test_even_high_frequency_loss_is_not_off_axis():
    """Ein gleichmäßiger Abfall über beide Bänder ist ein anderer Befund —
    eher Abstand oder Windschutz — und darf die Achsenregel nicht auslösen."""
    take = make_measurement(
        third_octave_db=bands(hz_5000=-5.0, hz_6300=-5.0, hz_8000=-5.0, hz_10000=-5.0)
    )
    assert "position.off_axis" not in ids(advise(take, reference=reference()))


def test_sibilance_fires_on_five_to_eight_kilohertz():
    take = make_measurement(third_octave_db=bands(hz_5000=4.0, hz_6300=4.0, hz_8000=4.0))
    assert "position.sibilance" in ids(advise(take, reference=reference()))


def test_low_snr_with_flat_spectrum_means_distance():
    take = make_measurement(noise_floor_dbfs=-50.0)  # SNR 29 dB < 35 dB
    assert "position.distance_excess" in ids(advise(take, reference=reference()))


def test_sufficient_snr_does_not_fire():
    take = make_measurement(noise_floor_dbfs=-58.0)  # SNR 37 dB
    assert "position.distance_excess" not in ids(advise(take, reference=reference()))


def test_drift_needs_both_span_and_slope():
    """Eine große Spanne allein ist Sprechweise. Erst die Drift über Minuten
    macht daraus einen Abstandsbefund."""
    times = [float(i) for i in range(20)]
    drifting = make_measurement(
        speech_p10_dbfs=-32.0,
        speech_p90_dbfs=-10.0,  # Spanne 22 dB
        short_term_times_s=times,
        short_term_lufs=[-18.0 - 0.3 * i for i in range(20)],  # rund 5,7 dB Drift
    )
    steady = make_measurement(
        speech_p10_dbfs=-32.0,
        speech_p90_dbfs=-10.0,  # gleiche Spanne
        short_term_times_s=times,
        short_term_lufs=[-21.0 + (1.0 if i % 2 else -1.0) for i in range(20)],
    )
    assert "position.drift" in ids(advise(drifting, reference=reference()))
    assert "position.drift" not in ids(advise(steady, reference=reference()))


def test_plosives_are_reported_with_the_speech_peak():
    take = make_measurement(plosives=[a_plosive()], peak_dbfs=-0.2, peak_speech_dbfs=-8.0)
    result = advise(take, reference=reference())
    suggestion = next(s for s in result.suggestions if s.id == "position.plosives")
    assert "peak_speech_dbfs" in {e.field for e in suggestion.evidence} or any(
        "peak_speech" in e.field for e in suggestion.evidence
    )


def test_comb_filter_is_reported_when_measured():
    take = make_measurement(comb_spacing_hz=1000.0, comb_depth_db=9.0)
    result = advise(take, reference=reference())
    assert "position.comb_filter" in ids(result)
    suggestion = next(s for s in result.suggestions if s.id == "position.comb_filter")
    assert suggestion.severity == "high"


# --- Reihenfolge und Rückhalt ------------------------------------------------


def test_eq_is_held_back_by_an_open_position_finding():
    """Was der Abstand behebt, wird nicht per Filter repariert."""
    take = make_measurement(
        comb_spacing_hz=1000.0, comb_depth_db=9.0, third_octave_db=bands(hz_1000=6.0)
    )
    result = advise(take, reference=reference())
    assert "eq.blocked_by_position" in ids(result)
    assert not any(s.id.startswith("eq.band_") for s in result.suggestions)


def test_topics_are_ordered_position_eq_comp():
    take = make_measurement(third_octave_db=bands(hz_1000=6.0))
    topics = [s.topic for s in advise(take, reference=reference()).suggestions]
    assert topics == sorted(topics, key=("position", "eq", "comp").index)


def test_order_starts_at_one_and_is_dense():
    result = advise(make_measurement(), reference=reference())
    assert [s.order for s in result.suggestions] == list(range(1, len(result.suggestions) + 1))


def test_processed_material_skips_position_with_a_reason():
    result = advise(make_measurement(), reference=reference(), material="processed")
    assert not any(s.topic == "position" for s in result.suggestions)
    assert any("position" in note for note in result.skipped)


def test_missing_reference_is_named_not_swallowed():
    result = advise(make_measurement())
    assert not result.had_reference
    assert any("Referenz" in note for note in result.skipped)


# --- EQ ---------------------------------------------------------------------


def test_eq_gain_is_capped_by_the_profile():
    take = make_measurement(third_octave_db=bands(hz_1000=12.0))
    result = advise(take, reference=reference(), topics=("eq",))
    band = next(s for s in result.suggestions if s.id.startswith("eq.band_"))
    assert abs(band.parameters["gain_db"]) <= PROFILE.eq_max_gain_db
    assert "Profilgrenze" in band.detail


def test_eq_uses_bandwidth_not_q():
    """ReaEQ nimmt Bandbreite in Oktaven. Die Umrechnung auf Q wäre eine
    Fehlerquelle an einer Stelle, an der der Nutzer Zahlen abtippt."""
    take = make_measurement(third_octave_db=bands(hz_1000=6.0))
    band = next(
        s
        for s in advise(take, reference=reference(), topics=("eq",)).suggestions
        if s.id.startswith("eq.band_")
    )
    assert "bandwidth_octaves" in band.parameters
    assert "q" not in band.parameters


def test_every_boost_comes_with_an_output_gain():
    """Version 007 der Messreihe clippte an 54 Samples, weil der Ausgangs-Gain
    nach einer Anhebung nicht nachgezogen war."""
    take = make_measurement(third_octave_db=bands(hz_1000=-6.0))  # Anhebung nötig
    result = advise(take, reference=reference(), topics=("eq",))
    boosts = [s for s in result.suggestions if s.parameters.get("gain_db", 0) > 0]
    assert boosts
    assert "eq.output_gain" in ids(result)


def test_no_output_gain_suggestion_without_a_boost():
    take = make_measurement(third_octave_db=bands(hz_1000=6.0))  # nur Absenkung
    assert "eq.output_gain" not in ids(advise(take, reference=reference(), topics=("eq",)))


def test_eq_respects_the_filter_limit():
    take = make_measurement(
        third_octave_db=bands(hz_125=6.0, hz_250=6.0, hz_1000=6.0, hz_5000=6.0, hz_10000=6.0)
    )
    result = advise(take, reference=reference(), topics=("eq",))
    assert (
        sum(s.id.startswith("eq.band_") for s in result.suggestions) <= PROFILE.eq_max_filters
    )


# --- Kompression ------------------------------------------------------------


def test_threshold_lies_below_the_median():
    """Die Richtung ist der eigentliche Inhalt der Regel: Ein Threshold über
    dem Median lässt den Kompressor nur die obere Hälfte der Sprache sehen."""
    take = make_measurement(speech_median_dbfs=-21.0)
    suggestion = next(
        s for s in advise(take, topics=("comp",)).suggestions if s.id == "comp.threshold"
    )
    assert suggestion.parameters["threshold_db"] == pytest.approx(-24.0)
    assert suggestion.parameters["threshold_db"] < take.speech_median_dbfs


def test_threshold_follows_the_recording_level():
    quiet = make_measurement(speech_median_dbfs=-30.0)
    suggestion = next(
        s for s in advise(quiet, topics=("comp",)).suggestions if s.id == "comp.threshold"
    )
    assert suggestion.parameters["threshold_db"] == pytest.approx(-33.0)


def test_attack_and_release_come_from_the_profile_not_the_measurement():
    suggestion = next(
        s
        for s in advise(make_measurement(), topics=("comp",)).suggestions
        if s.id == "comp.ratio"
    )
    assert suggestion.parameters["attack_ms"] == PROFILE.comp_attack_ms
    assert suggestion.parameters["release_ms"] == PROFILE.comp_release_ms
    assert "nicht gerechnet" in suggestion.detail


def test_raised_noise_floor_flags_over_compression():
    """Version 012 der Messreihe war genau daran unbrauchbar: Lautheit und
    Dynamikspanne stimmten, der Rauschteppich stand bei −32,5 dB."""
    over = make_measurement(noise_floor_dbfs=-32.5)
    assert "comp.noise_lift" in ids(advise(over, topics=("comp",), material="processed"))


def test_quiet_noise_floor_does_not_flag():
    fine = make_measurement(noise_floor_dbfs=-55.0)
    assert "comp.noise_lift" not in ids(advise(fine, topics=("comp",), material="processed"))


def test_true_peak_over_the_limit_lowers_the_output():
    hot = make_measurement(true_peak_dbtp=-0.5)  # Profil raw erlaubt −3
    result = advise(hot, topics=("comp",))
    assert "comp.true_peak" in ids(result)
    suggestion = next(s for s in result.suggestions if s.id == "comp.true_peak")
    assert suggestion.parameters["output_gain_db"] < 0
    assert "Plugin" in suggestion.detail  # kein weiteres Plugin in die Kette


def test_makeup_gain_is_declared_a_starting_value():
    suggestion = next(
        s
        for s in advise(make_measurement(), topics=("comp",)).suggestions
        if s.id == "comp.makeup"
    )
    assert "Startwert" in suggestion.title
    assert "erneut" in suggestion.detail and "messen" in suggestion.detail


# --- Vertrag ----------------------------------------------------------------


def test_suggestion_ids_are_unique():
    take = make_measurement(
        third_octave_db=bands(hz_125=6.0, hz_1000=-6.0, hz_5000=5.0),
        noise_floor_dbfs=-50.0,
        true_peak_dbtp=-0.5,
        plosives=[a_plosive()],
    )
    suggestions = advise(take, reference=reference()).suggestions
    assert len({s.id for s in suggestions}) == len(suggestions)


def test_every_suggestion_names_evidence_and_expectation():
    """Jede Empfehlung nennt die auslösenden Messwerte und die erwartete
    Wirkung. Ohne den zweiten Punkt ist Beratung nicht falsifizierbar."""
    take = make_measurement(
        third_octave_db=bands(hz_125=6.0, hz_5000=5.0), noise_floor_dbfs=-50.0
    )
    for suggestion in advise(take, reference=reference()).suggestions:
        if suggestion.id == "eq.blocked_by_position":
            continue  # ein Hinweis, keine Empfehlung
        assert suggestion.evidence, suggestion.id
        assert suggestion.expected, suggestion.id


def test_ids_follow_the_topic_dot_name_pattern():
    take = make_measurement(third_octave_db=bands(hz_125=6.0), noise_floor_dbfs=-50.0)
    for suggestion in advise(take, reference=reference()).suggestions:
        topic, _, name = suggestion.id.partition(".")
        assert topic == suggestion.topic
        assert name


def test_advice_carries_its_own_preconditions():
    result = advise(make_measurement(), reference=reference(), material="raw")
    assert result.profile == PROFILE
    assert result.material == "raw"
    assert result.had_reference is True
    assert result.ruleset_version >= 1
    assert result.chain_order[0] == "Hochpass"


def test_unknown_topic_is_rejected():
    with pytest.raises(ValueError, match="Unbekannte Themen"):
        advise(make_measurement(), topics=("gitarre",))


def test_unknown_material_is_rejected():
    with pytest.raises(ValueError, match="material"):
        advise(make_measurement(), material="vielleicht")


# --- Referenzprüfung --------------------------------------------------------


def test_short_material_is_no_reference():
    result = check_reference(make_measurement(lufs_i_reliable=False, duration_s=12.0))
    assert not result.suitable
    assert any("kurz" in reason for reason in result.reasons)


def test_clipped_material_is_no_reference():
    result = check_reference(make_measurement(clipped_samples=54))
    assert not result.suitable
    assert any("54" in reason for reason in result.reasons)


def test_missing_noise_floor_is_no_reference():
    result = check_reference(make_measurement(noise_floor_dbfs=None))
    assert not result.suitable
    assert any("Rauschteppich" in reason for reason in result.reasons)


def test_clean_take_is_a_reference():
    assert check_reference(make_measurement()).suitable


def test_mismatched_sample_rate_is_reported():
    result = check_reference(make_measurement(), against=make_measurement(sample_rate=44100))
    assert not result.suitable
    assert any("Samplerate" in reason for reason in result.reasons)


def test_same_file_cannot_be_its_own_reference():
    same = make_measurement()
    result = check_reference(same, against=same)
    assert not result.suitable
    assert any("dieselbe Datei" in reason for reason in result.reasons)
