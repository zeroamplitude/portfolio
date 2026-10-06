#!/usr/bin/env python3
"""Draft site/llms.txt (https://llmstxt.org) from the pages in site/.

  llms_txt.py            # print the draft
  llms_txt.py --write    # write site/llms.txt

The draft is built from each page's title, meta description and <h2>s plus
the Person JSON-LD. Edit the result by hand; it is a summary for AI tools, so
keep it factual and short. Never add contact details (email, phone, the resume).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import SITE, local_pages, page_url  # noqa: E402

SKIP = {"404.html"}


def person(pages):
    for block in pages["index.html"].ld:
        try:
            d = json.loads(block)
        except ValueError:
            continue
        if d.get("@type") == "Person":
            return d
    return {}


def build():
    pages = local_pages()
    me = person(pages)
    name = me.get("name", "Nicholas De Souza")
    home = pages["index.html"]
    lines = [f"# {name}", "", f"> {home.meta.get('description', '')}", ""]
    if me.get("jobTitle") and me["jobTitle"] not in home.meta.get("description", ""):
        org = (me.get("worksFor") or {}).get("name")
        lines.append(f"{me['jobTitle']}{f' at {org}' if org else ''}. "
                     + ("Founder of " + " and ".join(f["name"] for f in me.get("founder", [])) + "." if me.get("founder") else ""))
        lines.append("")
    lines += ["## Pages", ""]
    order = ["index.html"] + [f for f in pages if f != "index.html"]
    for fname in order:
        p = pages[fname]
        if fname in SKIP:
            continue
        title = p.title.split(" — ")[0] if fname != "index.html" else "Home"
        lines.append(f"- [{title}]({page_url(fname)}): {p.meta.get('description', '')}")
        h2 = [h.rstrip(".") for k, h in p.headings if k == "h2" and not h.endswith("?")]
        if h2 and fname != "index.html":
            lines.append(f"  Sections: {'; '.join(h2)}")
    if me.get("sameAs"):
        lines += ["", "## Elsewhere", ""] + [f"- {u}" for u in me["sameAs"]]
    lines += ["", "## Optional", "",
              "- [Full site as Markdown](https://nicholasdesouza.com/llms-full.txt): every page's text in one file",
              "- Each page also has a Markdown copy: replace .html with .md (the home page is /index.md)"]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    text = build()
    if a.write:
        (SITE / "llms.txt").write_text(text, encoding="utf-8")
        print(f"wrote site/llms.txt ({len(text)} bytes)")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
