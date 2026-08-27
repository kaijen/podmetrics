"""Kommandozeile.

Der Terminalgebrauch ist gleichrangig mit dem Bibliotheksgebrauch, nicht ein
Nebenprodukt. Dafür darf nichts installiert, gestartet oder geöffnet werden
müssen außer diesem Paket.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from .advice import advise, check_reference
from .compare import compare
from .io import load
from .models import Advice, Measurement, TargetProfile
from .report import measure

app = typer.Typer(
    add_completion=False,
    help="Messung von Sprachaufnahmen: Pegel, Lautheit, Spektrum — und Empfehlungen daraus.",
    no_args_is_help=True,
)

AUDIO_SUFFIXES = {".wav", ".flac", ".aiff", ".aif", ".ogg", ".mp3"}

# Farbe nur, wenn die Ausgabe auf ein Terminal geht. Bei Umleitung in eine
# Datei entfallen die Steuerzeichen.
console = Console(stderr=False, no_color=not sys.stdout.isatty())
errors = Console(stderr=True)


def _region(value: str | None, name: str) -> tuple[float, float] | None:
    if value is None:
        return None
    try:
        start, end = (float(part) for part in value.split(":", 1))
    except ValueError as exc:
        raise typer.BadParameter(f"{name} braucht die Form ANFANG:ENDE in Sekunden.") from exc
    return start, end


def _load_measurement(
    path: Path,
    *,
    channel: int,
    noise: tuple[float, float] | None,
    region: tuple[float, float] | None,
) -> Measurement:
    """Nimmt eine Audiodatei oder eine gespeicherte Messung als .json."""
    if path.suffix.lower() == ".json":
        return Measurement.from_dict(json.loads(path.read_text(encoding="utf-8")))
    return measure(load(path, channel=channel), noise_region=noise, region=region)


def _fmt(value: float | None, digits: int = 2) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def _row(name: str, m: Measurement) -> list[str]:
    return [
        name,
        _fmt(m.peak_dbfs),
        _fmt(m.peak_speech_dbfs),
        _fmt(m.true_peak_dbtp),
        _fmt(m.lufs_i) + ("" if m.lufs_i_reliable else " ?"),
        _fmt(m.crest_db, 1),
        _fmt(m.p10_p90_db, 1),
        _fmt(m.noise_floor_dbfs, 1),
    ]


HEADERS = [
    "Datei",
    "Peak",
    "PeakSpr",
    "TruePeak",
    "LUFS-I",
    "Crest",
    "P10–P90",
    "Rauschen",
]


def _table(rows: list[list[str]]) -> Table:
    table = Table(box=None, pad_edge=False)
    table.add_column(HEADERS[0], overflow="fold")
    for header in HEADERS[1:]:
        table.add_column(header, justify="right")
    for row in rows:
        table.add_row(*row)
    return table


def _print_advice(result: Advice) -> None:
    material = "bearbeitet" if result.material == "processed" else "unbearbeitet"
    console.print(
        f"[dim]Material:[/dim] {material}"
        f"   [dim]Referenz:[/dim] {'ja' if result.had_reference else 'keine'}"
        f"   [dim]Profil:[/dim] {result.profile.name}"
        f"   [dim]Regelstand:[/dim] {result.ruleset_version}"
    )
    console.print(f"[dim]Kette:[/dim] {' → '.join(result.chain_order)}\n")

    if not result.suggestions:
        console.print("Keine Empfehlung. Die geprüften Kennwerte liegen im Zielbereich.")
    for suggestion in result.suggestions:
        marker = "zuerst" if suggestion.order == 1 else "danach"
        console.print(
            f"[bold]{suggestion.order}. {suggestion.title}[/bold]  "
            f"[{suggestion.severity}]  ({marker})"
        )
        console.print(f"   {suggestion.detail}")
        for evidence in suggestion.evidence:
            console.print(
                f"   [dim]Grund:[/dim] {evidence.field} = {evidence.value:.2f} "
                f"{evidence.unit} (Schwelle {evidence.threshold:.2f})"
            )
        for expectation in suggestion.expected:
            console.print(
                f"   [dim]Erwartung:[/dim] {expectation.field} {expectation.direction} "
                f"um {expectation.amount:.1f} {expectation.unit}"
            )
        if suggestion.parameters:
            values = ", ".join(f"{k} = {v:g}" for k, v in suggestion.parameters.items())
            console.print(f"   [dim]Werte:[/dim] {values}")
        console.print()

    for note in result.skipped:
        console.print(f"[dim]Nicht geprüft:[/dim] {note}")


@app.command()
def measure_cmd(
    file: Annotated[Path, typer.Argument(help="Audiodatei")],
    noise: Annotated[
        str | None, typer.Option("--noise", help="Sprechpause, ANFANG:ENDE in s")
    ] = None,
    region: Annotated[
        str | None, typer.Option("--region", help="Auszuwertender Abschnitt")
    ] = None,
    channel: Annotated[int, typer.Option("--channel", help="Kanal der Quelle")] = 0,
    as_json: Annotated[bool, typer.Option("--json", help="Maschinenlesbar ausgeben")] = False,
) -> None:
    """Eine Datei messen."""
    result = measure(
        load(file, channel=channel),
        noise_region=_region(noise, "--noise"),
        region=_region(region, "--region"),
    )
    if as_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return
    console.print(_table([_row(file.name, result)]))
    if not result.lufs_i_reliable:
        errors.print(
            f"[yellow]Hinweis:[/yellow] LUFS-I ist unzuverlässig — {result.duration_s:.1f} s, "
            f"gefordert sind {result.params.lufs_min_duration_s:.0f} s."
        )
    if result.plosives:
        errors.print(
            f"[yellow]Hinweis:[/yellow] {len(result.plosives)} Plosivspitze(n) erkannt. "
            "Maßstab für den Gain ist PeakSpr, nicht Peak."
        )


@app.command()
def batch(
    directory: Annotated[Path, typer.Argument(help="Ordner mit Aufnahmen")],
    reference: Annotated[Path | None, typer.Option("--reference", help="Referenzdatei")] = None,
    region: Annotated[str | None, typer.Option("--region")] = None,
    channel: Annotated[int, typer.Option("--channel")] = 0,
    csv_path: Annotated[
        Path | None, typer.Option("--csv", help="Tabelle zusätzlich schreiben")
    ] = None,
) -> None:
    """Einen Ordner messen — eine Zeile pro Datei.

    Bleibt ohne Empfehlungen: Wer für zwanzig Dateien Ratschläge ausgibt,
    bekommt eine Textwand statt einer Tabelle.
    """
    files = sorted(p for p in directory.iterdir() if p.suffix.lower() in AUDIO_SUFFIXES)
    if not files:
        raise typer.BadParameter(f"Keine Audiodateien in {directory}.")

    slice_ = _region(region, "--region")
    rows = []
    for path in files:
        result = measure(load(path, channel=channel), region=slice_)
        rows.append(_row(path.name, result))

    if reference is not None:
        console.print(f"[dim]Referenz:[/dim] {reference.name}\n")
    console.print(_table(rows))

    if csv_path is not None:
        with open(csv_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(HEADERS)
            writer.writerows(rows)
        errors.print(f"[dim]geschrieben:[/dim] {csv_path}")


@app.command()
def compare_cmd(
    files: Annotated[list[Path], typer.Argument(help="Zu vergleichende Dateien")],
    reference: Annotated[Path, typer.Option("--reference", help="Referenzdatei")],
    channel: Annotated[int, typer.Option("--channel")] = 0,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Messungen gegen eine Referenz stellen."""
    ref = _load_measurement(reference, channel=channel, noise=None, region=None)
    items = [_load_measurement(p, channel=channel, noise=None, region=None) for p in files]
    result = compare(items, reference=ref)

    if as_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    table = Table(box=None, pad_edge=False)
    table.add_column("Datei", overflow="fold")
    for header in ("ΔPeak", "ΔTruePeak", "ΔLUFS", "ΔCrest", "ΔMedian", "ΔP10–P90", "ΔRauschen"):
        table.add_column(header, justify="right")
    for path, delta in zip(files, result.deltas, strict=True):
        table.add_row(
            path.name,
            f"{delta.peak_db:+.2f}",
            f"{delta.true_peak_db:+.2f}",
            f"{delta.lufs_i_db:+.2f}",
            f"{delta.crest_db:+.1f}",
            f"{delta.speech_median_db:+.1f}",
            f"{delta.p10_p90_db:+.1f}",
            "—" if delta.noise_floor_db is None else f"{delta.noise_floor_db:+.1f}",
        )
    console.print(table)
    for warning in result.warnings:
        errors.print(f"[yellow]Warnung:[/yellow] {warning}")


@app.command()
def advise_cmd(
    file: Annotated[Path, typer.Argument(help="Audiodatei")],
    reference: Annotated[
        Path | None,
        typer.Option("--reference", help="Audiodatei oder gespeicherte Messung (.json)"),
    ] = None,
    topic: Annotated[
        list[str] | None,
        typer.Option("--topic", help="position, eq oder comp; mehrfach angebbar"),
    ] = None,
    noise: Annotated[str | None, typer.Option("--noise")] = None,
    region: Annotated[str | None, typer.Option("--region")] = None,
    channel: Annotated[int, typer.Option("--channel")] = 0,
    processed: Annotated[
        bool, typer.Option("--processed", help="Material ist bereits bearbeitet")
    ] = False,
    delivery: Annotated[
        bool, typer.Option("--delivery", help="Gegen das Profil der fertigen Folge raten")
    ] = False,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Empfehlungen ableiten: was als Nächstes anders zu machen ist."""
    noise_region = _region(noise, "--noise")
    slice_ = _region(region, "--region")

    subject = measure(load(file, channel=channel), noise_region=noise_region, region=slice_)
    ref = (
        _load_measurement(reference, channel=channel, noise=noise_region, region=slice_)
        if reference is not None
        else None
    )
    result = advise(
        subject,
        reference=ref,
        profile=TargetProfile.delivery() if delivery else TargetProfile.raw(),
        topics=tuple(topic) if topic else ("position", "eq", "comp"),
        material="processed" if processed else "raw",
    )
    if as_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return
    _print_advice(result)


@app.command()
def check_reference_cmd(
    file: Annotated[Path, typer.Argument(help="Kandidat für die Referenz")],
    against: Annotated[
        Path | None,
        typer.Option("--against", help="Prüfling, gegen den verglichen werden soll"),
    ] = None,
    noise: Annotated[str | None, typer.Option("--noise")] = None,
    channel: Annotated[int, typer.Option("--channel")] = 0,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Prüfen, ob eine Messung als Maßstab taugt.

    Eine technische Frage, keine künstlerische: Ob der Take gut klingt,
    entscheidest Du.
    """
    noise_region = _region(noise, "--noise")
    candidate = _load_measurement(file, channel=channel, noise=noise_region, region=None)
    other = (
        _load_measurement(against, channel=channel, noise=None, region=None)
        if against is not None
        else None
    )
    result = check_reference(candidate, against=other)

    if as_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        raise typer.Exit(0 if result.suitable else 1)

    if result.suitable:
        console.print(
            f"[green]Taugt als Referenz.[/green] Geprüft: {len(result.checked)} Punkte."
        )
    else:
        console.print("[red]Taugt nicht als Referenz.[/red]")
        for reason in result.reasons:
            console.print(f"  • {reason}")
    console.print(
        "\n[dim]Ob der Take gut klingt, sagt diese Prüfung nicht. "
        "Das entscheidest Du nach Gehör.[/dim]"
    )
    raise typer.Exit(0 if result.suitable else 1)


# Befehlsnamen ohne das _cmd-Suffix, das nur Namenskollisionen im Modul vermeidet.
for command, name in (
    (measure_cmd, "measure"),
    (compare_cmd, "compare"),
    (advise_cmd, "advise"),
    (check_reference_cmd, "check-reference"),
):
    for info in app.registered_commands:
        if info.callback is command:
            info.name = name


def main() -> None:
    app()


if __name__ == "__main__":
    main()
