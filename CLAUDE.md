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
- `site/robots.txt` (blocks only the resume PDF), `site/sitemap.xml`, `site/404.html`
- `site/0f1689ce29c9b84210c0f147231fdff8.txt` — IndexNow key file (public by design; keep it)

Preview locally: `cd site && python3 -m http.server`.

## Deploying

- Pushing to `main` deploys via `.github/workflows/pages.yml` (GitHub Pages, custom domain, DNS on Cloudflare).
- The workflow rewrites `?v=dev` on `styles.css`/`main.js` URLs to the commit SHA (cache busting). Keep `?v=dev` in the HTML.
- After deploying, the workflow notifies IndexNow (Bing, Yandex, …) with every URL in `sitemap.xml`. **When adding a page, add it to `sitemap.xml`.**
- Actions are pinned to commit SHAs; update by resolving the new tag's SHA.

## Conventions and constraints

- **Content Security Policy** (meta tag in every page's `<head>`): only self, Google Fonts, and Formspree. No inline scripts, no inline `style=""` attributes — put styles in `styles.css`. JSON-LD (`application/ld+json`) is fine.
- Match the existing design: dark theme, Geist / Geist Mono, lime accent `oklch(0.87 0.17 128)`. Mobile breakpoint is 760px; mobile content is **left-aligned** (centring was tried and reverted).
- Home page has Person structured data, canonical URLs and Open Graph tags on each page — keep them in sync if titles/pages change.
- Contact form posts to Formspree `https://formspree.io/f/xgavyroa` (in `main.js`). Don't enable Formspree reCAPTCHA (breaks the AJAX submit). The owner's email must never appear on the site.
- The resume PDF contains contact details; it's deliberately not indexed (robots.txt + `rel="nofollow"`). Don't put its contact details into page text.
- Vowbird.ai and Digistax should stay presented as independent companies; no "built by" links on their sites.
- Make each logical change its own commit (the owner likes being able to revert pieces). Verify in a headless browser (Chromium is at `/opt/pw-browsers/chromium`) at desktop and 390px widths before pushing.

## Infrastructure (no secrets)

- **DNS (Cloudflare, all DNS only / grey cloud):** GitHub Pages A `185.199.108–111.153`, AAAA `2606:50c0:8000–8003::153`, CNAME `www → zeroamplitude.github.io`. Two Google verification TXT records on `@` (`google-site-verification=PtAcwamV…` and `…=RmSxY-b-…`) — must stay. **No email on this domain:** SPF `v=spf1 -all`, DMARC `p=reject`, null MX. Don't restore old Google Workspace MX or `googlehosted.com` CNAMEs.
- **Search Console:** Domain property `sc-domain:nicholasdesouza.com`, verified via DNS; sitemap submitted.
- **Bing Webmaster Tools:** site imported from Search Console; IndexNow enabled via the deploy workflow.

## API access (only in the "Profile" cloud environment)

Sessions in the **Profile** environment have API credentials injected by the agent proxy — call the APIs
without auth headers and never print or log credential values:

- Cloudflare (Bearer) → `api.cloudflare.com`, DNS edit for the nicholasdesouza.com zone only
- Google Search Console (GCP service-account token) → `searchconsole.googleapis.com`
- Bing Webmaster (`apikey` parameter) → `ssl.bing.com` (`/webmaster/api.svc/json/...`)

Always show proposed DNS changes and get approval before creating, changing or deleting records.

## Open items (owner to do)

- GitHub: tick Enforce HTTPS; verify the domain in account Settings → Pages; ensure 2FA is on.
- Cloudflare: enable DNSSEC.
- Check Bing's IndexNow page shows received URLs; check Search Console Performance in 2–4 weeks.
