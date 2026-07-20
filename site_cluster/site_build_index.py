#!/usr/bin/env python3
"""Keep Tekmeria index cards, JSON-LD ItemList, and sitemap in sync with posts.json."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from write_publish_gate import write_publish_gate

SITE_BASE = "https://tekmeria.eulogikon.org"
ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
POSTS_FILE = ROOT / "posts.json"
INDEX_FILE = PUBLIC / "index.html"
SITEMAP_FILE = PUBLIC / "sitemap.xml"
SKIP_HTML = frozenset(
    {
        "index.html",
        "new-post.html",
        # Drafts / alternate builds not registered in posts.json
        "_preview-aristotle.html",
    }
)

POST_CARDS_START = "<!-- tekmeria:post-cards:start -->"
POST_CARDS_END = "<!-- tekmeria:post-cards:end -->"
LDJSON_START = "<!-- tekmeria:ld+json:start -->"
LDJSON_END = "<!-- tekmeria:ld+json:end -->"


@dataclass(frozen=True)
class Post:
    """One Tekmeria essay registered for index, sitemap, and JSON-LD."""

    display_string: str
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
    display_strings: set[str] = set()
    for index, item in enumerate(posts_raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"{path}: posts[{index - 1}] must be an object")
        display_string = _require_str(item, "display_string", path, index - 1)
        if display_string in display_strings:
            raise ValueError(f"{path}: duplicate display_string {display_string!r}")
        display_strings.add(display_string)
        posts.append(
            Post(
                display_string=display_string,
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
    """Return display strings for root-level essay HTML files."""
    display_strings: set[str] = set()
    for path in PUBLIC.glob("*.html"):
        if path.name in SKIP_HTML:
            continue
        display_strings.add(path.stem)
    return display_strings


def validate_posts(posts: list[Post]) -> list[str]:
    """Return human-readable errors for manifest vs essay file mismatches."""
    errors: list[str] = []
    manifest_display_strings = {post.display_string for post in posts}
    essay_display_strings = discover_essay_files()

    for display_string in sorted(manifest_display_strings - essay_display_strings):
        errors.append(
            f"missing essay file: {display_string}.html (listed in posts.json)"
        )

    for display_string in sorted(essay_display_strings - manifest_display_strings):
        errors.append(f"missing posts.json entry for essay: {display_string}.html")

    for post in posts:
        html_path = PUBLIC / f"{post.display_string}.html"
        if not html_path.exists():
            continue
        html = html_path.read_text(encoding="utf-8")
        expected_canonical = f"{SITE_BASE}/{post.display_string}"
        canonical_match = re.search(
            r'<link rel="canonical" href="([^"]+)"',
            html,
        )
        if canonical_match is None:
            errors.append(f"{post.display_string}.html: missing canonical link")
        elif canonical_match.group(1) != expected_canonical:
            errors.append(
                f"{post.display_string}.html: canonical must be "
                f"{expected_canonical}, got {canonical_match.group(1)}"
            )
        if f'"headline": "{post.title}"' not in html and (
            f'"headline": {json.dumps(post.title)}' not in html
        ):
            errors.append(
                f"{post.display_string}.html: JSON-LD headline should match "
                "posts.json title"
            )
    return errors


def render_post_cards(posts: list[Post]) -> str:
    """Render index post-card anchors from the manifest."""
    lines: list[str] = []
    for post in posts:
        lines.extend(
            [
                f'                <a class="post-card" href="/{post.display_string}">',
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
        "name": "Tekmeria essays",
        "itemListOrder": "https://schema.org/ItemListOrderDescending",
        "numberOfItems": len(posts),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": position,
                "url": f"{SITE_BASE}/{post.display_string}",
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
            "name": "Tekmeria",
            "alternateName": "Τεκμήρια",
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
            "name": "Tekmeria",
            "alternateName": "Τεκμήρια",
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
                f"    <loc>{SITE_BASE}/{post.display_string}</loc>",
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
    gate_changed = write_publish_gate(check_only=check_only)

    if check_only and (index_changed or sitemap_changed or gate_changed):
        if index_changed:
            print(
                "error: index.html is out of sync with posts.json "
                "(run: python site_cluster/site_build_index.py)",
                file=sys.stderr,
            )
        if sitemap_changed:
            print(
                "error: sitemap.xml is out of sync with posts.json "
                "(run: python site_cluster/site_build_index.py)",
                file=sys.stderr,
            )
        if gate_changed:
            print(
                "error: publish-gate middleware is out of sync with posts.json "
                "(run: python site_cluster/site_build_index.py)",
                file=sys.stderr,
            )
        return 1

    if not check_only:
        if index_changed:
            print(f"updated {INDEX_FILE.relative_to(ROOT)}")
        if sitemap_changed:
            print(f"updated {SITEMAP_FILE.relative_to(ROOT)}")
        if gate_changed:
            print("updated public/functions/_middleware.js")
        if not index_changed and not sitemap_changed and not gate_changed:
            print("index.html, sitemap.xml, and publish gate already in sync")

    return 0


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Sync Tekmeria index cards, JSON-LD ItemList, and sitemap "
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
