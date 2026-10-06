#!/usr/bin/env python3
"""Google Search Console for sc-domain:nicholasdesouza.com.

Credentials are injected by the cloud environment's proxy (the "Profile"
environment); the script sends no auth header and never handles a key.

  gsc.py performance [--days 28] [--by query|page|date|device|country] [--limit 25]
  gsc.py sitemaps
  gsc.py inspect [URL ...]        # default: every URL in site/sitemap.xml
  add --json to any command for raw output

Search Console data lags by 2-3 days, so --days counts back from 3 days ago.
"""
import argparse
import datetime
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import SITE, emit, get_json  # noqa: E402

PROPERTY = "sc-domain:nicholasdesouza.com"
API = "https://searchconsole.googleapis.com"
SITE_PATH = f"{API}/webmasters/v3/sites/{urllib.parse.quote(PROPERTY, safe='')}"


def call(url, body=None):
    f, data = get_json(url, body)
    if f.status != 200:
        detail = (data or {}).get("error", {}).get("message") if isinstance(data, dict) else (f.error or f.text()[:200])
        why = "environment limitation (no Search Console access here)" if f.limited or f.status in (401, 403) else "API error"
        sys.exit(f"Search Console {why}: HTTP {f.status}: {detail}")
    return data


def performance(a):
    end = datetime.date.today() - datetime.timedelta(days=3)
    start = end - datetime.timedelta(days=a.days - 1)
    body = {"startDate": start.isoformat(), "endDate": end.isoformat(), "dimensions": [a.by], "rowLimit": a.limit}
    rows = call(f"{SITE_PATH}/searchAnalytics/query", body).get("rows", [])
    data = {"range": [body["startDate"], body["endDate"]], "by": a.by,
            "rows": [{"key": r["keys"][0], "clicks": r["clicks"], "impressions": r["impressions"],
                      "ctr": round(r["ctr"] * 100, 1), "position": round(r["position"], 1)} for r in rows]}

    def render(d):
        out = [f"{d['range'][0]} to {d['range'][1]}, by {d['by']}"]
        if not d["rows"]:
            return out[0] + "\n  no data yet (new or low-traffic sites can take weeks to show rows)"
        out.append(f"  {'clicks':>6} {'impr':>6} {'ctr%':>5} {'pos':>5}  {d['by']}")
        for r in d["rows"]:
            out.append(f"  {r['clicks']:>6} {r['impressions']:>6} {r['ctr']:>5} {r['position']:>5}  {r['key']}")
        return "\n".join(out)

    emit(data, a.json, render)


def sitemaps(a):
    data = call(f"{SITE_PATH}/sitemaps").get("sitemap", [])

    def render(d):
        return "\n".join(
            f"{s['path']}\n  submitted {s.get('lastSubmitted', '-')}, last read by Google {s.get('lastDownloaded', '-')}, "
            f"errors {s.get('errors', 0)}, warnings {s.get('warnings', 0)}, pending {s.get('isPending')}"
            + "".join(f"\n  {c.get('type')}: {c.get('submitted')} submitted" for c in s.get("contents", []))
            for s in d) or "no sitemaps submitted"

    emit(data, a.json, render)


def inspect(a):
    urls = a.urls or re.findall(r"<loc>([^<]+)</loc>", (SITE / "sitemap.xml").read_text(encoding="utf-8"))
    results = []
    for u in urls:
        r = call(f"{API}/v1/urlInspection/index:inspect", {"inspectionUrl": u, "siteUrl": PROPERTY})
        idx = r.get("inspectionResult", {}).get("indexStatusResult", {})
        rich = r.get("inspectionResult", {}).get("richResultsResult", {})
        results.append({
            "url": u, "verdict": idx.get("verdict"), "coverage": idx.get("coverageState"),
            "indexing": idx.get("indexingState"), "robots": idx.get("robotsTxtState"),
            "fetch": idx.get("pageFetchState"), "last_crawl": idx.get("lastCrawlTime"),
            "google_canonical": idx.get("googleCanonical"), "user_canonical": idx.get("userCanonical"),
            "rich_results": [i.get("richResultType") for i in rich.get("detectedItems", [])],
        })

    def render(d):
        out = []
        for r in d:
            out.append(f"{r['url']}\n  {r['verdict']}: {r['coverage']} (last crawl {r['last_crawl'] or 'never'})")
            if r["google_canonical"] and r["google_canonical"] != r["user_canonical"]:
                out.append(f"  ! Google chose canonical {r['google_canonical']}, page declares {r['user_canonical']}")
            if r["rich_results"]:
                out.append(f"  rich results: {', '.join(r['rich_results'])}")
        return "\n".join(out)

    emit(results, a.json, render)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("performance")
    p.add_argument("--days", type=int, default=28)
    p.add_argument("--by", default="query", choices=["query", "page", "date", "device", "country"])
    p.add_argument("--limit", type=int, default=25)
    sub.add_parser("sitemaps")
    i = sub.add_parser("inspect")
    i.add_argument("urls", nargs="*")
    for s in sub.choices.values():
        s.add_argument("--json", action="store_true")
    a = ap.parse_args()
    {"performance": performance, "sitemaps": sitemaps, "inspect": inspect}[a.cmd](a)


if __name__ == "__main__":
    main()
