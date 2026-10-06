#!/usr/bin/env python3
"""Core Web Vitals and Lighthouse performance from the PageSpeed Insights API.

  pagespeed.py [URL] [--strategy mobile|desktop] [--json]

The keyless API is heavily rate-limited (HTTP 429 is common). Set PSI_API_KEY
in the environment for a reliable quota; it's sent as a query parameter, so
only use a key restricted to the PageSpeed Insights API.

Field data (real Chrome users, 28 days) is what Google ranks on; low-traffic
pages often have none, in which case only lab data is shown.
"""
import argparse
import os
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import BASE, emit, get_json  # noqa: E402

# metric: (good up to, poor from, unit). Thresholds are Google's, at the 75th percentile.
FIELD = {
    "LARGEST_CONTENTFUL_PAINT_MS": ("LCP", 2500, 4000, "ms"),
    "INTERACTION_TO_NEXT_PAINT": ("INP", 200, 500, "ms"),
    "CUMULATIVE_LAYOUT_SHIFT_SCORE": ("CLS", 0.1, 0.25, ""),
}


def rate(v, good, poor):
    return "good" if v <= good else "poor" if v > poor else "needs improvement"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url", nargs="?", default=BASE)
    ap.add_argument("--strategy", default="mobile", choices=["mobile", "desktop"])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    q = {"url": a.url, "strategy": a.strategy, "category": "performance"}
    if os.environ.get("PSI_API_KEY"):
        q["key"] = os.environ["PSI_API_KEY"]
    f, r = get_json("https://www.googleapis.com/pagespeedonline/v5/runPagespeed?" + urllib.parse.urlencode(q))
    if f.status != 200 or not r:
        why = "rate-limited without PSI_API_KEY" if f.status == 429 else (f.error or f"HTTP {f.status}")
        sys.exit(f"PageSpeed Insights unavailable ({why}); environment limitation, not a site result")

    field = {}
    for key, (name, good, poor, unit) in FIELD.items():
        m = (r.get("loadingExperience", {}).get("metrics") or {}).get(key)
        if m:
            v = m["percentile"] / 100 if name == "CLS" else m["percentile"]
            field[name] = {"p75": v, "unit": unit, "rating": rate(v, good, poor)}
    lh = r.get("lighthouseResult", {})
    audits = lh.get("audits", {})
    lab = {k: audits[k].get("displayValue") for k in
           ("largest-contentful-paint", "cumulative-layout-shift", "total-blocking-time", "first-contentful-paint", "speed-index")
           if k in audits}
    opportunities = sorted(
        ({"id": k, "title": v.get("title"), "savings_ms": v.get("details", {}).get("overallSavingsMs", 0)}
         for k, v in audits.items() if v.get("details", {}).get("type") == "opportunity" and v.get("details", {}).get("overallSavingsMs", 0) > 50),
        key=lambda o: -o["savings_ms"])
    data = {"url": a.url, "strategy": a.strategy,
            "score": round((lh.get("categories", {}).get("performance", {}).get("score") or 0) * 100),
            "field": field, "lab": lab, "opportunities": opportunities[:8]}

    def render(d):
        out = [f"{d['url']} ({d['strategy']})  Lighthouse performance {d['score']}/100"]
        out.append("  field (real users, p75): " + (", ".join(f"{k} {v['p75']}{v['unit']} {v['rating']}" for k, v in d["field"].items())
                                                    or "no field data (not enough Chrome traffic)"))
        out.append("  lab: " + ", ".join(f"{k} {v}" for k, v in d["lab"].items()))
        for o in d["opportunities"]:
            out.append(f"  - {o['title']} (~{o['savings_ms']} ms)")
        return "\n".join(out)

    emit(data, a.json, render)


if __name__ == "__main__":
    main()
