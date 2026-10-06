<!-- Updated: 2026-10-06 -->
# AI search

## Policy (decided 2026-10-06)

**All crawlers are allowed**, AI training crawlers included. The site exists
to be found and described accurately, and an AI assistant that has read it
answers "who is Nicholas De Souza" better. The only exclusion is the resume
PDF (contact details), which stays disallowed for every crawler.

To revisit: blocking training while keeping AI search is possible by
disallowing `GPTBot`, `ClaudeBot`, `Google-Extended`, `Applebot-Extended`,
`CCBot`, `meta-externalagent` and `Bytespider`, while leaving the search and
user-fetch agents alone. `robots_ai.py` lists which agent does what.

## robots.txt gotcha

A crawler obeys only the most specific `User-agent` group that matches it.
`site/robots.txt` has one `*` group, so every crawler gets the resume
`Disallow`. Adding a named group, even an allow-everything one like
`User-agent: GPTBot` / `Allow: /`, means that crawler ignores the `*` group
and **can fetch the resume**. Any named group must repeat
`Disallow: /assets/Nicholas-De-Souza-Resume.pdf`. Run `robots_ai.py` after
every robots.txt edit.

Google AI Overviews and AI Mode use the normal Googlebot index;
`Google-Extended` only controls Gemini training and grounding, not Search.

## llms.txt

`site/llms.txt` is a Markdown summary of the site for AI tools (llmstxt.org).
No major search engine has said it uses the file, so treat it as cheap,
optional help for assistants and agents that fetch it. Regenerate with
`llms_txt.py`, then edit by hand: factual, short, no contact details, no
resume link. The hook checks its links.

## Writing for AI answers

The same things that help people help assistants quote the site correctly:

- State facts plainly in text (not only in images): role, employer, what each
  company does, outcomes with numbers.
- Keep the bio consistent across the site, Person JSON-LD, LinkedIn and GitHub.
- Name things the way people ask about them ("Digistax, an agent-run software
  consultancy"), not only with internal jargon.
