# Nicholas De Souza — portfolio

Static portfolio site, built from a Claude Design handoff.

```
site/
  index.html        Home: hero, highlights, Now building, Past work, Resume, contact
  case-study.html   Digistax case study
  gallery.html      Screenshot gallery with lightbox
  styles.css        All styles (dark theme, Geist, lime accent)
  main.js           Contact form modal (Formspree), carousels, lightbox
  assets/           Images and resume
```

No build step. To preview locally: `cd site && python3 -m http.server` and open http://localhost:8000.

## Contact form

All "Get in touch" / "Start a conversation" / "Start a project" buttons open one form that posts to Formspree (`https://formspree.io/f/xgavyroa`, set in `site/main.js`). Messages go to the email on that Formspree account; the address never appears on the site.

After the site is live, in Formspree → the form's **Settings**, add your domain under allowed/restricted domains so the endpoint can't be used from other sites.

## Hosting (free): GitHub Pages

`.github/workflows/pages.yml` publishes `site/` on every push to `main`.

1. Push this repository to GitHub (public repos get Pages for free).
2. In the repo, **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Push to `main` (or run the workflow manually). The site appears at `https://<username>.github.io/<repo>/`.

## Custom domain

1. In the repo, **Settings → Pages → Custom domain**, enter your domain (e.g. `www.example.com`) and save.
2. At your domain registrar's DNS settings, add:

   | Type  | Name  | Value                   |
   |-------|-------|-------------------------|
   | A     | `@`   | `185.199.108.153`       |
   | A     | `@`   | `185.199.109.153`       |
   | A     | `@`   | `185.199.110.153`       |
   | A     | `@`   | `185.199.111.153`       |
   | AAAA  | `@`   | `2606:50c0:8000::153`   |
   | AAAA  | `@`   | `2606:50c0:8001::153`   |
   | AAAA  | `@`   | `2606:50c0:8002::153`   |
   | AAAA  | `@`   | `2606:50c0:8003::153`   |
   | CNAME | `www` | `<username>.github.io`  |

   Remove any existing A/AAAA/CNAME records for `@` and `www` that point to your old host first.
3. Wait for DNS to propagate (minutes to a few hours), then tick **Enforce HTTPS** on the Pages settings screen.
4. Optional but recommended: verify the domain under your GitHub account's **Settings → Pages** to prevent takeover.
