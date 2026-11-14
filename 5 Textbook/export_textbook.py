#!/usr/bin/env python3
"""Build one tidy PDF from the PDP's modular master textbook.

Run from repository root:
    python3 -m pip install mistune weasyprint
    python3 "5 Textbook/export_textbook.py"

Optional:
    python3 "5 Textbook/export_textbook.py" --output textbook.pdf
"""
import argparse
import html
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import mistune
from weasyprint import HTML

LEVELS = ("B", "I", "P", "E")

CSS = """
@page {
    size: A4;
    margin: 19mm 17mm 20mm;
    @bottom-left {
        content: "Software Engineering  |  Master Textbook";
        color: #758091;
        font-size: 8pt;
    }
    @bottom-right {
        content: counter(page);
        color: #758091;
        font-size: 8pt;
    }
}
@page:first {
    @bottom-left { content: none; }
    @bottom-right { content: none; }
}
body {
    font-family: "DejaVu Sans", sans-serif;
    font-size: 9.5pt;
    line-height: 1.53;
    color: #27313d;
}
h1, h2, h3, h4, h5 { color: #19314a; line-height: 1.24; break-after: avoid; }
h1 { font-size: 21pt; margin: 0 0 11pt; }
h2 { font-size: 14pt; margin: 16pt 0 7pt; }
h3 { font-size: 11.5pt; margin: 13pt 0 5pt; }
h4 { font-size: 10pt; margin: 11pt 0 4pt; }
p { margin: 0 0 8pt; orphans: 2; widows: 2; }
li { margin-bottom: 3pt; }
ul, ol { margin: 4pt 0 9pt; padding-left: 19pt; }
a { color: #245b83; text-decoration: none; }
strong { color: #172c3d; }
code, pre { font-family: "DejaVu Sans Mono", monospace; font-size: 8pt; }
code { background: #f1f4f7; padding: 1px 2px; }
pre { background: #f2f5f8; border-left: 2pt solid #bdcddd;
      padding: 9pt; margin: 10pt 0; white-space: pre-wrap;
      overflow-wrap: anywhere; line-height: 1.35; }
pre code { background: none; padding: 0; }
table { width: 100%; border-collapse: collapse; font-size: 8.2pt;
        margin: 9pt 0 13pt; overflow-wrap: anywhere; }
th, td { border-bottom: .6pt solid #dae1e7; padding: 5pt 6pt;
         text-align: left; vertical-align: top; }
th { background: #edf2f6; color: #203952; font-weight: bold; }
tr { break-inside: avoid; }
img { max-width: 100%; height: auto; }
blockquote { border-left: 2pt solid #b7c9d7; padding-left: 10pt;
             color: #435366; margin: 10pt 0; }
hr { border: 0; border-top: .6pt solid #dbe2e8; margin: 15pt 0; }
section.part, section.chapter, section.backmatter { break-before: page; }
section.level { margin-top: 12pt; }
section.chapter > h1, section.part > h1 { border-bottom: 1pt solid #cad6df; padding-bottom: 8pt; }
section.level h2:first-of-type { border-bottom: .6pt solid #dae3eb; padding-bottom: 5pt; }
"""

def collect(book: Path) -> list[tuple[Path, str]]:
    """Read front matter, parts, chapters, levels (B/I/P/E), appendices."""
    result = [(book / "Master Textbook.md", "front")]
    parts = sorted(
        (p for p in book.glob("Part *") if p.is_dir()),
        key=lambda p: int(re.search(r"Part (\d+)", p.name).group(1)),
    )
    if not parts:
        raise ValueError(f"No Part folders found under {book}")

    for part in parts:
        result.append((part / "README.md", "part"))
        for chapter in sorted(p for p in part.iterdir() if p.is_dir()):
            result.append((chapter / "README.md", "chapter"))
            for level in LEVELS:
                matches = list(chapter.glob(f"*-{level} *.md"))
                if len(matches) != 1:
                    raise ValueError(f"Expected one {level} file in {chapter}; found {len(matches)}")
                result.append((matches[0], "level"))

    result.extend(
        (book / name, "backmatter")
        for name in ("Glossary.md", "Further Reading and Reference Notes.md")
    )
    for file, _ in result:
        if not file.is_file():
            raise FileNotFoundError(file)
    return result

def anchor_for(file: Path, kind: str) -> str:
    if kind == "front":
        return "master-toc"
    if kind == "part":
        return "part-" + re.search(r"Part (\d+)", file.parent.name).group(1)
    if kind == "chapter":
        return file.parent.name.split(" ", 1)[0].lower()
    if kind == "level":
        return file.name.split(" ", 1)[0].lower()
    return "glossary" if file.name == "Glossary.md" else "further-reading"

def prepare_markdown(text: str, kind: str) -> str:
    # Master TOC is enough: omit repeated mini contents menus.
    if kind == "part":
        text = re.split(r"(?m)^## Chapters\s*$", text, maxsplit=1)[0]
    elif kind == "chapter":
        text = re.split(r"(?m)^## Levels\s*$", text, maxsplit=1)[0]
    elif kind == "level":
        # Retain the existing stable anchor and one visible heading.
        text = re.sub(r"\A# T-[^\n]+\n(?:\n|\*Chapter:[^\n]*\n)*", "", text)
        text = re.sub(
            r"(?m)^#### (T-[A-Z]{3}-\d{2}-[BIPE] —)",
            r"## \1", text, count=1,
        )
    return text

def rewrite_links(fragment: str, source: Path, anchors: dict[Path, str]) -> str:
    """Make relative Markdown links navigate inside the finished PDF."""
    def replace(match: re.Match) -> str:
        original = html.unescape(match.group(1))
        parsed = urlsplit(original)
        if parsed.scheme or parsed.netloc or not parsed.path:
            return match.group(0)
        target = (source.parent / unquote(parsed.path)).resolve()
        if target not in anchors:
            return match.group(0)
        dest = parsed.fragment or anchors[target]
        return f'href="#{html.escape(unquote(dest), quote=True)}"'
    return re.sub(r'href="([^"]+)"', replace, fragment)

def build_pdf(book: Path, output: Path) -> None:
    files = collect(book)
    anchors = {path.resolve(): anchor_for(path, kind) for path, kind in files}
    markdown = mistune.create_markdown(
        escape=False, plugins=["table", "strikethrough", "url"]
    )
    chunks = []
    for path, kind in files:
        source = prepare_markdown(path.read_text(encoding="utf-8"), kind)
        rendered = rewrite_links(markdown(source), path, anchors)
        # Level files contain their own stable HTML anchor.
        tag_id = ("file-" if kind == "level" else "") + anchors[path.resolve()]
        chunks.append(
            f'<section class="{kind}" id="{tag_id}">\n{rendered}\n</section>'
        )

    document = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Software Engineering — The Master Textbook</title>"
        f"<style>{CSS}</style></head><body>"
        + "\n".join(chunks) + "</body></html>"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=document, base_url=book.as_uri() + "/").write_pdf(str(output))
    print(f"Created {output} from {len(files)} Markdown files")

def main() -> None:
    parser = argparse.ArgumentParser(description="Export PDP master textbook as PDF")
    parser.add_argument(
        "--textbook", type=Path, default=Path("5 Textbook"),
        help="Textbook folder (default: ./5 Textbook)"
    )
    parser.add_argument(
        "--output", type=Path, default=Path("Master Textbook.pdf"),
        help="Output PDF (default: ./Master Textbook.pdf)"
    )
    args = parser.parse_args()
    build_pdf(args.textbook.resolve(), args.output.resolve())

if __name__ == "__main__":
    main()
