#!/usr/bin/env python3
"""Keep Semeia index cards, JSON-LD ItemList, and sitemap in sync with posts.json."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SITE_BASE = "https://semeia.eulogikon.org"
ROOT = Path(__file__).resolve().parent.parent
POSTS_FILE = ROOT / "posts.json"
INDEX_FILE = ROOT / "index.html"
SITEMAP_FILE = ROOT / "sitemap.xml"
SKIP_HTML = frozenset({"index.html", "new-post.html"})

POST_CARDS_START = "<!-- semeia:post-cards:start -->"
POST_CARDS_END = "<!-- semeia:post-cards:end -->"
LDJSON_START = "<!-- semeia:ld+json:start -->"
LDJSON_END = "<!-- semeia:ld+json:end -->"


@dataclass(frozen=True)
class Post:
    """One Semeia essay registered for index, sitemap, and JSON-LD."""

    slug: str
    title: str
    date: str
    date_display: str
    blurb: str


def load_posts(path: Path = POSTS_FILE) -> list[Post]:
    """Load and validate the posts manifest."""
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    posts_raw = raw.get("posts")
    if not isinstance(posts_raw, list) or not posts_raw:
        raise ValueError(f"{path}: 'posts' must be a non-empty array")

    posts: list[Post] = []
    slugs: set[str] = set()
    for index, item in enumerate(posts_raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"{path}: posts[{index - 1}] must be an object")
        slug = _require_str(item, "slug", path, index - 1)
        if slug in slugs:
            raise ValueError(f"{path}: duplicate slug {slug!r}")
        slugs.add(slug)
        posts.append(
            Post(
                slug=slug,
                title=_require_str(item, "title", path, index - 1),
                date=_require_str(item, "date", path, index - 1),
                date_display=_require_str(item, "date_display", path, index - 1),
                blurb=_require_str(item, "blurb", path, index - 1),
            )
        )
    return posts


def _require_str(item: dict[str, Any], key: str, path: Path, index: int) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}: posts[{index}].{key} must be a non-empty string")
    return value.strip()


def discover_essay_files() -> set[str]:
    """Return slugs for root-level essay HTML files."""
    slugs: set[str] = set()
    for path in ROOT.glob("*.html"):
        if path.name in SKIP_HTML:
            continue
        slugs.add(path.stem)
    return slugs


def validate_posts(posts: list[Post]) -> list[str]:
    """Return human-readable errors for manifest vs essay file mismatches."""
    errors: list[str] = []
    manifest_slugs = {post.slug for post in posts}
    essay_slugs = discover_essay_files()

    for slug in sorted(manifest_slugs - essay_slugs):
        errors.append(f"missing essay file: {slug}.html (listed in posts.json)")

    for slug in sorted(essay_slugs - manifest_slugs):
        errors.append(f"missing posts.json entry for essay: {slug}.html")

    for post in posts:
        html_path = ROOT / f"{post.slug}.html"
        if not html_path.exists():
            continue
        html = html_path.read_text(encoding="utf-8")
        expected_canonical = f"{SITE_BASE}/{post.slug}"
        canonical_match = re.search(
            r'<link rel="canonical" href="([^"]+)"',
            html,
        )
        if canonical_match is None:
            errors.append(f"{post.slug}.html: missing canonical link")
        elif canonical_match.group(1) != expected_canonical:
            errors.append(
                f"{post.slug}.html: canonical must be {expected_canonical}, "
                f"got {canonical_match.group(1)}"
            )
        if f'"headline": "{post.title}"' not in html and (
            f'"headline": {json.dumps(post.title)}' not in html
        ):
            errors.append(
                f"{post.slug}.html: JSON-LD headline should match posts.json title"
            )
    return errors


def render_post_cards(posts: list[Post]) -> str:
    """Render index post-card anchors from the manifest."""
    lines: list[str] = []
    for post in posts:
        lines.extend(
            [
                f'                <a class="post-card" href="/{post.slug}">',
                f'                    <div class="post-card-date">{post.date_display}</div>',
                f"                    <h2>{post.title}</h2>",
                f"                    <p>{post.blurb}</p>",
                "                </a>",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def render_itemlist_object(posts: list[Post]) -> dict[str, Any]:
    """Build the schema.org ItemList object for the index page."""
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "@id": f"{SITE_BASE}/#posts",
        "name": "Semeia essays",
        "itemListOrder": "https://schema.org/ItemListOrderDescending",
        "numberOfItems": len(posts),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": position,
                "url": f"{SITE_BASE}/{post.slug}",
                "name": post.title,
            }
            for position, post in enumerate(posts, start=1)
        ],
    }


def render_index_ldjson(posts: list[Post]) -> str:
    """Render the full index JSON-LD script block."""
    graph: list[dict[str, Any]] = [
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "@id": f"{SITE_BASE}/#website",
            "name": "Semeia",
            "alternateName": "Σημεῖα",
            "url": SITE_BASE,
            "description": (
                "Short essays reading the ancient Greek corpus closely, with the "
                "original text and its commentators, from Eulogikon."
            ),
            "inLanguage": "en",
            "publisher": {
                "@type": "Organization",
                "@id": "https://eulogikon.org/#organization",
                "name": "Eulogikon",
                "url": "https://eulogikon.org",
            },
            "isPartOf": {
                "@type": "WebSite",
                "@id": "https://eulogikon.org/#website",
                "name": "Eulogikon",
                "url": "https://eulogikon.org",
            },
        },
        {
            "@context": "https://schema.org",
            "@type": "Blog",
            "@id": f"{SITE_BASE}/#blog",
            "name": "Semeia",
            "alternateName": "Σημεῖα",
            "url": SITE_BASE,
            "description": (
                "Short essays reading the Eulogikon ancient Greek corpus closely: "
                "the original text, its commentators, and what the words actually "
                "meant."
            ),
            "inLanguage": "en",
            "publisher": {
                "@type": "Organization",
                "@id": "https://eulogikon.org/#organization",
                "name": "Eulogikon",
                "url": "https://eulogikon.org",
            },
            "isPartOf": {"@id": f"{SITE_BASE}/#website"},
        },
        render_itemlist_object(posts),
    ]
    payload = json.dumps(graph, ensure_ascii=False, indent=2)
    return '    <script type="application/ld+json">\n' f"{payload}\n" "    </script>"


def render_sitemap(posts: list[Post]) -> str:
    """Render sitemap.xml from the manifest."""
    homepage_lastmod = max(post.date for post in posts)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        "  <url>",
        f"    <loc>{SITE_BASE}/</loc>",
        f"    <lastmod>{homepage_lastmod}</lastmod>",
        "    <changefreq>weekly</changefreq>",
        "    <priority>1.0</priority>",
        "  </url>",
    ]
    for post in posts:
        lines.extend(
            [
                "  <url>",
                f"    <loc>{SITE_BASE}/{post.slug}</loc>",
                f"    <lastmod>{post.date}</lastmod>",
                "    <changefreq>monthly</changefreq>",
                "    <priority>0.8</priority>",
                "  </url>",
            ]
        )
    lines.append("</urlset>")
    lines.append("")
    return "\n".join(lines)


def replace_between_markers(
    content: str,
    start_marker: str,
    end_marker: str,
    replacement: str,
) -> str:
    """Replace content between HTML comment markers, keeping the markers."""
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    if not pattern.search(content):
        raise ValueError(f"missing markers: {start_marker} … {end_marker}")
    wrapped = f"{start_marker}\n{replacement}\n{end_marker}"
    return pattern.sub(wrapped, content, count=1)


def sync_index(posts: list[Post], content: str) -> str:
    """Apply manifest-driven blocks to index.html."""
    updated = replace_between_markers(
        content,
        POST_CARDS_START,
        POST_CARDS_END,
        render_post_cards(posts),
    )
    return replace_between_markers(
        updated,
        LDJSON_START,
        LDJSON_END,
        render_index_ldjson(posts).strip(),
    )


def write_if_changed(path: Path, content: str, check_only: bool) -> bool:
    """Write content when it differs from disk; return True if a write is needed."""
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if current == content:
        return False
    if check_only:
        return True
    path.write_text(content, encoding="utf-8")
    return False


def run_sync(check_only: bool) -> int:
    """Sync or verify index.html and sitemap.xml against posts.json."""
    posts = load_posts()
    validation_errors = validate_posts(posts)
    if validation_errors:
        for error in validation_errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    index_content = sync_index(posts, INDEX_FILE.read_text(encoding="utf-8"))
    sitemap_content = render_sitemap(posts)

    index_changed = write_if_changed(INDEX_FILE, index_content, check_only)
    sitemap_changed = write_if_changed(SITEMAP_FILE, sitemap_content, check_only)

    if check_only and (index_changed or sitemap_changed):
        if index_changed:
            print(
                "error: index.html is out of sync with posts.json "
                "(run: python scripts/sync_semeia_site.py)",
                file=sys.stderr,
            )
        if sitemap_changed:
            print(
                "error: sitemap.xml is out of sync with posts.json "
                "(run: python scripts/sync_semeia_site.py)",
                file=sys.stderr,
            )
        return 1

    if not check_only:
        if index_changed:
            print(f"updated {INDEX_FILE.relative_to(ROOT)}")
        if sitemap_changed:
            print(f"updated {SITEMAP_FILE.relative_to(ROOT)}")
        if not index_changed and not sitemap_changed:
            print("index.html and sitemap.xml already in sync")

    return 0


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Sync Semeia index cards, JSON-LD ItemList, and sitemap "
        "from posts.json.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with an error if generated files differ from posts.json.",
    )
    args = parser.parse_args()
    return run_sync(check_only=args.check)


if __name__ == "__main__":
    sys.exit(main())
