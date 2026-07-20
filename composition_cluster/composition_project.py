"""Phase 7 deterministic projector for the philostorgia Tekmerion.

Renders the essay HTML for ``site_cluster/public/`` purely from the composition
store (``philostorgia.db``) and the resolved CATALOG (``philostorgia_catalog.json``).
It carries no editorial judgment: block order is the station ``seq``; each block
prints its Greek, transliteration, translation, and commentary; secondaries
print as compact inline pointers from their ``idx`` line; the sources table and
the citation list are recomputed from the store and catalog. Every decision the
projection would otherwise need already lives in the records.

Run only after ``composition_verify.py`` reports clean and the stations are
``checked``. Idempotent: rewrites the one output file each run.
"""

from __future__ import annotations

import datetime
import html
import json
import pathlib
import sqlite3

HERE = pathlib.Path(__file__).resolve().parent
DB = HERE / "philostorgia.db"
CATALOG_JSON = HERE / "philostorgia_catalog.json"
PUBLIC = HERE.parent / "site_cluster" / "public"

SITE = "https://tekmeria.eulogikon.org"
BODY_CLOSING_SECTION = "VI"

# Editorial-apparatus brackets kept faithfully in block.greek but stripped from
# the reading surface here (the store-versus-surface split; see
# prose_rules.md and references/witness-block.md).
APPARATUS_BRACKETS = "\u27e8\u27e9\u3008\u3009\u2020[]"


def strip_apparatus(greek: str) -> str:
    """Remove editorial-apparatus brackets from Greek for the reading surface.

    The store keeps them (faithful record); the reader never sees them. Only
    the bracket glyphs are removed, never the letters they enclose.
    """
    return "".join(c for c in greek if c not in APPARATUS_BRACKETS)


def _public_body_sections(con: sqlite3.Connection) -> list[str]:
    """Return body chapter numbers to project, in order, excluding the closing.

    Skips section VI and any chapter whose ``title`` is empty or null (compose-
    only scaffold: dating-trap audit, internal notes). Every extended Tekmerion
    uses the same rule; per-essay writers clear or omit public titles for
    chapters that must not reach the reader.
    """
    rows = con.execute(
        "SELECT section_no FROM chapter "
        "WHERE section_no != ? "
        "AND title IS NOT NULL AND TRIM(title) != '' "
        "ORDER BY section_no",
        (BODY_CLOSING_SECTION,),
    ).fetchall()
    if not rows:
        raise SystemExit(
            "no public body chapters: each movement needs a non-empty title, "
            "or clear compose-only chapters before projection"
        )
    return [str(r["section_no"]) for r in rows]


def esc(text: str) -> str:
    """HTML-escape text for element content or attribute values."""
    return html.escape(text or "", quote=True)


def _date_display(iso: str) -> str:
    """Render an ISO date as e.g. '19 July 2026'."""
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B')} {d.year}"


def _connect() -> sqlite3.Connection:
    """Open the store read-only with row access by name."""
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _guard_checked(con: sqlite3.Connection) -> None:
    """Refuse to project unless every station/secondary is ``checked``."""
    bad = con.execute(
        "SELECT COUNT(*) FROM station WHERE disposition IN "
        "('station','secondary') AND status != 'checked'"
    ).fetchone()[0]
    if bad:
        raise SystemExit(f"{bad} rows not 'checked'; run verify first")


def _canonical_citation(row: sqlite3.Row, work: dict[str, str]) -> str:
    """Render the one canonical citation form for a witness.

    Author, <em><a href=url>Title</a></em>, Eulogikon: wid, ref. N

    This is the only citation format on the page. A witness that cannot be
    rendered in it (missing url, title, wid, or ref) is not citable and must
    not be mentioned; the projector raises rather than emit a partial citation.
    """
    url = (work or {}).get("url")
    title = (work or {}).get("title")
    wid = row["wid"]
    ref = row["ref"]
    if not (url and title and wid and ref):
        raise SystemExit(
            f"uncitable witness unit {row['unit_id'] if 'unit_id' in row.keys() else '?'}"
            f" (wid={wid!r} ref={ref!r} title={title!r} url={url!r}); "
            "a witness that cannot be cited in the canonical form must be "
            "set aside, not projected"
        )
    return (f'{esc(row["author"])}, '
            f'<em><a href="{esc(url)}" '
            f'title="{esc(title)} ({esc(wid)})">{esc(title)}</a></em>, '
            f'Eulogikon: {esc(wid)}, ref. {esc(ref)}')


def _witness_block(row: sqlite3.Row, blk: sqlite3.Row,
                   work: dict[str, str]) -> list[str]:
    """Render one station: framing, citation, Greek block, commentary.

    The citation is the canonical form as a header line above the three
    evidence lines (Greek, transliteration, translation), then commentary.
    """
    out: list[str] = []
    if blk["framing"]:
        out.append(f'<p class="witness-framing">{esc(blk["framing"])}</p>')
    ref = f'<p class="witness-ref">{_canonical_citation(row, work)}</p>'
    out += [ref,
            f'<blockquote lang="grc" class="grc">{esc(strip_apparatus(blk["greek"]))}</blockquote>',
            f'<p class="translit"><em>{esc(blk["translit"])}</em></p>',
            f'<p class="translation">{esc(blk["translation"])}</p>',
            f'<p>{esc(blk["commentary"])}</p>']
    return out


def _secondary_line(row: sqlite3.Row, idx: sqlite3.Row,
                    work: dict[str, str]) -> str:
    """Render one secondary: English pointer, then the canonical citation.

    The sentence carries the content; the citation follows in parentheses in
    the one canonical form, wrapping the whole reference:
    ``summary (Author, <em>Title</em>, Eulogikon: wid, ref. N).``
    No bare Greek in the summary.
    """
    summary = (idx["summary"] or "").rstrip(".")
    return (f'<p class="cite">{esc(summary)} '
            f'({_canonical_citation(row, work)}).</p>')


def render_body(con: sqlite3.Connection, works: dict[str, dict[str, str]]) -> str:
    """Render the full essay body: opening, chapters, ending, sources."""
    essay_cols = {r[1] for r in con.execute("PRAGMA table_info(essay)")}
    essay_sql = "SELECT question, hinge"
    if "opening_lead" in essay_cols:
        essay_sql += ", opening_lead"
    essay = con.execute(essay_sql + " FROM essay").fetchone()
    chapters = {
        r["section_no"]: r for r in con.execute(
            "SELECT section_no, title, shows, body FROM chapter")
    }
    items = con.execute(
        "SELECT seq, section, disposition, unit_id, wid, ref, author "
        "FROM station WHERE disposition IN ('station','secondary') "
        "ORDER BY (seq IS NULL), seq"
    ).fetchall()
    block_cols = {r[1] for r in con.execute("PRAGMA table_info(block)")}
    framing_col = ", b.framing" if "framing" in block_cols else ", '' AS framing"
    blocks = {
        r["unit_id"]: r for r in con.execute(
            "SELECT s.unit_id AS unit_id, b.greek, b.translit, b.translation, "
            f"b.commentary{framing_col} FROM block b "
            "JOIN station s ON s.id = b.station_id")
    }
    idx = {
        r["unit_id"]: r for r in con.execute(
            "SELECT unit_id, key_phrase, summary FROM idx")
    }

    parts: list[str] = [f"<p>{esc(essay['question'])}</p>"]
    if essay_cols and "opening_lead" in essay_cols and essay["opening_lead"]:
        parts.append(f"<p>{esc(essay['opening_lead'])}</p>")
    parts.append(f"<p>{esc(essay['hinge'])}</p>")
    for sec in _public_body_sections(con):
        ch = chapters[sec]
        parts.append(f"<h2>{esc(ch['title'])}</h2>")
        if ch["shows"]:
            parts.append(f'<p class="chapter-lead">{esc(ch["shows"])}</p>')
        if ch["body"]:
            for para in ch["body"].split("\n\n"):
                if para.strip():
                    parts.append(f"<p>{esc(para.strip())}</p>")
        for it in [i for i in items if i["section"] == sec]:
            work = works[it["wid"]]
            if it["disposition"] == "station":
                parts += _witness_block(it, blocks[it["unit_id"]], work)
            else:
                parts.append(_secondary_line(it, idx[it["unit_id"]], work))

    closing = chapters[BODY_CLOSING_SECTION]
    parts.append(f"<h2>{esc(closing['title'])}</h2>")
    for para in (closing["body"] or "").split("\n\n"):
        if para.strip():
            parts.append(f"<p>{esc(para.strip())}</p>")

    parts.append(_sources_table(items, works))
    parts.append(
        '<p style="margin-top: 1em; font-size: 0.9em; color: #718096;">'
        "<strong>Note on Eulogikon references.</strong> Every citation takes "
        "one form: Author, <em>Title</em> (linked to the full text), "
        "Eulogikon: wid, ref. A work is keyed by its wid; the ref locates the "
        "passage within it.</p>")
    return "\n".join(parts)


def _sources_table(items: list[sqlite3.Row],
                   works: dict[str, dict[str, str]]) -> str:
    """Recompute the Sources cited table, grouped by wid in reading order."""
    order: list[str] = []
    by_wid: dict[str, dict[str, object]] = {}
    for it in items:
        wid = it["wid"]
        if wid not in by_wid:
            by_wid[wid] = {"author": it["author"], "refs": []}
            order.append(wid)
        by_wid[wid]["refs"].append(it["ref"])
    rows = []
    for wid in order:
        rec = by_wid[wid]
        work = works[wid]
        refs = ", ".join(esc(r) for r in rec["refs"])  # type: ignore[arg-type]
        rows.append(
            "<tr>"
            f'<td>{esc(str(rec["author"]))}</td>'
            f'<td><em><a href="{esc(work["url"])}">{esc(work["title"])}</a>'
            "</em></td>"
            f"<td>{esc(wid)}</td>"
            f"<td>{refs}</td>"
            "</tr>")
    return (
        '<section class="sources-cited">\n'
        "<h2>Sources cited</h2>\n"
        '<div class="table-scroll">\n'
        '<table class="summary sources">\n'
        "<thead><tr><th>Author</th><th>Title</th><th>wid</th>"
        "<th>Passages cited</th></tr></thead>\n"
        "<tbody>\n" + "\n".join(rows) + "\n</tbody>\n"
        "</table>\n</div>\n</section>")


def _jsonld(essay: sqlite3.Row, url: str,
            works: dict[str, dict[str, str]],
            wid_order: list[str]) -> str:
    """Build the BlogPosting JSON-LD block from the records and catalog."""
    data = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "@id": f"{url}#article",
        "headline": essay["title"],
        "description": essay["blurb"],
        "url": url,
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "inLanguage": "en",
        "datePublished": essay["pub_date"],
        "image": "https://eulogikon.org/assets/images/og-default.jpg",
        "author": {"@type": "Organization",
                   "@id": "https://eulogikon.org/#organization",
                   "name": "Eulogikon", "url": "https://eulogikon.org"},
        "publisher": {"@type": "Organization",
                      "@id": "https://eulogikon.org/#organization",
                      "name": "Eulogikon", "url": "https://eulogikon.org"},
        "isPartOf": {"@type": "Blog", "@id": f"{SITE}/#blog",
                     "name": "Tekmeria", "url": SITE},
        "citation": [works[w]["url"] for w in wid_order],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def render_page(con: sqlite3.Connection,
                works: dict[str, dict[str, str]]) -> tuple[str, str]:
    """Return (slug, full HTML document)."""
    essay = con.execute(
        "SELECT title, subtitle, blurb, slug, pub_date, question, hinge "
        "FROM essay"
    ).fetchone()
    slug = essay["slug"]
    url = f"{SITE}/{slug}"
    title = essay["title"]
    blurb = essay["blurb"]
    meta = (f"Τεκμήρια · Eulogikon · {_date_display(essay['pub_date'])} · "
            f"{essay['subtitle']}")
    wid_order: list[str] = []
    for r in con.execute(
        "SELECT wid FROM station WHERE disposition IN ('station','secondary') "
        "ORDER BY (seq IS NULL), seq"
    ):
        if r["wid"] not in wid_order:
            wid_order.append(r["wid"])
    body = render_body(con, works)
    jsonld = _jsonld(essay, url, works, wid_order)

    doc = _TEMPLATE.format(
        title=esc(title), blurb=esc(blurb), url=esc(url),
        canonical=esc(url), meta=esc(meta), date=esc(essay["pub_date"]),
        breadcrumb=esc(title), jsonld=jsonld, body=body)
    return slug, doc


_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} · Tekmeria</title>
    <meta name="description" content="{blurb}">
    <meta name="robots" content="index, follow">
    <meta name="ai-train" content="yes">
    <link rel="canonical" href="{canonical}">

    <!-- Open Graph -->
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="Tekmeria · Eulogikon">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{blurb}">
    <meta property="og:url" content="{url}">
    <meta property="og:image" content="https://eulogikon.org/assets/images/og-default.jpg">
    <meta property="og:image:alt" content="Tekmeria: essays from the Eulogikon ancient Greek corpus">
    <meta property="og:image:type" content="image/jpeg">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:locale" content="en">
    <meta property="article:published_time" content="{date}">

    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{blurb}">
    <meta name="twitter:image" content="https://eulogikon.org/assets/images/og-default.jpg">
    <meta name="twitter:image:alt" content="Tekmeria: essays from the Eulogikon ancient Greek corpus">

    <!-- Favicon -->
    <link rel="icon" href="https://eulogikon.org/favicon.ico" sizes="48x48">
    <link rel="icon" type="image/svg+xml" href="https://eulogikon.org/favicon.svg">
    <link rel="icon" type="image/png" sizes="32x32" href="https://eulogikon.org/icons/favicon-32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="https://eulogikon.org/icons/favicon-16.png">
    <link rel="apple-touch-icon" sizes="180x180" href="https://eulogikon.org/apple-touch-icon.png">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro:ital,wght@0,300;0,400;0,600;1,300;1,400;1,600&display=swap">

    <link rel="stylesheet" href="/assets/eulogikon-base.css">
    <link rel="stylesheet" href="/assets/tekmeria.css">

    <script type="application/ld+json">
{jsonld}
    </script>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-content">
            <button class="hamburger-menu-toggle" onclick="toggleHamburgerMenu()" aria-label="Toggle navigation menu" aria-expanded="false" aria-controls="hamburger-menu-panel">
                <span class="hamburger-line"></span>
                <span class="hamburger-line"></span>
                <span class="hamburger-line"></span>
            </button>
            <div class="nav-center">
                <a href="/" class="home-link"><span>Τεκμήρια</span></a>
                <div class="navbar-subtitle">Eulogikon · Essays from the corpus</div>
            </div>
            <div class="nav-tabs desktop-only">
                <a href="/" class="nav-tab">Essays</a>
                <a href="https://eulogikon.org/" class="nav-tab">Library</a>
                <a href="https://eulogikon.org/index_alphabetic" class="nav-tab">Authors</a>
                <a href="https://eulogikon.org/contact" class="nav-tab">Contact</a>
            </div>
            <div class="hamburger-menu-overlay" onclick="toggleHamburgerMenu()"></div>
            <div class="hamburger-menu-panel" id="hamburger-menu-panel" role="navigation">
                <div class="menu-section menu-navigation">
                    <h3 class="menu-section-title">Navigation</h3>
                    <a href="/" class="menu-link">Essays</a>
                    <a href="https://eulogikon.org/" class="menu-link">Library</a>
                    <a href="https://eulogikon.org/index_alphabetic" class="menu-link">Authors</a>
                    <a href="https://eulogikon.org/contact" class="menu-link">Contact</a>
                </div>
            </div>
        </div>
    </nav>

    <div class="breadcrumbs">
        <a href="/">Tekmeria</a> <span class="breadcrumb-separator">›</span> <span class="breadcrumb-current">{breadcrumb}</span>
    </div>

    <main>
    <div class="container">
        <div class="content-wrapper">
            <article class="tekmeria-essay">
                <header class="post-header">
                    <h1>{title}</h1>
                    <div class="post-meta">{meta}</div>
                </header>

{body}

            </article>
        </div>
    </div>
    </main>

    <div class="footer">
        <p><strong>Τεκμήρια</strong> · Essays from <a href="https://eulogikon.org" style="color: inherit;">Eulogikon</a></p>
        <p style="margin-top: 6px; font-size: 0.9em; opacity: 0.8;">
            Greek source texts are public domain. Essay text is <a href="https://creativecommons.org/publicdomain/zero/1.0/" style="color: inherit; text-decoration: underline;">CC0 1.0</a>.
        </p>
        <nav style="margin-top: 16px; display: flex; flex-wrap: wrap; justify-content: center; gap: 8px 20px; font-size: 0.9em;">
            <a href="/" style="color: white; text-decoration: none;">Essays</a>
            <a href="https://eulogikon.org/" style="color: white; text-decoration: none;">Library</a>
            <a href="https://eulogikon.org/index_alphabetic" style="color: white; text-decoration: none;">Authors A-Z</a>
            <a href="https://eulogikon.org/contact" style="color: white; text-decoration: none;">Contact</a>
        </nav>
    </div>

    <script>
        function toggleHamburgerMenu() {{
            const button = document.querySelector('.hamburger-menu-toggle');
            const panel = document.getElementById('hamburger-menu-panel');
            const overlay = document.querySelector('.hamburger-menu-overlay');
            button.classList.toggle('active');
            panel.classList.toggle('open');
            overlay.classList.toggle('visible');
        }}
        document.addEventListener('DOMContentLoaded', function() {{
            const overlay = document.querySelector('.hamburger-menu-overlay');
            if (overlay) {{ overlay.addEventListener('click', toggleHamburgerMenu); }}
        }});
    </script>
</body>
</html>
"""


def main() -> None:
    """Project the store to the served HTML file."""
    if not DB.exists():
        raise SystemExit(f"{DB} missing")
    catalog = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
    works = catalog["works"]
    con = _connect()
    try:
        _guard_checked(con)
        slug, doc = render_page(con, works)
    finally:
        con.close()
    out = PUBLIC / f"{slug}.html"
    out.write_text(doc, encoding="utf-8")
    print(f"projected {out.relative_to(HERE.parent)} ({len(doc)} bytes)")


if __name__ == "__main__":
    main()
