#!/usr/bin/env python3
"""Baut aus den mkdocs-Quellen ein EPUB.

Die Reihenfolge der Kapitel kommt aus der Navigation in mkdocs.yml. Es gibt
keine zweite Kapitelliste — eine Seite, die in der Navigation fehlt, fehlt auch
im EPUB, und das ist die richtige Kopplung.

Gerendert wird mit denselben Markdown-Erweiterungen, die mkdocs benutzt.
Deshalb überleben Admonitions und Tabellen den Weg ins EPUB, statt als
Rohtext durchzuschlagen.

Aufruf:  python scripts/build_epub.py [ZIELDATEI]
"""

from __future__ import annotations

import mimetypes
import os
import re
import sys
from pathlib import Path, PurePosixPath

import markdown
import yaml
from ebooklib import epub

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "mkdocs.yml"

# Wie in mkdocs.yml, aber ohne die Permalink-Anker: Ein "¶" hinter jeder
# Überschrift ist im Browser eine Bedienhilfe und im E-Book nur Müll.
EXTENSIONS = [
    "admonition",
    "attr_list",
    "def_list",
    "tables",
    "toc",
    "pymdownx.details",
    "pymdownx.superfences",
]

CSS = """
body { line-height: 1.5; }
h1, h2, h3 { line-height: 1.25; }
code, pre { font-family: monospace; font-size: 0.9em; }
pre { padding: 0.6em; background: #f4f4f4; overflow-x: auto;
      border-left: 3px solid #ccc; }
table { border-collapse: collapse; width: 100%; font-size: 0.9em; }
th, td { border: 1px solid #bbb; padding: 0.3em 0.5em; text-align: left; }
th { background: #f0f0f0; }
blockquote { border-left: 3px solid #bbb; padding-left: 1em; }

/* Admonitions: Rahmen statt Farbe, damit sie auch auf E-Ink lesbar bleiben. */
.admonition { border: 1px solid #999; border-left-width: 4px;
              padding: 0.6em 0.8em; margin: 1.2em 0; }
.admonition-title { font-weight: bold; margin: 0 0 0.4em 0; }
.admonition.warning, .admonition.danger { border-left-color: #000; }
details { border: 1px solid #999; padding: 0.5em; margin: 1em 0; }
summary { font-weight: bold; }
"""


def load_config() -> dict:
    # mkdocs.yml kann Python-spezifische Tags enthalten; unsere nicht. Ein
    # unbekannter Tag soll auffallen und nicht still verschluckt werden.
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def walk_nav(nav) -> list[tuple[str, str]]:
    """Navigation zu einer flachen Liste (Titel, Pfad) machen."""
    pages: list[tuple[str, str]] = []
    for entry in nav:
        if isinstance(entry, str):
            pages.append(("", entry))
            continue
        for title, target in entry.items():
            if isinstance(target, list):
                pages.extend(walk_nav(target))
            else:
                pages.append((title, target))
    return pages


def render(md_path: Path) -> tuple[str, str]:
    """Eine Seite nach XHTML rendern. Gibt (Titel, HTML) zurück."""
    text = md_path.read_text(encoding="utf-8")
    md = markdown.Markdown(
        extensions=EXTENSIONS,
        extension_configs={"toc": {"permalink": False}},
        output_format="xhtml",
    )
    html = md.convert(text)

    # Überschrift der Seite für Kapitelnamen und Inhaltsverzeichnis.
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = m.group(1).strip() if m else md_path.stem

    # Querverweise zeigen auf .md-Dateien. Die Verzeichnisstruktur bleibt im
    # EPUB erhalten, deshalb genügt der Tausch der Endung — relative Pfade
    # und Anker stimmen dann von allein.
    html = re.sub(r'(href="(?!https?:)[^"]*?)\.md(#[^"]*)?"',
                  lambda m: '%s.xhtml%s"' % (m.group(1), m.group(2) or ""),
                  html)
    return title, html


def collect_images(html: str, page: Path) -> list[tuple[str, Path]]:
    """Lokale Bilder einsammeln, damit sie nicht still fehlen."""
    found = []
    for src in re.findall(r'<img[^>]+src="([^"]+)"', html):
        if src.startswith(("http://", "https://", "data:")):
            continue
        target = (page.parent / src).resolve()
        if target.is_file():
            found.append((src, target))
        else:
            print("  WARNUNG: Bild nicht gefunden: %s (in %s)" % (src, page),
                  file=sys.stderr)
    return found


def check_links(rendered: dict[str, str]) -> list[str]:
    """Interne Verweise prüfen. Gibt die Fehler zurück, leer heißt sauber.

    Dieselbe Regel wie beim Seitenbau mit --strict: Ein toter Verweis bricht
    den Bau, statt still ausgeliefert zu werden. Im EPUB wiegt das schwerer
    als auf einer Webseite, denn dort merkt man den Fehler beim Klicken; hier
    liegt die Datei schon beim Leser.
    """
    ids: dict[str, set[str]] = {}
    for name, html in rendered.items():
        ids[name] = set(re.findall(r'\sid="([^"]+)"', html))

    errors = []
    for name, html in rendered.items():
        base = PurePosixPath(name).parent
        for href in re.findall(r'href="([^"]+)"', html):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            target, _, anchor = href.partition("#")
            if not target:
                page = name              # Verweis innerhalb der Seite
            else:
                if not target.endswith(".xhtml"):
                    continue             # style.css und Ähnliches
                page = str((base / target).as_posix())
                page = str(PurePosixPath(os.path.normpath(page)).as_posix())
                if page not in rendered:
                    errors.append("%s: Ziel fehlt: %s" % (name, href))
                    continue
            if anchor and anchor not in ids[page]:
                errors.append("%s: Anker fehlt: %s" % (name, href))
    return errors


def build(out_path: Path) -> None:
    cfg = load_config()
    docs_dir = ROOT / cfg.get("docs_dir", "docs")
    pages = walk_nav(cfg["nav"])

    book = epub.EpubBook()
    book.set_identifier(cfg.get("site_url", "podmetrics").rstrip("/"))
    book.set_title(cfg.get("site_name", "podmetrics"))
    book.set_language("de")
    if cfg.get("copyright"):
        book.add_author(cfg["copyright"])
    if cfg.get("site_description"):
        book.add_metadata("DC", "description", cfg["site_description"])

    style = epub.EpubItem(uid="style", file_name="style.css",
                          media_type="text/css", content=CSS)
    book.add_item(style)

    chapters = []
    embedded: set[str] = set()
    rendered: dict[str, str] = {}

    for nav_title, rel in pages:
        md_path = docs_dir / rel
        if not md_path.is_file():
            raise SystemExit("Seite aus der Navigation fehlt: %s" % md_path)

        title, html = render(md_path)
        title = title or nav_title

        for src, target in collect_images(html, md_path):
            name = "images/" + target.name
            if name not in embedded:
                book.add_item(epub.EpubItem(
                    uid="img_%d" % len(embedded),
                    file_name=name,
                    media_type=mimetypes.guess_type(target.name)[0]
                    or "application/octet-stream",
                    content=target.read_bytes()))
                embedded.add(name)
            depth = rel.count("/")
            html = html.replace('src="%s"' % src,
                                'src="%s%s"' % ("../" * depth, name))

        chapter = epub.EpubHtml(
            title=title,
            file_name=rel[:-3] + ".xhtml",
            lang="de",
        )
        chapter.content = "<h1>%s</h1>\n%s" % (title, html) \
            if not html.lstrip().startswith("<h1") else html
        chapter.add_item(style)
        book.add_item(chapter)
        chapters.append(chapter)
        rendered[chapter.file_name] = chapter.content

    errors = check_links(rendered)
    if errors:
        for line in errors:
            print("  FEHLER: %s" % line, file=sys.stderr)
        raise SystemExit("EPUB nicht gebaut: %d tote Verweise" % len(errors))

    book.toc = tuple(chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + chapters

    out_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(out_path), book)
    print("%s — %d Kapitel, %d Bilder, %.1f KB"
          % (out_path, len(chapters), len(embedded),
             out_path.stat().st_size / 1024))


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "site" / "podmetrics.epub"
    build(target)
