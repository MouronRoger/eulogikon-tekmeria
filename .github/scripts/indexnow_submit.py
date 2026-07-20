#!/usr/bin/env python3
"""Submit published Tekmeria essay URLs to IndexNow.

Only URLs registered in ``posts.json`` are ever submitted. The index page,
assets, drafts, scripts, and every other path are ignored.

Modes:
  * ``--all-posts``: every registered published post
  * ``--base`` / ``--head``: registered posts whose HTML changed in the range

IndexNow covers Bing, Yandex, Seznam, and Naver (not Google).

Environment:
    INDEXNOW_KEY   required unless ``--dry-run``

Exit codes:
    0  success (or nothing to submit, or dry-run)
    1  bad input / git failure
    2  IndexNow API rejected a batch
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable
from urllib import error as urllib_error
from urllib import request as urllib_request

API_URL = "https://api.indexnow.org/indexnow"
BATCH_SIZE = 9000
DEFAULT_HOST = "tekmeria.eulogikon.org"
REPO_ROOT = Path(__file__).resolve().parents[2]
POSTS_CANDIDATES = (
    REPO_ROOT / "site_cluster" / "posts.json",
    REPO_ROOT / "posts.json",
)
PUBLIC_HTML_PREFIXES = (
    "site_cluster/public/",
    "public/",
    "",
)


def load_published_display_strings(posts_path: Path) -> list[str]:
    """Return ordered display strings for published posts from ``posts.json``."""
    raw: object = json.loads(posts_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{posts_path}: root must be a JSON object")
    posts_raw = raw.get("posts")
    if not isinstance(posts_raw, list) or not posts_raw:
        raise ValueError(f"{posts_path}: 'posts' must be a non-empty array")

    display_strings: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(posts_raw):
        if not isinstance(item, dict):
            raise ValueError(f"{posts_path}: posts[{index}] must be an object")
        value = item.get("display_string")
        if value is None:
            value = item.get("slug")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{posts_path}: posts[{index}] needs display_string or slug"
            )
        display_string = value.strip()
        if display_string in seen:
            continue
        seen.add(display_string)
        display_strings.append(display_string)
    return display_strings


def default_posts_path() -> Path:
    """Return the first existing posts.json among known layout locations."""
    for candidate in POSTS_CANDIDATES:
        if candidate.is_file():
            return candidate
    return POSTS_CANDIDATES[0]


def post_url(display_string: str, host: str) -> str:
    """Build the canonical public URL for one published post."""
    return f"https://{host}/{display_string}"


def published_urls(display_strings: list[str], host: str) -> list[str]:
    """Map every registered post to its canonical URL."""
    return [post_url(display_string, host) for display_string in display_strings]


def git_changed_paths(base: str, head: str) -> list[str]:
    """Return paths that were Added, Modified, Copied, or Renamed."""
    result = subprocess.run(
        ["git", "diff", "--name-status", "--no-renames", base, head],
        check=True,
        capture_output=True,
        text=True,
    )
    changed: list[str] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0][0]
        if status not in {"A", "M", "C", "R"}:
            continue
        changed.append(parts[-1])
    return changed


def path_to_display_string(path: str) -> str | None:
    """Return a post display_string if ``path`` is that post's public HTML."""
    if not path.endswith(".html"):
        return None
    for prefix in PUBLIC_HTML_PREFIXES:
        if prefix and not path.startswith(prefix):
            continue
        rel = path[len(prefix) :] if prefix else path
        if "/" in rel:
            return None
        name = Path(rel).name
        if name in {"index.html", "new-post.html"} or name.startswith("_"):
            return None
        if name.endswith(".html"):
            return name[: -len(".html")]
    return None


def changed_published_urls(
    changed_paths: Iterable[str],
    published: set[str],
    host: str,
) -> list[str]:
    """Intersect changed HTML paths with the published-post registry."""
    urls: list[str] = []
    seen: set[str] = set()
    for path in changed_paths:
        display_string = path_to_display_string(path)
        if display_string is None or display_string not in published:
            continue
        url = post_url(display_string, host)
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls


def chunked(items: list[str], size: int) -> Iterable[list[str]]:
    """Yield successive slices of ``items`` with length at most ``size``."""
    for i in range(0, len(items), size):
        yield items[i : i + size]


def submit_batch(host: str, key: str, urls: list[str]) -> tuple[int, str]:
    """POST one IndexNow batch; return ``(status_code, response_body)``."""
    body = json.dumps(
        {
            "host": host,
            "key": key,
            "keyLocation": f"https://{host}/{key}.txt",
            "urlList": urls,
        }
    ).encode("utf-8")
    req = urllib_request.Request(
        API_URL,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib_error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def main() -> int:
    """CLI entry: resolve published-post URLs, optionally POST to IndexNow."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--all-posts",
        action="store_true",
        help="submit every published post from posts.json",
    )
    mode.add_argument("--base", help="previous commit SHA (git-diff mode)")
    parser.add_argument("--head", help="current commit SHA (required with --base)")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument(
        "--posts",
        type=Path,
        default=None,
        help="path to posts.json (default: site_cluster/posts.json or posts.json)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.base and not args.head:
        print("error: --head is required with --base", file=sys.stderr)
        return 1

    key = os.environ.get("INDEXNOW_KEY", "").strip()
    if not key and not args.dry_run:
        print("error: INDEXNOW_KEY env var not set", file=sys.stderr)
        return 1

    posts_path = args.posts if args.posts is not None else default_posts_path()
    try:
        display_strings = load_published_display_strings(posts_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error reading posts registry: {exc}", file=sys.stderr)
        return 1

    published = set(display_strings)
    urls: list[str]
    if args.all_posts:
        urls = published_urls(display_strings, args.host)
    else:
        assert args.base is not None and args.head is not None
        try:
            changed = git_changed_paths(args.base, args.head)
        except subprocess.CalledProcessError as exc:
            print(f"git diff failed: {exc.stderr}", file=sys.stderr)
            return 1
        urls = changed_published_urls(changed, published, args.host)

    if not urls:
        print("no published posts to submit")
        return 0

    print(f"submitting {len(urls)} published post URL(s) from {posts_path}")
    for url in urls[:20]:
        print(f"  {url}")
    if len(urls) > 20:
        print(f"  … and {len(urls) - 20} more")

    if args.dry_run:
        print("dry-run: not submitting")
        return 0

    failed = 0
    for batch in chunked(urls, BATCH_SIZE):
        status, body = submit_batch(args.host, key, batch)
        if 200 <= status < 300:
            print(f"submitted batch of {len(batch)}: HTTP {status}")
        else:
            failed += len(batch)
            print(
                f"batch of {len(batch)} rejected: HTTP {status} {body!r}",
                file=sys.stderr,
            )

    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
