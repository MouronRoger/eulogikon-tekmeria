# Semeia · `semeia.eulogikon.org`

Σημεῖα ("signs, marks"): short essays that read the [Eulogikon](https://eulogikon.org)
ancient-Greek corpus closely: the original text, its commentators, and what the
words actually meant. A standalone static site, deliberately decoupled from the
eulogikon corpus pipeline (no database, no generators, no build step).

## Style

**No em dashes (U+2014).** Repunctuate with colons, commas, parentheses, or middle
dots (·) instead. Examples:

| Instead of | Use |
|---|---|
| `Semeia — Eulogikon` | `Semeia · Eulogikon` |
| `Semeia — Essays from…` | `Semeia: Essays from…` |
| `two things — X — and Y` | `two things (X) and Y` |
| `The question is — what…` | `The question is: what…` |
| `earlier thinkers — the Pythagoreans — had` | `earlier thinkers (the Pythagoreans) had` |

En dashes (U+2013) in reference ranges (e.g. `1078b17–31`, `740–741`) are fine.

## Layout

```
semeia/
├── posts.json        # essay registry (single source of truth for index + sitemap)
├── scripts/
│   └── sync_semeia_site.py   # sync/check index cards, ItemList, sitemap from posts.json
├── index.html        # landing page (post cards + ItemList generated from posts.json)
├── new-post.html     # blank skeleton: copy this to start a new essay
├── <post-name>.html  # one file per essay; the filename IS the URL (/<post-name>)
└── assets/
    ├── eulogikon-base.css   # the main site's chrome + typography, lifted verbatim
    └── semeia.css           # essay-specific styling (Greek quotes, citations, tables)
```

## Add a post

1. `cp new-post.html my-essay-name.html` (the filename becomes the URL path).
2. Fill in every `<!-- TODO -->`: title, description, canonical, Open Graph,
   JSON-LD, and the article body. The skeleton documents the content patterns
   (Greek quote + translation + citation, summary table, caveats box).
3. **Link corpus citations the correct way:** resolve identity → URL, never
   hand-guess a slug. From the eulogikon repo:
   ```bash
   EULOGIKON_STRICT_DB=1 venv/bin/python -c \
     "from src.core.url_composer import canonical_work_url; print(canonical_work_url('hgw-bj'))"
   # -> https://eulogikon.org/works/aristotle-metaphysics-hgw-bj
   ```
   `eul_wid` is the stable reference key; the display-string prefix is just a
   mutable attribute. Composing from the DB guarantees the link is live and
   correct even if a display string later changes.
4. **Register the post** in `posts.json` (slug, title, date, date_display,
   blurb). Newest first in the array.
5. **Sync derived files** (index post cards, JSON-LD `ItemList`, `sitemap.xml`):
   ```bash
   python scripts/sync_semeia_site.py
   ```
6. **Verify before commit** (also runs in GitHub Actions on every push/PR):
   ```bash
   python scripts/sync_semeia_site.py --check
   ```

The sync script reads `posts.json` as the single registry. It rewrites the
marked blocks in `index.html` and regenerates `sitemap.xml`. CI fails if you
forget step 5, so `numberOfItems`, sitemap entries, and index cards cannot
drift apart again.

## Preview

```bash
npx wrangler pages dev .     # production-faithful: serves /my-essay-name without .html
```

(Plain `python3 -m http.server` works too, but won't do extensionless URLs;
visit the `.html` form locally in that case.)

## Deploy

Production deploys **automatically on push to `main`**. The Cloudflare Pages
project `eulogikon-semeia` is connected to this GitHub repo; custom domain
`semeia.eulogikon.org` is already configured.

To redeploy manually (rare):

```bash
npx wrangler pages deploy . --project-name=eulogikon-semeia
```

## Note on the chrome

`assets/eulogikon-base.css` and the navbar/footer markup are a **lifted copy** of
the main eulogikon site's chrome (`src/core/site_chrome.py` + a rendered work
page's `<style>` block). They do not auto-track changes to the main site; this
is the accepted per-surface duplication trade (see the eulogikon
`multilingual_sites/deployment/PLAN.md`: shared assets are duplicated across
sibling repos rather than cross-referenced). The navbar/footer **links** are
rewritten to absolute `https://eulogikon.org/...` because relative paths would
resolve against this subdomain and 404.
