#!/usr/bin/env python3
"""Check pages as search engines see them: redirects, status, headers and on-page tags.

  live_check.py                         # every page in the sitemap, plus host/scheme redirects
  live_check.py https://nicholasdesouza.com/case-study.html
  live_check.py site/case-study.html    # a local file (tags only, no HTTP)
  live_check.py --json ...

Each finding is (severity, message). "limited" means this environment could not
reach the URL (network policy, DNS, rate limit); it is not evidence about the site.
"""
import argparse
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import BASE, SITE, emit, fetch_chain, parse  # noqa: E402

HOST = urllib.parse.urlparse(BASE).netloc


def tag_findings(p, url):
    out = []
    t, d = p.title, p.meta.get("description", "")
    if not t:
        out.append(("critical", "no <title>"))
    elif not 30 <= len(t) <= 60:
        out.append(("warning", f"title is {len(t)} chars (aim for 30-60): {t!r}"))
    if not d:
        out.append(("critical", "no meta description"))
    elif not 120 <= len(d) <= 160:
        out.append(("warning", f"meta description is {len(d)} chars (aim for 120-160)"))
    if url and p.canonical and p.canonical != url:
        out.append(("warning", f"canonical {p.canonical} differs from the URL checked ({url})"))
    if not p.canonical:
        out.append(("critical", "no canonical link"))
    if "noindex" in p.meta.get("robots", ""):
        out.append(("info", "page is noindex"))
    h1 = [h for k, h in p.headings if k == "h1"]
    if len(h1) != 1:
        out.append(("warning", f"{len(h1)} <h1> elements"))
    for key in ("og:title", "og:description", "og:image", "og:url", "twitter:card"):
        if not p.meta.get(key):
            out.append(("warning", f"no {key}"))
    if not p.lang:
        out.append(("warning", "<html> has no lang attribute"))
    if not [i for i in p.imgs if i.get("loading") != "lazy"] and p.imgs:
        out.append(("info", "every image is lazy-loaded; the first visible image should load eagerly for LCP"))
    missing_dims = [i.get("src") for i in p.imgs if not (i.get("width") and i.get("height"))]
    if missing_dims:
        out.append(("info", f"{len(missing_dims)} <img> without width/height (layout shift risk unless CSS sizes them)"))
    return out


def summary(p):
    return {
        "title": p.title, "description": p.meta.get("description", ""), "canonical": p.canonical,
        "robots": p.meta.get("robots", ""), "h1": [h for k, h in p.headings if k == "h1"],
        "h2": [h for k, h in p.headings if k == "h2"], "words": p.words, "schema_types": p.schema_types(),
        "og_image": p.meta.get("og:image", ""),
    }


def check_url(url):
    hops = fetch_chain(url)
    last = hops[-1]
    res = {"url": url, "chain": [[h.url, h.status] for h in hops], "findings": []}
    if last.limited:
        res["findings"].append(("limited", f"could not fetch ({last.status or last.error})"))
        return res
    f = res["findings"]
    if len(hops) > 2:
        f.append(("warning", f"{len(hops) - 1} redirects before the final page"))
    if any(h.status in (302, 303, 307) for h in hops[:-1]):
        f.append(("warning", "temporary redirect in the chain; permanent (301/308) passes signals reliably"))
    if last.status != 200:
        f.append(("critical", f"final status {last.status}"))
    hd = last.headers
    if "strict-transport-security" not in hd:
        f.append(("info", "no HSTS header (GitHub Pages can't set it; Cloudflare proxy could)"))
    if "noindex" in hd.get("x-robots-tag", ""):
        f.append(("critical", f"X-Robots-Tag: {hd['x-robots-tag']}"))
    if "text/html" in hd.get("content-type", ""):
        p = parse(last.text())
        res["page"] = summary(p)
        f += tag_findings(p, hops[-1].url)
    return res


def check_host_variants():
    """http:// and www. should 301 to https://apex/."""
    out = []
    for v in (f"http://{HOST}/", f"https://www.{HOST}/", f"http://www.{HOST}/"):
        hops = fetch_chain(v)
        final = hops[-1]
        if final.limited:
            out.append({"url": v, "chain": [[h.url, h.status] for h in hops], "findings": [("limited", f"could not fetch ({final.error or final.status})")]})
            continue
        ok = final.url == BASE and final.status == 200
        out.append({"url": v, "chain": [[h.url, h.status] for h in hops],
                    "findings": [] if ok else [("critical", f"ends at {final.url} ({final.status}), expected {BASE}")]})
    return out


def sitemap_urls():
    return re.findall(r"<loc>([^<]+)</loc>", (SITE / "sitemap.xml").read_text(encoding="utf-8"))


def render(results):
    lines = []
    for r in results:
        lines.append(f"\n{r['url']}")
        if len(r.get("chain", [])) > 1:
            lines.append("  chain: " + " -> ".join(f"{u} [{s}]" for u, s in r["chain"]))
        if "page" in r:
            pg = r["page"]
            lines.append(f"  title ({len(pg['title'])}): {pg['title']}")
            lines.append(f"  description ({len(pg['description'])}): {pg['description']}")
            lines.append(f"  h1: {pg['h1']}  words: {pg['words']}  schema: {pg['schema_types']}")
        for sev, msg in r["findings"] or [("pass", "no issues")]:
            lines.append(f"  [{sev}] {msg}")
    return "\n".join(lines).lstrip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="*", help="URLs or local .html files (default: sitemap URLs + host variants)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    results = []
    targets = a.targets or sitemap_urls()
    for t in targets:
        if not re.match(r"^https?://", t):
            path = Path(t)
            p = parse(path.read_text(encoding="utf-8"))
            url = BASE if path.name == "index.html" else BASE + path.name
            results.append({"url": str(path), "page": summary(p), "findings": tag_findings(p, url)})
        else:
            results.append(check_url(t))
    if not a.targets:
        results += check_host_variants()
    emit(results, a.json, render)


if __name__ == "__main__":
    main()
