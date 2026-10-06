<!-- Updated: 2026-10-06 -->
# Titles and descriptions

## Titles (30–60 characters)

- Pattern: `<What the page is> — Nicholas De Souza`. Home is the exception:
  `Nicholas De Souza — <role>`, because the name is what people search for.
- Lead with the distinctive words: "Digistax case study", not "Case study: Digistax".
- One page, one title. The hook blocks duplicates.
- `og:title` matches `<title>` unless the social version needs to be shorter.

## Meta descriptions (120–160 characters)

- First clause says what the page is; the rest gives the most concrete
  specifics (company names, outcomes, technologies). Write it as a sentence
  for a person deciding whether to click, not as a keyword list.
- Use names people search: Nicholas De Souza, Salesforce, Agentforce,
  Digistax, Vowbird.ai, AI agents, Toronto.
- No contact details, no superlatives ("world-class"), no claims the page
  doesn't back up.
- `og:description` can be shorter and punchier; keep both in sync with the copy.
- When the home description changes, update the Person JSON-LD `description` too.

## Process

1. Show current vs proposed for each page with character counts
   (`live_check.py site/<page>.html` prints both).
2. Check `gsc.py performance --by query` first: if a page already earns
   impressions for a query, keep that phrase.
3. After deploy, give Google 2–4 weeks before judging CTR changes.

## Examples

| | Text | Chars |
|---|---|---|
| Too vague | "Welcome to my portfolio. Learn more about my work and projects." | 63 |
| Too long | Anything over 160: Google truncates mid-sentence | |
| Good (home) | "Toronto solution engineer at Salesforce who builds AI agents and takes them to production. Founder of Digistax and Vowbird.ai." | 126 |
