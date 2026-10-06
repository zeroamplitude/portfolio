<!-- Updated: 2026-10-06 -->
# Ground rules

Facts to apply and myths to avoid. If this file is more than six months old,
check the dated claims against Google Search Central before relying on them.

## Current Google facts

- **Core Web Vitals** are LCP, INP and CLS, judged at the 75th percentile of
  real Chrome users (field data, 28 days):

  | Metric | Good | Needs improvement | Poor |
  |---|---|---|---|
  | LCP (largest contentful paint) | ≤ 2.5 s | 2.5–4 s | > 4 s |
  | INP (interaction to next paint) | ≤ 200 ms | 200–500 ms | > 500 ms |
  | CLS (cumulative layout shift) | ≤ 0.1 | 0.1–0.25 | > 0.25 |

  INP replaced FID in March 2024; never mention FID. A low-traffic site often
  has no field data, so Google falls back to origin-level or no data. Lab
  numbers (Lighthouse) are diagnostics, not the ranking signal.
- **Mobile-first indexing** is universal: Google indexes the 390px-wide
  layout, so content hidden on mobile is content Google may not weigh.
- **Structured data**: JSON-LD only. FAQ rich results are limited to
  authoritative government and health sites, and HowTo rich results are
  gone, so don't add either. Markup must describe content visible on the page.
- **Titles**: Google shows roughly 600px (≈ 50–60 characters) and rewrites
  titles that are vague, stuffed or don't match the page. The `<h1>` and
  title should agree.
- **Meta descriptions** aren't a ranking factor but drive clicks; Google
  often substitutes a page excerpt when the description doesn't match the query.
- **Canonical**: one per page, absolute, self-referencing. If Google picks a
  different canonical (`gsc.py inspect` shows it), fix internal links and
  redirects rather than fighting it.
- **Sitemaps** help discovery; `lastmod` should only change when the page's
  content does (the hook handles this).

## Myths: don't recommend these

- Word-count minimums ("500 words for a homepage"). Length isn't a ranking
  factor; a portfolio should be as long as the substance needs.
- Keyword density, meta keywords tag, exact-match keyword stuffing.
- An overall "SEO score out of 100" as a goal.
- Building backlinks by buying or exchanging them.
- Changing URLs for keywords. Moving pages costs more than it gains.

## What helps a personal site rank

- **Clear entity signals**: the same name, role and description everywhere:
  the home page, Person structured data, LinkedIn, GitHub and Digistax/Vowbird
  bylines. `sameAs` links tie them together.
- **Experience shown, not claimed** (Google's E-E-A-T: experience, expertise,
  authoritativeness, trust): concrete outcomes with numbers, named employers,
  real screenshots, a case study written first-hand. Never fabricate metrics.
- **Specific titles and descriptions** that match how people search: his
  name, "Digistax", "AI agents", "solution engineer Toronto".
- **Fast, stable pages**: correctly sized images, eager-loaded hero images,
  width/height on images that aren't sized by CSS.
- **Links in from his own profiles** (LinkedIn, GitHub, company sites where
  appropriate) and from talks, articles or directories that mention him.

## Site-specific constraints (see CLAUDE.md)

- Content Security Policy: no inline scripts or `style=""`; JSON-LD is fine.
- The owner's email and the resume's contact details never appear on the site.
- Vowbird.ai and Digistax are independent companies; no "built by" links on their sites.
- GitHub Pages serves the site: no server redirects or custom headers. An
  old URL can only be redirected with a static page carrying
  `<meta http-equiv="refresh">` plus a canonical, or by moving DNS behind a
  Cloudflare proxy (ask first).
