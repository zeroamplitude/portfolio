#!/usr/bin/env python3
"""Which crawlers may fetch which paths, according to robots.txt.

  robots_ai.py                  # site/robots.txt in this repo
  robots_ai.py --live           # https://nicholasdesouza.com/robots.txt
  robots_ai.py --path /gallery.html --json

Remember how groups work: a crawler obeys only the most specific User-agent
group that names it. Adding "User-agent: GPTBot / Allow: /" would drop the
"*" group's Disallow lines (the resume) for GPTBot, so repeat them in any
named group.
"""
import argparse
import sys
import urllib.robotparser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import BASE, SITE, emit, fetch  # noqa: E402

# (user-agent token, operator, purpose)
CRAWLERS = [
    ("Googlebot", "Google", "search"),
    ("Bingbot", "Microsoft", "search (also feeds Copilot and DuckDuckGo)"),
    ("Google-Extended", "Google", "Gemini training/grounding (not search)"),
    ("Applebot", "Apple", "Siri/Spotlight search"),
    ("Applebot-Extended", "Apple", "Apple AI training"),
    ("OAI-SearchBot", "OpenAI", "ChatGPT search results"),
    ("ChatGPT-User", "OpenAI", "fetches a page a ChatGPT user asked about"),
    ("GPTBot", "OpenAI", "model training"),
    ("Claude-SearchBot", "Anthropic", "Claude search results"),
    ("Claude-User", "Anthropic", "fetches a page a Claude user asked about"),
    ("ClaudeBot", "Anthropic", "model training"),
    ("PerplexityBot", "Perplexity", "Perplexity search results"),
    ("Perplexity-User", "Perplexity", "fetches a page a user asked about"),
    ("meta-externalagent", "Meta", "Meta AI training"),
    ("CCBot", "Common Crawl", "open dataset used for training"),
    ("Bytespider", "ByteDance", "training"),
]
DEFAULT_PATHS = ["/", "/case-study.html", "/assets/Nicholas-De-Souza-Resume.pdf"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--live", action="store_true", help="fetch the deployed robots.txt instead of site/robots.txt")
    ap.add_argument("--path", action="append", help="path to test (repeatable)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.live:
        f = fetch(BASE + "robots.txt")
        if f.limited or f.status != 200:
            sys.exit(f"could not fetch {BASE}robots.txt ({f.status or f.error}); environment limitation, try without --live")
        text, source = f.text(), BASE + "robots.txt"
    else:
        text, source = (SITE / "robots.txt").read_text(encoding="utf-8"), "site/robots.txt"

    rp = urllib.robotparser.RobotFileParser()
    rp.parse(text.splitlines())
    paths = a.path or DEFAULT_PATHS
    rows = [{"crawler": ua, "operator": op, "purpose": why,
             "allowed": {p: rp.can_fetch(ua, BASE.rstrip("/") + p) for p in paths}} for ua, op, why in CRAWLERS]
    data = {"source": source, "sitemaps": rp.site_maps() or [], "paths": paths, "crawlers": rows}

    def render(d):
        w = max(len(r["crawler"]) for r in d["crawlers"])
        out = [f"{d['source']}  sitemaps: {', '.join(d['sitemaps']) or 'NONE'}", ""]
        out.append(" " * (w + 2) + "  ".join(d["paths"]))
        for r in d["crawlers"]:
            cells = "  ".join(("allow" if r["allowed"][p] else "BLOCK").ljust(len(p)) for p in d["paths"])
            out.append(f"{r['crawler'].ljust(w)}  {cells}  ({r['operator']}: {r['purpose']})")
        return "\n".join(out)

    emit(data, a.json, render)


if __name__ == "__main__":
    main()
