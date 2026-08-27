"""Die Dokumentation gegen den Code prüfen.

CLAUDE.md sagt: Eine Dokumentationsseite, die einer Festlegung widerspricht,
ist ein Fehler und kein zweiter Standpunkt. Ohne Test bleibt das eine
Absichtserklärung — spätestens beim dritten Feld, das jemand ergänzt, ohne die
Seite nachzuziehen.

Geprüft wird nur Nachweisbares: Feldnamen, exportierte Namen, Befehle und
Optionen, Suggestion-IDs. Ob der Text daneben stimmt, kann kein Test wissen.
"""

from __future__ import annotations

import inspect
import re
from dataclasses import fields, is_dataclass
from pathlib import Path

import pytest

import podmetrics
from podmetrics import advice, cli, models

DOCS = Path(__file__).resolve().parent.parent / "docs"

# Die Dokumentation liegt nicht im Quellarchiv. Läuft die Suite aus einem
# installierten sdist, gibt es hier nichts zu prüfen.
pytestmark = pytest.mark.skipif(not DOCS.is_dir(), reason="docs/ nicht vorhanden")


def documentation() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(DOCS.rglob("*.md")))


def documented_models(text: str) -> dict[str, set[str]]:
    """Feldnamen je Modell, wie sie in den Codeblöcken der Doku stehen."""
    stripped = re.sub(r"@dataclass\(frozen=True\)\n", "", text)
    blocks = re.findall(r"class (\w+)[^:]*:\n((?:(?: {4}[^\n]*)?\n)+)", stripped)
    return {
        name: set(re.findall(r"^ {4}(\w+)\s*:", body, re.MULTILINE)) for name, body in blocks
    }


MODEL_NAMES = [
    name
    for name in dir(models)
    if is_dataclass(getattr(models, name, None)) and not name.startswith("_")
]


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_documented_fields_match_the_code(name):
    text = documentation()
    documented = documented_models(text).get(name)
    if documented is None:
        pytest.skip(f"{name} hat keinen Feldblock in der Dokumentation")
    actual = {f.name for f in fields(getattr(models, name))}
    assert actual - documented == set(), f"{name}: im Code, nicht in der Doku"
    assert documented - actual == set(), f"{name}: in der Doku, nicht im Code"


@pytest.mark.parametrize("name", [n for n in podmetrics.__all__ if not n.startswith("__")])
def test_public_names_appear_in_the_documentation(name):
    """Die exportierten Namen sind der Vertrag. Ein Vertrag, der nirgends
    steht, ist keiner."""
    assert name in documentation(), f"{name} kommt in der Dokumentation nicht vor"


COMMANDS = {
    info.name or info.callback.__name__: info.callback for info in cli.app.registered_commands
}


@pytest.mark.parametrize("command", sorted(COMMANDS))
def test_cli_commands_are_documented(command):
    assert command in documentation(), f"CLI-Befehl {command} fehlt in der Dokumentation"


@pytest.mark.parametrize("command", sorted(COMMANDS))
def test_cli_options_are_documented(command):
    text = documentation()
    positional = {"file", "directory", "files"}
    for name, parameter in inspect.signature(COMMANDS[command]).parameters.items():
        if name in positional or parameter.default is inspect.Parameter.empty:
            continue
        flag = "--" + name.replace("_", "-").removesuffix("-path").removeprefix("as-")
        assert flag in text, f"{command}: Option {flag} fehlt in der Dokumentation"


def emitted_suggestion_ids() -> set[str]:
    source = inspect.getsource(advice)
    plain = set(re.findall(r'id="((?:position|eq|comp)\.\w+)"', source))
    formatted = set(re.findall(r'id=f"((?:position|eq|comp)\.[^"]+)"', source))
    return plain | formatted


def test_suggestion_ids_are_documented():
    """Die IDs sind Teil des Vertrags wie die Funktionsnamen: Die Webapp hängt
    Texte daran."""
    text = documentation()
    missing = []
    for suggestion_id in sorted(emitted_suggestion_ids()):
        _, _, name = suggestion_id.partition(".")
        if "{" in name:  # eq.band_<frequenz>hz wird zur Laufzeit gebildet
            name = "band_<frequenz>hz"
        if name not in text:
            missing.append(suggestion_id)
    assert not missing, f"Suggestion-IDs fehlen in der Dokumentation: {missing}"


def test_the_check_would_notice_a_missing_field():
    """Ein Prüfer, der nie anschlägt, ist kein Prüfer."""
    documented = documented_models("class Measurement:\n    peak_dbfs: float\n")
    actual = {f.name for f in fields(models.Measurement)}
    assert actual - documented["Measurement"], "Die Feldsuche findet nichts"
