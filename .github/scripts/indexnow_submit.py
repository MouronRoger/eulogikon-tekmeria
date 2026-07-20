#!/usr/bin/env python3
"""Submit Tekmeria page URLs to IndexNow.

Maps served HTML to ``https://tekmeria.eulogikon.org/…`` and POSTs batches
to ``api.indexnow.org``. Accepts either layout:

* repo-root HTML (current production deploy root)
* ``site_cluster/public/`` HTML (clustered layout)

Modes:
  * git-diff: ``--base`` / ``--head`` for changed HTML in a push
  * sitemap: ``--from-sitemap`` for every URL in ``sitemap.xml``

IndexNow covers Bing, Yandex, Seznam, and Naver (not Google). Bing's signal
also feeds DuckDuckGo and ChatGPT search.

Environment:
    INDEXNOW_KEY   required unless ``--dry-run`` (32-char hex key string)

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
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable
from urllib import error as urllib_error
from urllib import request as urllib_request

API_URL = "https://api.indexnow.org/indexnow"
BATCH_SIZE = 9000
DEFAULT_HOST = "tekmeria.eulogikon.org"
PUBLIC_PREFIXES = ("site_cluster/public/", "public/")
SKIP_HTML_NAMES = frozenset({"new-post.html"})
REPO_ROOT = Path(__file__).resolve().parents[2]
SITEMAP_CANDIDATES = (
    REPO_ROOT / "site_cluster" / "public" / "sitemap.xml",
    REPO_ROOT / "sitemap.xml",
)
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def git_changed_paths(base: str, head: str) -> list[str]:
    """Return paths that were Added, Modified, Copied, or Renamed.

    Deleted files are skipped: IndexNow will discover 404s on recrawl, and
    submitting dead URLs can hurt the host's IndexNow reputation.
    """
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


def _is_served_html(path: str) -> bool:
    """Return True if ``path`` is a live essay/index HTML file."""
    if not path.endswith(".html"):
        return False
    name = Path(path).name
    if name in SKIP_HTML_NAMES or name.startswith("_"):
        return False
    if path.startswith("site_cluster/public/"):
        # Only the public root, not nested drafts elsewhere under site_cluster.
        rel = path[len("site_cluster/public/") :]
        return "/" not in rel.rstrip("/")
    if path.startswith("composition_cluster/") or path.startswith("tests/"):
        return False
    if "/" in path:
        # Nested non-public paths are not served URLs.
        return False
    return True


def html_paths(paths: Iterable[str]) -> list[str]:
    """Keep HTML pages that map to live Tekmeria URLs."""
    return [path for path in paths if _is_served_html(path)]


def path_to_url(path: str, host: str) -> str:
    """Map a repo-relative public HTML path to its canonical URL."""
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            path = path[len(prefix) :]
            break

    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    elif path == "index.html":
        path = ""
    elif path.endswith(".html"):
        path = path[: -len(".html")]
    return f"https://{host}/{path}"


def default_sitemap() -> Path:
    """Return the first existing sitemap among known layout locations."""
    for candidate in SITEMAP_CANDIDATES:
        if candidate.is_file():
            return candidate
    return SITEMAP_CANDIDATES[0]


def urls_from_sitemap(sitemap: Path, host: str) -> list[str]:
    """Load absolute URLs from the site sitemap, scoped to ``host``."""
    if not sitemap.is_file():
        raise FileNotFoundError(f"sitemap not found: {sitemap}")
    root = ET.parse(sitemap).getroot()
    host_root = f"https://{host}"
    expected_prefix = f"{host_root}/"
    urls: list[str] = []
    seen: set[str] = set()
    for loc in root.findall("sm:url/sm:loc", SITEMAP_NS):
        text = (loc.text or "").strip()
        if text.rstrip("/") == host_root:
            text = f"{host_root}/"
        elif not text.startswith(expected_prefix):
            continue
        if text in seen:
            continue
        seen.add(text)
        urls.append(text)
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
    """CLI entry: resolve URLs, optionally POST them to IndexNow."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--from-sitemap",
        action="store_true",
        help="submit every URL listed in the sitemap",
    )
    mode.add_argument("--base", help="previous commit SHA (git-diff mode)")
    parser.add_argument("--head", help="current commit SHA (required with --base)")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument(
        "--sitemap",
        type=Path,
        default=None,
        help="path to sitemap.xml (with --from-sitemap)",
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

    urls: list[str]
    if args.from_sitemap:
        sitemap = args.sitemap if args.sitemap is not None else default_sitemap()
        try:
            urls = urls_from_sitemap(sitemap, args.host)
        except (OSError, ET.ParseError) as exc:
            print(f"error reading sitemap: {exc}", file=sys.stderr)
            return 1
    else:
        assert args.base is not None and args.head is not None
        try:
            changed = git_changed_paths(args.base, args.head)
        except subprocess.CalledProcessError as exc:
            print(f"git diff failed: {exc.stderr}", file=sys.stderr)
            return 1
        pages = html_paths(changed)
        urls = [path_to_url(path, args.host) for path in pages]

    if not urls:
        print("no URLs to submit")
        return 0

    print(f"found {len(urls)} URL(s)")
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
