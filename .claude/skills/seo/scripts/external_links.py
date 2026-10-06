#!/usr/bin/env python3
"""Check every external link on the site's pages still works.

  external_links.py [--json]

Requests each http(s) link found in an <a href> in site/*.html (fonts and
preconnect hints are skipped) and reports anything that isn't 2xx after
redirects. LinkedIn and some others answer bots with 999/403; those are
reported as "blocked bots", not as broken. "limited" means this environment
couldn't reach the host at all.
"""
import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import BASE, emit, fetch_chain, local_pages  # noqa: E402

BOT_WALLS = {403, 429, 999}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    where = {}
    for fname, p in local_pages().items():
        for href in p.links:
            if href.startswith(("http://", "https://")) and not href.startswith(BASE):
                where.setdefault(href, set()).add(fname)

    def check(url):
        hops = fetch_chain(url)
        last = hops[-1]
        if last.limited and last.status != 429:
            state = "limited"
        elif last.status and 200 <= last.status < 300:
            state = "ok"
        elif last.status in BOT_WALLS:
            state = "blocked bots"
        else:
            state = "broken"
        return {"url": url, "status": last.status, "final": last.url, "state": state,
                "redirects": len(hops) - 1, "on": sorted(where[url])}

    with ThreadPoolExecutor(6) as pool:
        results = sorted(pool.map(check, where), key=lambda r: (r["state"] == "ok", r["url"]))

    def render(d):
        out = []
        for r in d:
            extra = f" -> {r['final']}" if r["redirects"] else ""
            out.append(f"[{r['state']}] {r['status']} {r['url']}{extra}  ({', '.join(r['on'])})")
        return "\n".join(out) or "no external links"

    emit(results, a.json, render)


if __name__ == "__main__":
    main()
