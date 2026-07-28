#!/usr/bin/env python3
"""Generate site/index.html from links.json, characters.json, and materials/.

Run:  python3 build.py
"""

import html
import json
from pathlib import Path

ROOT = Path(__file__).parent
MATERIALS = ROOT / "materials"
OUT = ROOT / "site" / "index.html"
LINKS = ROOT / "links.json"
CHARACTERS = ROOT / "characters.json"

SKIP = {".DS_Store", "Thumbs.db", ".gitkeep"}

KIND_BY_EXT = {
    ".pdf": "PDF", ".doc": "DOC", ".docx": "DOC", ".txt": "TXT", ".rtf": "DOC",
    ".jpg": "IMG", ".jpeg": "IMG", ".png": "IMG", ".gif": "IMG", ".heic": "IMG",
    ".mp3": "AUDIO", ".m4a": "AUDIO", ".wav": "AUDIO",
    ".mp4": "VIDEO", ".mov": "VIDEO",
    ".zip": "ZIP", ".csv": "CSV", ".xlsx": "XLS",
}


def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def scan_materials(exclude_dirs=()):
    """{section: [file_info]} for materials/, skipping excluded top-level folders."""
    if not MATERIALS.exists():
        return {}
    sections = {}
    for path in sorted(MATERIALS.rglob("*")):
        if not path.is_file() or path.name in SKIP or path.name.startswith("."):
            continue
        rel = path.relative_to(MATERIALS)
        if rel.parts[0] in exclude_dirs or (len(rel.parts) > 1 and rel.parts[1] in exclude_dirs):
            continue
        group = rel.parts[1] if len(rel.parts) > 2 else (rel.parts[0] if len(rel.parts) > 1 else "")
        sections.setdefault(group, []).append({
            "name": path.stem.replace("_", " ").replace("-", " "),
            "href": "/" + "/".join(rel.parts),
            "kind": KIND_BY_EXT.get(path.suffix.lower(), path.suffix.lstrip(".").upper() or "FILE"),
            "size": human_size(path.stat().st_size),
        })
    return sections


def render_character(c):
    name = html.escape(c["name"])
    aka = f' <span class="aka">&ldquo;{html.escape(c["aka"])}&rdquo;</span>' if c.get("aka") else ""
    relation = f'<span class="relation">{html.escape(c["relation"])}</span>' if c.get("relation") else ""
    # Linked once a page exists; until then the card is inert.
    if c.get("status") == "ready":
        return f"""      <li><a href="/characters/{html.escape(c['slug'])}.html">
        <span class="cname">{name}{aka}</span>{relation}
      </a></li>"""
    return f"""      <li class="inert">
        <span class="cname">{name}{aka}</span>{relation}
        <span class="soon">background pending</span>
      </li>"""


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
    cfg = load(LINKS, {})
    chars = load(CHARACTERS, {})
    site = cfg.get("site", {})
    title = site.get("title", "Materials")
    blocks = []

    # Carousel of group portraits; first entry is what loads by default.
    slides = cfg.get("carousel", [])
    if not slides and site.get("hero"):
        slides = [{"src": site["hero"], "caption": site.get("hero_caption", "")}]
    if slides:
        figures = "\n".join(
            f'      <figure>\n'
            f'        <img src="{html.escape(s["src"])}" alt="{html.escape(s.get("caption") or title)}"'
            f'{"" if i == 0 else " loading=lazy"}>\n'
            + (f'        <figcaption>{html.escape(s["caption"])}</figcaption>\n' if s.get("caption") else "")
            + "      </figure>"
            for i, s in enumerate(slides)
        )
        dots = "\n".join(
            f'      <button class="dot{" on" if i == 0 else ""}" data-i="{i}" '
            f'aria-label="Photo {i + 1} of {len(slides)}"></button>'
            for i in range(len(slides))
        )
        nav = ""
        if len(slides) > 1:
            nav = (
                '    <button class="arrow prev" aria-label="Previous photo">&lsaquo;</button>\n'
                '    <button class="arrow next" aria-label="Next photo">&rsaquo;</button>\n'
                f'    <div class="dots">\n{dots}\n    </div>\n'
            )
        blocks.append(
            f'  <section class="carousel" aria-roledescription="carousel">\n'
            f'    <div class="track">\n{figures}\n    </div>\n{nav}  </section>'
        )

    # Characters.
    people = chars.get("characters", [])
    if people:
        note = chars.get("note")
        blocks.append(
            f'  <section>\n    <h2>{html.escape(chars.get("heading", "The Characters"))}</h2>\n'
            + (f'    <p class="note">{html.escape(note)}</p>\n' if note else "")
            + '    <ul class="chars">\n'
            + "\n".join(render_character(c) for c in people)
            + "\n    </ul>\n  </section>"
        )

    # External links.
    for section in cfg.get("sections", []):
        items = [render_link(l["title"], l["url"], l.get("description"), badge="LINK")
                 for l in section.get("links", [])]
        if not items:
            continue
        note = section.get("note")
        blocks.append(
            f'  <section>\n    <h2>{html.escape(section["heading"])}</h2>\n'
            + (f'    <p class="note">{html.escape(note)}</p>\n' if note else "")
            + "    <ul>\n" + "\n".join(items) + "\n    </ul>\n  </section>"
        )

    # Files, excluding the group shots already shown as the hero.
    mat_cfg = cfg.get("materials", {})
    found = scan_materials(exclude_dirs=tuple(mat_cfg.get("exclude", [])))
    if found:
        blocks.append(f'  <section>\n    <h2>{html.escape(mat_cfg.get("heading", "Files"))}</h2>')
        labels = mat_cfg.get("folder_labels", {})
        for group in sorted(found):
            label = labels.get(group, group.replace("_", " ").replace("-", " ").title() or "General")
            blocks.append(
                f'    <h3>{html.escape(label)}</h3>\n    <ul>\n'
                + "\n".join(render_link(f["name"], f["href"], None, badge=f["kind"], meta=f["size"])
                            for f in found[group])
                + "\n    </ul>"
            )
        blocks.append("  </section>")

    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
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
  header {{ border-bottom: 1px solid var(--line); padding-bottom: 1.5rem; margin-bottom: 2rem; }}
  h1 {{ font-size: clamp(1.9rem, 5vw, 2.6rem); margin: 0 0 .4rem; letter-spacing: -.01em; }}
  .tagline {{ color: var(--muted); margin: 0; font-size: 1.05rem; }}
  h2 {{ font-size: 1.3rem; margin: 2.5rem 0 .3rem; }}
  h3 {{
    font-size: .8rem; text-transform: uppercase; letter-spacing: .09em;
    color: var(--muted); margin: 1.75rem 0 .6rem; font-family: ui-sans-serif, system-ui, sans-serif;
  }}
  .note {{ color: var(--muted); margin: 0 0 1rem; font-size: .95rem; }}
  .carousel {{ position: relative; margin: 0 0 1.5rem; }}
  .carousel .track {{
    display: flex; overflow-x: auto; scroll-snap-type: x mandatory;
    scroll-behavior: smooth; scrollbar-width: none; gap: 0;
  }}
  .carousel .track::-webkit-scrollbar {{ display: none; }}
  .carousel figure {{ flex: 0 0 100%; margin: 0; scroll-snap-align: center; }}
  .carousel img {{
    width: 100%; height: auto; display: block;
    border-radius: 10px; border: 1px solid var(--line);
  }}
  .carousel figcaption {{
    color: var(--muted); font-size: .88rem; margin-top: .6rem; text-align: center;
  }}
  .arrow {{
    position: absolute; top: 40%; transform: translateY(-50%);
    width: 2.4rem; height: 2.4rem; border-radius: 50%; cursor: pointer;
    border: 1px solid var(--line); background: var(--card); color: var(--fg);
    font-size: 1.4rem; line-height: 1; display: grid; place-items: center;
    opacity: .85; transition: opacity .15s;
  }}
  .arrow:hover {{ opacity: 1; }}
  .arrow.prev {{ left: .6rem; }}
  .arrow.next {{ right: .6rem; }}
  .dots {{ display: flex; justify-content: center; gap: .4rem; margin-top: .7rem; }}
  .dot {{
    width: .5rem; height: .5rem; padding: 0; border-radius: 50%; cursor: pointer;
    border: 1px solid var(--muted); background: transparent;
  }}
  .dot.on {{ background: var(--accent); border-color: var(--accent); }}
  @media (prefers-reduced-motion: reduce) {{ .carousel .track {{ scroll-behavior: auto; }} }}
  ul {{ list-style: none; padding: 0; margin: 0; }}
  li + li {{ margin-top: .5rem; }}
  li a, li.inert {{
    display: block; padding: .85rem 1rem; background: var(--card);
    border: 1px solid var(--line); border-radius: 8px;
    text-decoration: none; color: inherit;
  }}
  li a {{ transition: border-color .15s, transform .15s; }}
  li a:hover {{ border-color: var(--accent); transform: translateY(-1px); }}
  li a:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
  li.inert {{ opacity: .72; }}
  .chars .cname {{ font-weight: 600; }}
  .aka {{ font-weight: 400; color: var(--muted); }}
  .relation {{
    margin-left: .55rem; font-size: .74rem; letter-spacing: .05em; text-transform: uppercase;
    color: var(--muted); font-family: ui-sans-serif, system-ui, sans-serif;
  }}
  .soon {{
    float: right; font-size: .74rem; color: var(--muted);
    font-family: ui-sans-serif, system-ui, sans-serif;
  }}
  .row {{ display: flex; align-items: baseline; gap: .6rem; flex-wrap: wrap; }}
  .title {{ font-weight: 600; }}
  .badge {{
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: .62rem; letter-spacing: .06em; padding: .2rem .4rem;
    border: 1px solid var(--line); border-radius: 4px; color: var(--muted); flex-shrink: 0;
  }}
  .meta {{ margin-left: auto; color: var(--muted); font-size: .8rem; font-variant-numeric: tabular-nums; }}
  .desc {{ margin: .35rem 0 0; color: var(--muted); font-size: .92rem; }}
  footer {{
    margin-top: 3.5rem; padding-top: 1.5rem; border-top: 1px solid var(--line);
    color: var(--muted); font-size: .88rem;
  }}
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
<script>
(function () {{
  var c = document.querySelector('.carousel');
  if (!c) return;
  var track = c.querySelector('.track');
  var dots = [].slice.call(c.querySelectorAll('.dot'));
  var slides = [].slice.call(c.querySelectorAll('figure'));
  if (slides.length < 2) return;

  function go(i) {{
    i = Math.max(0, Math.min(slides.length - 1, i));
    track.scrollTo({{ left: slides[i].offsetLeft - track.offsetLeft, behavior: 'smooth' }});
  }}
  function current() {{
    return Math.round(track.scrollLeft / track.clientWidth);
  }}
  c.querySelector('.prev').addEventListener('click', function () {{ go(current() - 1); }});
  c.querySelector('.next').addEventListener('click', function () {{ go(current() + 1); }});
  dots.forEach(function (d) {{
    d.addEventListener('click', function () {{ go(+d.dataset.i); }});
  }});

  var tick;
  track.addEventListener('scroll', function () {{
    clearTimeout(tick);
    tick = setTimeout(function () {{
      var i = current();
      dots.forEach(function (d, n) {{ d.classList.toggle('on', n === i); }});
    }}, 60);
  }});

  c.tabIndex = 0;
  c.addEventListener('keydown', function (e) {{
    if (e.key === 'ArrowLeft') {{ e.preventDefault(); go(current() - 1); }}
    if (e.key === 'ArrowRight') {{ e.preventDefault(); go(current() + 1); }}
  }});
}})();
</script>
</body>
</html>
"""
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(doc)
    n_files = sum(len(v) for v in found.values())
    print(f"Wrote {OUT.relative_to(ROOT)} — {len(people)} character(s), {n_files} file(s).")


if __name__ == "__main__":
    main()
