# CLAUDE.md — portfolio (nicholasdesouza.com)

Context for Claude sessions working in this repo. This repo is **public**: never add secrets,
credential values, phone numbers or personal email addresses here or anywhere in the repo.

## What this is

Nicholas De Souza's personal portfolio, live at https://nicholasdesouza.com. Plain static
HTML/CSS/JS in `site/` (no build step, no framework). Built from a Claude Design handoff.

- `site/index.html` — home: hero, career highlights, Now building (Vowbird.ai, Digistax), Past work, Resume, contact
- `site/case-study.html` — Digistax case study
- `site/gallery.html` — screenshot gallery
- `site/styles.css`, `site/main.js` — all styles and behaviour (mobile menu, contact form modal, carousels, click-to-enlarge lightbox)
- `site/assets/` — images (screenshots are WebP; logos PNG; `og/` link-preview JPEGs), resume PDF
- `site/robots.txt` (blocks only the resume PDF; all search and AI crawlers are allowed by choice), `site/sitemap.xml`, `site/404.html`
- `site/home.html` — fallback redirect stub for `/home` (Cloudflare 301s it while proxied); instant meta refresh + canonical to `/`. Keep it out of the sitemap
- `site/llms.txt` — Markdown summary for AI assistants; regenerate with the SEO skill's `llms_txt.py`, then hand-edit
- `site/0f1689ce29c9b84210c0f147231fdff8.txt` — IndexNow key file (public by design; keep it)

Preview locally: `cd site && python3 -m http.server`.

## Deploying

- Pushing to `main` deploys via `.github/workflows/pages.yml` (GitHub Pages, custom domain, DNS on Cloudflare).
- The workflow runs `tools/page_markdown.py`, which writes a Markdown copy of each indexable page (`site/<page>.md`, home is `index.md`) and `site/llms-full.txt`. They're gitignored; the SEO hook also generates them locally so converter failures show up before deploy.
- The workflow rewrites `?v=dev` on `styles.css`/`main.js` URLs to the commit SHA (cache busting). Keep `?v=dev` in the HTML.
- After deploying, the workflow notifies IndexNow (Bing, Yandex, …) with every URL in `sitemap.xml`. **When adding a page, add it to `sitemap.xml`.**
- Actions are pinned to commit SHAs; update by resolving the new tag's SHA.

## Conventions and constraints

- **Content Security Policy** (meta tag in every page's `<head>`): only self, Google Fonts, and Formspree. No inline scripts, no inline `style=""` attributes — put styles in `styles.css`. JSON-LD (`application/ld+json`) is fine. Pages with the "Copy page" menu also allow `connect-src 'self'` (it fetches the page's `.md`).
- **"Copy page" menu** (home and case study; built by `main.js` from `<div class="copy-page" data-copy-page>`, add `copy-page-end` to right-align its menu): copy the page as Markdown, view the `.md`, open `llms-full.txt`, or open the page in Claude or ChatGPT. Add it to new text-heavy pages, not the gallery.
- Match the existing design: dark theme, Geist / Geist Mono, lime accent `oklch(0.87 0.17 128)`. Mobile breakpoint is 760px; mobile content is **left-aligned** (centring was tried and reverted).
- Home page has Person structured data, canonical URLs and Open Graph tags on each page — keep them in sync if titles/pages change.
- Contact form posts to Formspree `https://formspree.io/f/xgavyroa` (in `main.js`). Don't enable Formspree reCAPTCHA (breaks the AJAX submit). The owner's email must never appear on the site.
- The resume PDF contains contact details; it's deliberately not indexed (robots.txt + `rel="nofollow"`). Don't put its contact details into page text.
- Vowbird.ai and Digistax should stay presented as independent companies; no "built by" links on their sites.
- An SEO hook (`.claude/hooks/seo-check.py`, wired in `.claude/settings.json`) runs before every `git commit` Claude makes. It updates and stages `sitemap.xml` (missing pages, `lastmod` for changed pages) and `og:image` sizes, and blocks the commit on missing titles, descriptions, canonical/Open Graph tags, `<h1>` count, image alt text, invalid JSON-LD or broken local links. Run it by hand with `python3 .claude/hooks/seo-check.py --run`.
- The **SEO skill** (`.claude/skills/seo/`) covers audits, Search Console (`scripts/gsc.py`), titles and descriptions, structured data, AI crawlers and adding pages. Audit reports go to the gitignored `.seo-reports/`. Never add a named `User-agent` group to robots.txt without repeating the resume `Disallow` (see `references/ai-search.md`).
- Make each logical change its own commit (the owner likes being able to revert pieces). Verify in a headless browser (Chromium is at `/opt/pw-browsers/chromium`) at desktop and 390px widths before pushing.

## Infrastructure (no secrets)

- **DNS (Cloudflare):** GitHub Pages A `185.199.108–111.153`, AAAA `2606:50c0:8000–8003::153`, CNAME `www → zeroamplitude.github.io`. These 9 records are **Proxied** (orange cloud, since 2026-10-06) so Cloudflare can add headers and redirects; everything else is DNS only.
- **Cloudflare proxy settings:** SSL/TLS mode **Full** (not strict: GitHub may fail to renew its origin certificate behind the proxy, and strict would then take the site down), Always Use HTTPS on, HSTS `max-age=15552000` with nosniff (no includeSubDomains, no preload). Transform Rule "noindex Markdown copies and llms files" sends `X-Robots-Tag: noindex` for `*.md`, `/llms.txt` and `/llms-full.txt`. Single Redirect "Old /home URL to the home page" 301s `/home` and `/home/` to `/` (`site/home.html` stays as the fallback if the proxy is turned off). Bot Fight Mode and AI-bot blocking are off on purpose. DNSSEC is active. GitHub's Pages settings may warn about DNS while proxied; that's expected. To undo, set the 9 records back to DNS only. Two Google verification TXT records on `@` (`google-site-verification=PtAcwamV…` and `…=RmSxY-b-…`) — must stay. **No email on this domain:** SPF `v=spf1 -all`, DMARC `p=reject`, null MX. Don't restore old Google Workspace MX or `googlehosted.com` CNAMEs.
- **Search Console:** Domain property `sc-domain:nicholasdesouza.com`, verified via DNS; sitemap submitted.
- **Bing Webmaster Tools:** site imported from Search Console; IndexNow enabled via the deploy workflow.

## API access (only in the "Profile" cloud environment)

Sessions in the **Profile** environment have API credentials injected by the agent proxy — call the APIs
without auth headers and never print or log credential values:

- Cloudflare (Bearer) → `api.cloudflare.com`, nicholasdesouza.com zone only: Zone read, DNS edit, Zone Settings edit, SSL and Certificates read, Transform Rules edit, Single Redirect edit, Cache Rules edit, Cache Purge, Analytics read, Bot Management read
- Google Search Console (GCP service-account token) → `searchconsole.googleapis.com`

There is no Bing Webmaster API access: Bing's API needs the key in the URL query string, which the
environment's credential types can't inject. Bing gets URLs via IndexNow (deploy workflow); use the
Bing Webmaster Tools dashboard for reports.

Always show proposed DNS changes and get approval before creating, changing or deleting records.

## Open items (owner to do)

- GitHub: verify the domain in account Settings → Pages; ensure 2FA is on.
- Check Bing's IndexNow page shows received URLs; check Search Console Performance in 2–4 weeks.
