<!-- Updated: 2026-10-06 -->
# Structured data

JSON-LD in `<script type="application/ld+json">` in the `<head>` (the CSP allows it).
Markup must describe what is visible on the page. The hook checks syntax,
`@context`/`@type`, placeholders and retired types; Google's Rich Results Test
(search.google.com/test/rich-results) checks eligibility.

## What the site has

- `index.html`: `WebSite` (`#website`) and `Person` (`#person`) (name, url, image, jobTitle, description, worksFor,
  founder, alumniOf, address locality, knowsAbout, sameAs). Keep it in step
  with the resume section and the home description.

- `case-study.html`: `Article`, with the author linked to `#person`.

## Patterns for new pages

Give entities stable `@id`s so pages can refer to each other:
`https://nicholasdesouza.com/#person` and `https://nicholasdesouza.com/#website`.

**WebSite** (home page): helps Google show "Nicholas De Souza" as the site name.

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "@id": "https://nicholasdesouza.com/#website",
  "name": "Nicholas De Souza",
  "url": "https://nicholasdesouza.com/",
  "publisher": { "@id": "https://nicholasdesouza.com/#person" }
}
```

**Article** (case study): headline, image, dates and author by reference.

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "<the page's h1>",
  "description": "<the meta description>",
  "image": "https://nicholasdesouza.com/assets/og/<preview>.jpg",
  "datePublished": "<YYYY-MM-DD first published>",
  "dateModified": "<YYYY-MM-DD, same as the sitemap lastmod>",
  "author": {
    "@type": "Person",
    "@id": "https://nicholasdesouza.com/#person",
    "name": "Nicholas De Souza",
    "url": "https://nicholasdesouza.com/"
  },
  "mainEntityOfPage": "https://nicholasdesouza.com/case-study.html"
}
```

The Person on the home page carries that `@id`. Spell out the author's name
and url as well: Google doesn't reliably follow an `@id` to another page.
The hook keeps `dateModified` current whenever the page changes.

**Optional:** `ProfilePage` wrapping the Person on the home page
(`"@type": "ProfilePage", "mainEntity": {"@id": ".../#person"}`). Google
documents it for creator profile pages; a personal homepage fits, but the gain
is small.

## Don't

- `FAQPage` or `HowTo` (no rich results for this site; the hook blocks them).
- `Organization` markup for Digistax or Vowbird.ai on this site: they're
  independent companies with their own sites.
- `Review`/`AggregateRating` about yourself (against Google's guidelines).
- `sameAs` to profiles he doesn't control, or anything with contact details
  (`email`, `telephone`).
