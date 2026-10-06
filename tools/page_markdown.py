#!/usr/bin/env python3
"""Generate Markdown copies of the site's pages for LLMs.

  python3 tools/page_markdown.py

Writes site/<page>.md for every indexable page (index.html -> index.md) and
site/llms-full.txt (llms.txt followed by every page's Markdown). The deploy
workflow runs this before publishing; the outputs are gitignored. The "Copy
page" menu (main.js) copies, opens and links to these files.

Skipped: nav, footer, buttons, SVG, hidden elements, carousel controls and
links marked rel="nofollow" (the resume), which keep their text only.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

BASE = "https://nicholasdesouza.com/"
# GitHub Pages may send .md/.txt without a charset; a byte-order mark makes browsers
# decode them as UTF-8 regardless (fetch().text() strips it again).
ENCODING = "utf-8-sig"
SITE = Path(__file__).resolve().parent.parent / "site"
SKIP_TAGS = {"nav", "footer", "button", "svg", "script", "style", "form", "template", "noscript"}
SKIP_CLASSES = {"carousel-bar", "sprite", "copy-page", "back", "mono g-num"}
BLOCK = {"p", "div", "section", "article", "header", "figure", "figcaption", "li", "ul", "ol",
         "h1", "h2", "h3", "h4", "main", "blockquote", "table", "tr"}
VOID = {"img", "br", "hr", "meta", "link", "input", "source", "wbr"}


class ToMarkdown(HTMLParser):
    def __init__(self, page_url):
        super().__init__(convert_charrefs=True)
        self.url = page_url
        self.out, self.buf = [], ""
        self.in_main = False
        self.skip = 0          # depth inside a skipped element
        self.stack = []        # (tag, skipped?) for every open non-void element
        self.lists = []        # "ul" / "ol" counters
        self.link = None       # [href, text-start] while inside <a>
        self.heading = None
        self.figcap = False

    # ---- helpers
    def flush(self):
        text = " ".join(self.buf.split())
        self.buf = ""
        if not text:
            return
        if self.heading:
            text = "#" * int(self.heading[1]) + " " + text
        elif self.lists:
            kind, n = self.lists[-1]
            indent = "  " * (len(self.lists) - 1)
            if kind == "ol":
                self.lists[-1][1] += 1
                text = f"{indent}{n + 1}. {text}"
            else:
                text = f"{indent}- {text}"
            self.out.append(("li", text))
            return
        elif self.figcap:
            text = f"*{text}*"
        self.out.append(("p", text))

    def skipped(self, tag, a):
        cls = a.get("class") or ""
        return (tag in SKIP_TAGS or a.get("aria-hidden") == "true" or "hidden" in a
                or any(c in cls.split() for c in SKIP_CLASSES) or cls in SKIP_CLASSES)

    # ---- parser callbacks
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "main":
            self.in_main = True
        if not self.in_main:
            return
        if tag in VOID:
            if self.skip:
                return
            if tag == "br":
                self.buf += " "
            elif tag == "img" and a.get("alt"):
                self.flush()
                self.out.append(("p", f"![{a['alt']}]({urljoin(self.url, a.get('src', ''))})"))
            return
        is_skipped = bool(self.skip) or self.skipped(tag, a)
        self.stack.append((tag, is_skipped))
        if is_skipped:
            self.skip += 1
            return
        if tag in BLOCK:
            self.flush()
        if tag in ("h1", "h2", "h3", "h4"):
            self.heading = tag
        elif tag in ("ul", "ol"):
            self.lists.append([tag, 0])
        elif tag == "figcaption":
            self.figcap = True
        elif tag == "a" and a.get("href"):
            nofollow = "nofollow" in (a.get("rel") or "")
            href = a["href"]
            self.link = None if nofollow or href.startswith("#") else [urljoin(self.url, href), len(self.buf)]
        elif tag in ("strong", "b"):
            self.buf = self.buf.rstrip() + (" **" if self.buf.strip() else "**")
        elif tag == "span":
            self.buf += " "

    def handle_endtag(self, tag):
        if not self.in_main or tag in VOID:
            return
        # Pop to the matching open tag (tolerates sloppy nesting).
        while self.stack:
            t, was_skipped = self.stack.pop()
            if was_skipped:
                self.skip -= 1
            if t == tag:
                break
        else:
            return
        if self.skip:
            return
        if tag == "main":
            self.flush()
            self.in_main = False
        elif tag == "a" and self.link:
            href, start = self.link
            text = self.buf[start:].strip()
            self.buf = self.buf[:start] + (f" [{text}]({href})" if text else "")
            self.link = None
        elif tag in ("strong", "b"):
            self.buf = self.buf.rstrip() + "**: " if tag == "strong" and self.lists else self.buf.rstrip() + "** "
        elif tag == "span":
            self.buf += " "
        if tag in BLOCK:
            self.flush()
        if tag in ("h1", "h2", "h3", "h4"):
            self.heading = None
        elif tag in ("ul", "ol") and self.lists:
            self.lists.pop()
        elif tag == "figcaption":
            self.figcap = False

    def handle_data(self, data):
        if self.in_main and not self.skip:
            self.buf += data


def head_meta(html, pattern):
    m = re.search(pattern, html)
    return m.group(1) if m else ""


def page_markdown(path):
    html = path.read_text(encoding="utf-8")
    url = head_meta(html, r'<link rel="canonical" href="([^"]+)"') or BASE + path.name
    conv = ToMarkdown(url)
    conv.feed(html)
    body = ""
    for i, (kind, text) in enumerate(conv.out):
        if i:
            body += "\n" if kind == "li" and conv.out[i - 1][0] == "li" else "\n\n"
        body += text
    body = re.sub(r"\*\*\*\*", "", body)              # empty bold
    body = re.sub(r"\*\*: ([.,;:!?])", r"**\1", body)
    body = re.sub(r"[ \t]+([.,;:!?])", r"\1", body)
    title = head_meta(html, r"<title>([^<]*)</title>")
    desc = head_meta(html, r'<meta name="description" content="([^"]*)"')
    return f"---\ntitle: {title}\nurl: {url}\ndescription: {desc}\n---\n\n{body}\n"


def indexable(html):
    return ('rel="canonical"' in html and "noindex" not in html
            and 'http-equiv="refresh"' not in html)


def main():
    written = []
    for path in sorted(SITE.glob("*.html")):
        html = path.read_text(encoding="utf-8")
        if not indexable(html):
            continue
        md = page_markdown(path)
        out = path.with_suffix(".md")
        out.write_text(md, encoding=ENCODING)
        written.append((path, md))
    llms = (SITE / "llms.txt").read_text(encoding="utf-8") if (SITE / "llms.txt").exists() else ""
    order = sorted(written, key=lambda w: (w[0].name != "index.html", w[0].name))
    full = llms.rstrip() + "\n\n" + "\n\n".join(md for _, md in order)
    (SITE / "llms-full.txt").write_text(full, encoding=ENCODING)
    print(f"wrote {', '.join(p.with_suffix('.md').name for p, _ in written)} and llms-full.txt", file=sys.stderr)


if __name__ == "__main__":
    main()
