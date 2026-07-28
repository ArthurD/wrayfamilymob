#!/usr/bin/env python3
"""Generate site/index.html from links.json and whatever is in materials/.

Drop files into materials/ (subfolders become sections), edit links.json for
external links, then run:  python3 build.py
"""

import html
import json
import os
from pathlib import Path

ROOT = Path(__file__).parent
MATERIALS = ROOT / "materials"
OUT = ROOT / "site" / "index.html"
CONFIG = ROOT / "links.json"

# Files we never publish, even if they land in materials/ by accident.
SKIP = {".DS_Store", "Thumbs.db", ".gitkeep"}

KIND_BY_EXT = {
    ".pdf": "PDF", ".doc": "DOC", ".docx": "DOC", ".txt": "TXT", ".rtf": "DOC",
    ".jpg": "IMG", ".jpeg": "IMG", ".png": "IMG", ".gif": "IMG", ".heic": "IMG",
    ".mp3": "AUDIO", ".m4a": "AUDIO", ".wav": "AUDIO",
    ".mp4": "VIDEO", ".mov": "VIDEO",
    ".zip": "ZIP", ".csv": "CSV", ".xlsx": "XLS",
}


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def scan_materials():
    """Return {section_label: [file_info, ...]} for everything under materials/."""
    if not MATERIALS.exists():
        return {}
    sections = {}
    for path in sorted(MATERIALS.rglob("*")):
        if not path.is_file() or path.name in SKIP or path.name.startswith("."):
            continue
        rel = path.relative_to(MATERIALS)
        # Top-level folder is the section; loose files go under "Files".
        group = rel.parts[0] if len(rel.parts) > 1 else ""
        sections.setdefault(group, []).append({
            "name": path.stem.replace("_", " ").replace("-", " "),
            "href": "/".join(rel.parts),
            "kind": KIND_BY_EXT.get(path.suffix.lower(), path.suffix.lstrip(".").upper() or "FILE"),
            "size": human_size(path.stat().st_size),
        })
    return sections


def render_link(title, href, description, badge=None, meta=None):
    badge_html = f'<span class="badge">{html.escape(badge)}</span>' if badge else ""
    meta_html = f'<span class="meta">{html.escape(meta)}</span>' if meta else ""
    desc_html = f'<p class="desc">{html.escape(description)}</p>' if description else ""
    return f"""      <li>
        <a href="{html.escape(href)}">
          <span class="row">{badge_html}<span class="title">{html.escape(title)}</span>{meta_html}</span>
          {desc_html}
        </a>
      </li>"""


def main():
    cfg = json.loads(CONFIG.read_text())
    site = cfg.get("site", {})
    title = site.get("title", "Materials")
    blocks = []

    # External link sections, in the order they appear in links.json.
    for section in cfg.get("sections", []):
        items = [
            render_link(l["title"], l["url"], l.get("description"), badge="LINK")
            for l in section.get("links", [])
        ]
        if not items:
            continue
        note = section.get("note")
        blocks.append(
            f'  <section>\n    <h2>{html.escape(section["heading"])}</h2>\n'
            + (f'    <p class="note">{html.escape(note)}</p>\n' if note else "")
            + "    <ul>\n" + "\n".join(items) + "\n    </ul>\n  </section>"
        )

    # Uploaded materials, grouped by folder.
    mat_cfg = cfg.get("materials", {})
    labels = mat_cfg.get("folder_labels", {})
    found = scan_materials()
    if found:
        heading = mat_cfg.get("heading", "Files")
        note = mat_cfg.get("note")
        blocks.append(
            f'  <section>\n    <h2>{html.escape(heading)}</h2>\n'
            + (f'    <p class="note">{html.escape(note)}</p>\n' if note else "")
        )
        for group in sorted(found):
            label = labels.get(group, group.replace("_", " ").replace("-", " ").title() or "General")
            items = [
                render_link(f["name"], f["href"], None, badge=f["kind"], meta=f["size"])
                for f in found[group]
            ]
            blocks.append(
                f'    <h3>{html.escape(label)}</h3>\n    <ul>\n' + "\n".join(items) + "\n    </ul>"
            )
        blocks.append("  </section>")
    else:
        blocks.append(
            '  <section>\n    <p class="empty">No files yet. Drop them into the '
            "<code>materials/</code> folder and rebuild.</p>\n  </section>"
        )

    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
  :root {{
    --bg: #fbfaf8; --fg: #1b1a17; --muted: #6b6862;
    --line: #e2ded6; --card: #fff; --accent: #7a5c3e;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #161513; --fg: #ece9e3; --muted: #97928a;
      --line: #2e2c28; --card: #1e1d1a; --accent: #c8a279;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--bg); color: var(--fg);
    font: 16px/1.6 ui-serif, Georgia, "Times New Roman", serif;
    -webkit-text-size-adjust: 100%;
  }}
  .wrap {{ max-width: 46rem; margin: 0 auto; padding: 3rem 1.25rem 4rem; }}
  header {{ border-bottom: 1px solid var(--line); padding-bottom: 1.5rem; margin-bottom: 2.5rem; }}
  h1 {{ font-size: clamp(1.9rem, 5vw, 2.6rem); margin: 0 0 .4rem; letter-spacing: -.01em; }}
  .tagline {{ color: var(--muted); margin: 0; font-size: 1.05rem; }}
  h2 {{ font-size: 1.3rem; margin: 2.5rem 0 .3rem; }}
  h3 {{
    font-size: .8rem; text-transform: uppercase; letter-spacing: .09em;
    color: var(--muted); margin: 1.75rem 0 .6rem; font-family: ui-sans-serif, system-ui, sans-serif;
  }}
  .note, .empty {{ color: var(--muted); margin: 0 0 1rem; font-size: .95rem; }}
  .empty {{ padding: 1.5rem; border: 1px dashed var(--line); border-radius: 8px; text-align: center; }}
  ul {{ list-style: none; padding: 0; margin: 0; }}
  li + li {{ margin-top: .5rem; }}
  li a {{
    display: block; padding: .85rem 1rem; background: var(--card);
    border: 1px solid var(--line); border-radius: 8px;
    text-decoration: none; color: inherit; transition: border-color .15s, transform .15s;
  }}
  li a:hover {{ border-color: var(--accent); transform: translateY(-1px); }}
  li a:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
  .row {{ display: flex; align-items: baseline; gap: .6rem; flex-wrap: wrap; }}
  .title {{ font-weight: 600; }}
  .badge {{
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: .62rem; letter-spacing: .06em; padding: .2rem .4rem;
    border: 1px solid var(--line); border-radius: 4px; color: var(--muted);
    flex-shrink: 0;
  }}
  .meta {{ margin-left: auto; color: var(--muted); font-size: .8rem; font-variant-numeric: tabular-nums; }}
  .desc {{ margin: .35rem 0 0; color: var(--muted); font-size: .92rem; }}
  footer {{
    margin-top: 3.5rem; padding-top: 1.5rem; border-top: 1px solid var(--line);
    color: var(--muted); font-size: .88rem;
  }}
  code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .88em; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>{html.escape(title)}</h1>
    <p class="tagline">{html.escape(site.get("tagline", ""))}</p>
  </header>
{chr(10).join(blocks)}
  <footer>{html.escape(site.get("footer", ""))}</footer>
</div>
</body>
</html>
"""
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(doc)
    n_files = sum(len(v) for v in found.values())
    n_links = sum(len(s.get("links", [])) for s in cfg.get("sections", []))
    print(f"Wrote {OUT.relative_to(ROOT)} — {n_links} external link(s), {n_files} file(s).")


if __name__ == "__main__":
    main()
