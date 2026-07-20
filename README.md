# Tekmeria · `tekmeria.eulogikon.org`

Τεκμήρια ("evidence tokens"): short essays that read the
[Eulogikon](https://eulogikon.org) ancient-Greek corpus closely: the original
text, its commentators, and what the words actually meant. A standalone static
site, deliberately decoupled from the eulogikon corpus pipeline (no database,
no generators, no build step).

## Style

Mechanical formatting (Greek in English, witness blocks, citations, punctuation,
titles/meta): [`STYLE.md`](STYLE.md) § **Formatting cross-check**.

**No em dashes (U+2014).** Repunctuate with colons, commas, parentheses, or middle
dots (·) instead. Examples:

| Instead of | Use |
|---|---|
| `Tekmeria — Eulogikon` | `Tekmeria · Eulogikon` |
| `Tekmeria — Essays from…` | `Tekmeria: Essays from…` |
| `two things — X — and Y` | `two things (X) and Y` |
| `The question is — what…` | `The question is: what…` |
| `earlier thinkers — the Pythagoreans — had` | `earlier thinkers (the Pythagoreans) had` |

En dashes (U+2013) in reference ranges (e.g. `1078b17–31`, `740–741`) are fine.

## Layout

Two clusters (functional homes; see `governance_cluster/functional_concern_homes.yaml`):
`site_cluster/` generates the site, `composition_cluster/` composes long-form
Tekmeria. The static host serves `site_cluster/public/` (pinned in
`wrangler.toml`), so path still equals URL and no address changed.

```
eulogikon-semeia/
├── wrangler.toml               # Cloudflare Pages: output dir = site_cluster/public
├── site_cluster/               # site generation (machinery; not served)
│   ├── posts.json              # essay registry (single source for index + sitemap)
│   ├── site_build_index.py     # sync/check index cards, ItemList, sitemap from posts.json
│   ├── new-post.html           # blank skeleton: copy into public/ to start an essay
│   └── public/                 # the served site root (what Cloudflare Pages serves)
│       ├── index.html          # landing page (cards + ItemList generated from posts.json)
│       ├── <post-name>.html    # one file per essay; the filename IS the URL (/<post-name>)
│       ├── sitemap.xml  robots.txt  _redirects  BingSiteAuth.xml
│       ├── <indexnow-key>.txt  # IndexNow ownership key (host-specific)
│       ├── functions/          # Cloudflare Pages Functions (_middleware.js)
│       └── assets/
│           ├── eulogikon-base.css   # the main site's chrome + typography, lifted verbatim
│           └── tekmeria.css         # essay-specific styling (Greek quotes, citations, tables)
├── composition_cluster/        # long-form Tekmeria engine (store, builder, drafts; *.db gitignored)
├── docs/  CHARTERS.md          # governance, capability charters, concern homes
└── .claude/skills/tekmerion/   # the extended-Tekmerion procedure
```

## Add a post

1. `cp site_cluster/new-post.html site_cluster/public/my-essay-name.html` (the
   filename becomes the URL path).
2. Fill in every `<!-- TODO -->`: title, description, canonical, Open Graph,
   JSON-LD, and the article body. The skeleton documents the content patterns
   (Greek quote + translation + citation, summary table, caveats box).
3. **Link corpus citations the correct way:** resolve identity → URL, never
   hand-guess a display string. From the eulogikon repo:
   ```bash
   EULOGIKON_STRICT_DB=1 venv/bin/python -c \
     "from src.core.url_composer import canonical_work_url; print(canonical_work_url('hgw-bj'))"
   # -> https://eulogikon.org/works/aristotle-metaphysics-hgw-bj
   ```
   `eul_wid` is the stable reference key; the display-string prefix is just a
   mutable attribute. Composing from the DB guarantees the link is live and
   correct even if a display string later changes.
4. **Register the post** in `site_cluster/posts.json` (display_string, title,
   date, date_display, blurb). The `display_string` is the essay's URL path and
   filename stem. Newest first in the array.
5. **Sync derived files** (index post cards, JSON-LD `ItemList`, `sitemap.xml`):
   ```bash
   python site_cluster/site_build_index.py
   ```
6. **Verify before commit** (also runs in GitHub Actions on every push/PR):
   ```bash
   python site_cluster/site_build_index.py --check
   ```

The sync script reads `site_cluster/posts.json` as the single registry. It
rewrites the marked blocks in `site_cluster/public/index.html` and regenerates
`site_cluster/public/sitemap.xml`. CI fails if you forget step 5, so
`numberOfItems`, sitemap entries, and index cards cannot drift apart again.

## Preview

```bash
npx wrangler pages dev site_cluster/public   # production-faithful: serves /my-essay-name without .html
```

(Plain `python3 -m http.server` works too, but won't do extensionless URLs;
visit the `.html` form locally in that case.)

## Deploy

Production deploys **automatically on push to `main`**. The Cloudflare Pages
project `eulogikon-tekmeria` is connected to this GitHub repo; custom domain
`tekmeria.eulogikon.org` is already configured.

The output directory is `site_cluster/public`, pinned in `wrangler.toml`, so
the served root is that directory (not the repo root) and every published
address is unchanged. To redeploy manually (rare):

```bash
npx wrangler pages deploy site_cluster/public --project-name=eulogikon-tekmeria
```

## IndexNow

Tekmeria has its **own** IndexNow key (hosted on this host). Do not reuse the
eulogikon.org key: IndexNow matches key file to submitted host.

- Key file: `site_cluster/public/<key>.txt` (must be live at
  `https://tekmeria.eulogikon.org/<key>.txt`)
- Repo secret: `INDEXNOW_KEY` (same string as the file body)
- Opt-in on push: include `[indexnow]` in the commit message on `main`
  (submits only changed **published posts** from `posts.json`)
- Full resubmit: Actions → **indexnow** → Run workflow
  (submits every registered published post; never the index, assets, or drafts)

Dry-run locally:

```bash
INDEXNOW_KEY=dummy python .github/scripts/indexnow_submit.py --all-posts --dry-run
```

## Note on the chrome

`site_cluster/public/assets/eulogikon-base.css` and the navbar/footer markup are a **lifted copy** of
the main eulogikon site's chrome (`src/core/site_chrome.py` + a rendered work
page's `<style>` block). They do not auto-track changes to the main site; this
is the accepted per-surface duplication trade (see the eulogikon
`multilingual_sites/deployment/PLAN.md`: shared assets are duplicated across
sibling repos rather than cross-referenced). The navbar/footer **links** are
rewritten to absolute `https://eulogikon.org/...` because relative paths would
resolve against this subdomain and 404.
