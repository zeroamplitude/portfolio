---
name: seo
description: >
  SEO for nicholasdesouza.com: audits, search performance, metadata writing,
  structured data, AI search (robots.txt crawlers, llms.txt) and adding pages.
  Use when asked to "check SEO", "run an SEO audit", "how is the site doing in
  Google/Search Console", "improve the title/description", "add a page",
  "structured data/schema", "AI crawlers", "llms.txt", "Core Web Vitals", or
  when a commit is blocked or warned by the SEO hook.
---

# SEO skill for nicholasdesouza.com

A personal portfolio: three indexable pages (`index.html`, `case-study.html`,
`gallery.html`) plus `404.html`, static HTML in `site/`. The goal is to rank
for Nicholas's name and what he does (AI agents, solution engineering,
Digistax, Vowbird.ai), and to be described accurately by AI assistants.

## Division of labour

- **The hook** (`.claude/hooks/seo-check.py`) runs before every commit. It
  fixes the sitemap and og:image sizes, and blocks commits on mechanical
  problems. Don't duplicate its checks; run it with `--run` for its report.
- **This skill** handles anything that needs the network, judgement or writing.
  Propose changes before making them. Each change is its own commit (see CLAUDE.md).

## Scripts

All in `scripts/`, Python stdlib only. Each takes `--json`. Run from the repo root.

| Script | What it does | Needs |
|---|---|---|
| `live_check.py [URL or file ...]` | Redirects, status, headers, title/description/canonical/OG/h1, schema types, word count. No args: every sitemap URL plus http/www variants | Network access to the site (files work offline) |
| `robots_ai.py [--live]` | Which search and AI crawlers may fetch which paths | Nothing (`--live` needs network) |
| `gsc.py performance / sitemaps / inspect` | Search Console clicks, impressions, CTR and position; sitemap status; Google's index verdict and chosen canonical per URL | Search Console credentials from the environment proxy |
| `pagespeed.py [URL]` | Core Web Vitals (field) and Lighthouse lab metrics | `PSI_API_KEY`, or luck with the keyless quota |
| `external_links.py` | Every outbound link still resolves | Network |
| `llms_txt.py [--write]` | Drafts `site/llms.txt` from the pages and Person JSON-LD | Nothing |

When a script reports `limited` or exits with "environment limitation", that is
this environment (network allowlist, missing credentials, rate limit), **not**
a site problem. Say so, mark the affected findings `Hypothesis`, and carry on.
Don't retry more than once. In cloud sessions the live site is usually blocked;
`gsc.py inspect` shows Google's view of the live pages instead.

## Findings format

Every finding carries evidence and a confidence label:

- **Confirmed**: seen directly in a file, script output or API response.
- **Likely**: strong inference from confirmed facts.
- **Hypothesis**: plausible but unverified (often because a check was `limited`).

Severity: 🔴 critical (hurts indexing or ranking now), ⚠️ warning (worth fixing),
ℹ️ info. Order fixes by impact over effort. Never inflate: a three-page site
does not need a score out of 100.

## Workflows

### 1. Audit ("check SEO", "run an SEO audit")

1. `python3 .claude/hooks/seo-check.py --run`
2. `live_check.py site/*.html`, then `live_check.py` (live; may be `limited`)
3. `robots_ai.py`, `gsc.py sitemaps`, `gsc.py inspect`, `gsc.py performance --by query` and `--by page`
4. `pagespeed.py` (mobile), `external_links.py`
5. Read each page yourself and judge, using `references/rules.md`: does the
   copy say plainly who Nicholas is and what each project does? Are titles and
   descriptions specific (`references/metadata.md`)? Does structured data match
   the visible content (`references/schema.md`)?
6. Write `.seo-reports/<date>-audit.md` (gitignored; the repo is public):
   summary, findings table (finding, evidence, severity, confidence, fix), then
   an action plan. Tell the user the path and the top three actions.

### 2. Search performance ("how is the site doing")

`gsc.py performance` by query, page and date (try `--days 90`), plus `gsc.py inspect`.
Report what people search for, which pages earn impressions, and
position/CTR outliers: a query ranking 5–15 with low CTR means the title or
description isn't compelling. Search Console lags 2–3 days, and a new site
has sparse data for weeks. Bing has no API here; point to Bing Webmaster Tools.

### 3. Titles and descriptions

Follow `references/metadata.md`. Show the current and proposed text with
character counts. Update `og:title`/`og:description` (and the Person
`description` when the home page changes) in the same commit.

### 4. Adding a page

1. Copy the `<head>` of an existing page: CSP meta, title, description,
   canonical, the OG/Twitter set, favicon links, `?v=dev` assets.
2. Make a 1200×630 link-preview JPEG in `site/assets/og/`. The case study's
   was rendered from an SVG in Chromium; give it a new filename, not a reused one.
3. Add structured data if a type fits (`references/schema.md`).
4. Link to it from the nav (desktop and mobile menus) and any related page.
5. Commit. The hook adds the page to `sitemap.xml`. Then re-run `llms_txt.py`
   and review the diff.
6. After deploy, `gsc.py inspect <url>`. IndexNow pings Bing automatically.

### 5. Structured data

Follow `references/schema.md`. JSON-LD only, it must match visible text, and
re-validate with the hook. After deploy, `gsc.py inspect` lists detected rich results.

### 6. AI search

Policy and crawler list: `references/ai-search.md`. Check with `robots_ai.py`.
Regenerate `llms.txt` with `llms_txt.py`, then hand-edit for accuracy.

### 7. After a deploy

`live_check.py` (if the network allows), `gsc.py inspect` for changed pages,
`robots_ai.py --live`.

## Hard rules

- Never add contact details (email, phone, the resume's contents) to pages,
  structured data, `llms.txt` or reports. The resume stays disallowed in robots.txt.
- Never print or log credentials; the proxy injects them.
- Vowbird.ai and Digistax are presented as independent companies.
- Show proposed DNS changes and get approval before touching Cloudflare.
- Keep `references/` current: each file has an `Updated:` date. If one is over
  six months old, check its claims before relying on them.

Approach adapted from [Agentic-SEO-Skill](https://github.com/Bhanunamikaze/Agentic-SEO-Skill)
(MIT, Bhanu Namikaze); the scripts and references here were written for this site.
