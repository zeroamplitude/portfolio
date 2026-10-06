#!/usr/bin/env python3
"""SEO check-and-update for the site, run by Claude Code before every `git commit`.

Wired up as a PreToolUse hook in .claude/settings.json. It reads the hook's JSON
from stdin and does nothing unless the Bash command runs `git commit`.

Updates (then stages) automatically:
  - sitemap.xml: adds any indexable page that's missing, drops entries whose
    page is gone, and sets <lastmod> to today for pages changed since HEAD.
  - og:image:width / og:image:height: corrected to the image's real size.

Blocks the commit (exit 2, reasons on stderr) when a page is missing a title,
description, canonical URL or Open Graph tags, has a canonical/og:url mismatch,
not exactly one <h1>, an <img> without alt, broken JSON-LD, or a local link,
image or #fragment that doesn't resolve, JSON-LD without @context/@type or with
placeholder text or a retired type (HowTo, FAQPage, ...), titles or descriptions
duplicated across pages, or a broken link in llms.txt. Soft issues (title and
description length, images over 300 KB) are reported without blocking.

Run by hand: python3 .claude/hooks/seo-check.py --run
"""
import datetime
import json
import re
import struct
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://nicholasdesouza.com/"
NOINDEX_PAGES = {"404.html"}
IMAGE_WARN_BYTES = 300_000
RETIRED_SCHEMA = {"HowTo", "SpecialAnnouncement", "FAQPage", "ClaimReview"}  # no rich results for this site
PLACEHOLDER = re.compile(r"\[(?:your|insert|replace|todo|name|business name|city|phone|address)[^\]]*\]|lorem ipsum", re.I)
REQUIRED_META = ["og:type", "og:title", "og:description", "og:url", "og:site_name", "og:image", "twitter:card"]


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True).stdout


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self._in_title = "", False
        self.meta, self.canonical = {}, None
        self.h1 = 0
        self.imgs, self.links, self.ids = [], [], set()
        self.ld, self._in_ld = [], False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = a.get("property") or a.get("name")
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            if a.get("rel") == "canonical":
                self.canonical = a.get("href")
            elif a.get("href"):
                self.links.append(a["href"])
        elif tag == "h1":
            self.h1 += 1
        elif tag == "img":
            self.imgs.append(a)
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "script":
            if a.get("type") == "application/ld+json":
                self._in_ld = True
                self.ld.append("")
            elif a.get("src"):
                self.links.append(a["src"])

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script":
            self._in_ld = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_ld:
            self.ld[-1] += data


def image_size(path):
    """(width, height) for PNG, JPEG or WebP, or None."""
    data = path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        chunk = data[12:16]
        if chunk == b"VP8X":
            return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
        if chunk == b"VP8 ":
            w, h = struct.unpack("<HH", data[26:30])
            return w & 0x3FFF, h & 0x3FFF
        if chunk == b"VP8L":
            b = int.from_bytes(data[21:25], "little")
            return (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return None


def schema_problems(data, top=True):
    """Problems in a parsed JSON-LD value: missing @context/@type, placeholders, retired types."""
    out = []
    if isinstance(data, list):
        for item in data:
            out += schema_problems(item, top)
        return out
    if isinstance(data, dict):
        if top and "@graph" not in data and "@context" not in data:
            out.append("missing @context")
        if top and "@graph" not in data and "@type" not in data:
            out.append("missing @type")
        types = data.get("@type", [])
        for t in [types] if isinstance(types, str) else types:
            if t in RETIRED_SCHEMA:
                out.append(f"uses @type {t}, which gets no rich results here; remove it")
        for key, val in data.items():
            if isinstance(val, str) and PLACEHOLDER.search(val):
                out.append(f"{key} looks like placeholder text: {val!r}")
            elif key == "@graph":
                out += schema_problems(val, True)
            elif isinstance(val, (dict, list)):
                out += schema_problems(val, False)
    return out


def page_url(name):
    return BASE if name == "index.html" else BASE + name


def resolve(site, page_name, ref):
    """Map a link on a page to (local file, fragment), or None for external links."""
    if re.match(r"^[a-z]+:", ref) and not ref.startswith(BASE):
        return None  # https:, mailto:, data: ...
    if ref.startswith(BASE):
        ref = "/" + ref[len(BASE):]
    ref, _, frag = ref.partition("#")
    ref = ref.split("?")[0]
    if not ref:
        return site / page_name, frag
    target = site / ref.lstrip("/") if ref.startswith("/") else (site / ref)
    target = Path(str(target.resolve()))
    if target.is_dir():
        target = target / "index.html"
    return target, frag


def main():
    manual = "--run" in sys.argv
    if not manual:
        try:
            cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
        except ValueError:
            return 0
        if not re.search(r"(^|[\s;&|(])git(\s+-C\s+\S+)?\s+commit\b", cmd):
            return 0

    root = Path(git("rev-parse", "--show-toplevel", cwd=Path(__file__).parent).strip())
    site = root / "site"
    if not site.is_dir():
        return 0
    today = datetime.date.today().isoformat()
    errors, warnings, fixed = [], [], []

    pages, parsed = sorted(p.name for p in site.glob("*.html")), {}
    for name in pages:
        p = Page()
        p.feed((site / name).read_text(encoding="utf-8"))
        parsed[name] = p

    for name in pages:
        p, path = parsed[name], site / name
        where = f"site/{name}"
        indexable = name not in NOINDEX_PAGES

        if not p.title.strip():
            errors.append(f"{where}: missing <title>")
        elif indexable and not 30 <= len(p.title) <= 60:
            warnings.append(f"{where}: title is {len(p.title)} chars (aim for 30–60)")
        desc = p.meta.get("description", "")
        if not desc:
            errors.append(f"{where}: missing meta description")
        elif indexable and not 120 <= len(desc) <= 160:
            warnings.append(f"{where}: meta description is {len(desc)} chars (aim for 120–160)")
        if p.h1 != 1:
            errors.append(f"{where}: has {p.h1} <h1> elements (expected exactly 1)")
        for img in p.imgs:
            if "alt" not in img:
                errors.append(f"{where}: <img src=\"{img.get('src')}\"> has no alt attribute")
        for i, block in enumerate(p.ld):
            try:
                data = json.loads(block)
            except ValueError as e:
                errors.append(f"{where}: JSON-LD block {i + 1} is invalid ({e})")
                continue
            errors += [f"{where}: JSON-LD block {i + 1}: {msg}" for msg in schema_problems(data)]

        for ref in p.links + [i.get("src", "") for i in p.imgs]:
            r = resolve(site, name, ref)
            if r is None:
                continue
            target, frag = r
            if not target.exists():
                errors.append(f"{where}: link to {ref} points to a missing file")
            elif frag and target.suffix == ".html" and target.name in parsed and frag not in parsed[target.name].ids:
                errors.append(f"{where}: link to {ref} points to a missing #{frag}")

        robots = p.meta.get("robots", "")
        if not indexable:
            if "noindex" not in robots:
                errors.append(f"{where}: should carry <meta name=\"robots\" content=\"noindex\">")
            continue
        if "noindex" in robots:
            errors.append(f"{where}: indexable page is marked noindex")

        want = page_url(name)
        if p.canonical != want:
            errors.append(f"{where}: canonical is {p.canonical!r}, expected {want!r}")
        for key in REQUIRED_META:
            if not p.meta.get(key):
                errors.append(f"{where}: missing <meta {key}>")
        if p.meta.get("og:url") and p.meta["og:url"] != want:
            errors.append(f"{where}: og:url is {p.meta['og:url']!r}, expected {want!r}")

        og = p.meta.get("og:image", "")
        if og:
            img = site / og[len(BASE):] if og.startswith(BASE) else None
            if not img or not img.exists():
                errors.append(f"{where}: og:image {og} must be an absolute {BASE} URL to a file in site/")
            else:
                size = image_size(img)
                if size:
                    html = path.read_text(encoding="utf-8")
                    new = html
                    for key, val in (("og:image:width", size[0]), ("og:image:height", size[1])):
                        tag = f'<meta property="{key}" content="{val}">'
                        if re.search(rf'<meta property="{key}" content="[^"]*">', new):
                            new = re.sub(rf'<meta property="{key}" content="[^"]*">', tag, new)
                        else:
                            new = re.sub(r'(<meta property="og:image" content="[^"]*">)', rf"\1\n{tag}", new, count=1)
                    if new != html:
                        path.write_text(new, encoding="utf-8")
                        fixed.append((where, f"og:image size set to {size[0]}×{size[1]}"))

    # Sitemap: every indexable page listed, nothing stale, lastmod today for changed pages.
    sm_path = site / "sitemap.xml"
    sm = sm_path.read_text(encoding="utf-8")
    entries = dict(re.findall(r"<loc>([^<]+)</loc><lastmod>([^<]+)</lastmod>", sm))
    changed = set(git("diff", "HEAD", "--name-only", "--", "site", cwd=root).split())
    changed |= set(git("ls-files", "--others", "--exclude-standard", "--", "site", cwd=root).split())
    want_urls = {page_url(n): n for n in pages if n not in NOINDEX_PAGES}
    new_entries = {}
    for url, name in sorted(want_urls.items(), key=lambda kv: (kv[0] != BASE, kv[0])):
        lastmod = entries.get(url)
        if lastmod is None:
            fixed.append(("site/sitemap.xml", f"added {url}"))
            lastmod = today
        elif f"site/{name}" in changed and lastmod != today:
            fixed.append(("site/sitemap.xml", f"lastmod for {url} set to {today}"))
            lastmod = today
        new_entries[url] = lastmod
    for url in entries:
        if url not in want_urls:
            fixed.append(("site/sitemap.xml", f"removed {url} (no such indexable page)"))
    if list(new_entries.items()) != list(entries.items()):
        body = "".join(f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in new_entries.items())
        sm_path.write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                           f"{body}</urlset>\n", encoding="utf-8")

    # Titles and descriptions must be unique across indexable pages.
    for label, get in (("title", lambda p: p.title.strip()), ("meta description", lambda p: p.meta.get("description", ""))):
        seen = {}
        for name in pages:
            if name in NOINDEX_PAGES or not get(parsed[name]):
                continue
            seen.setdefault(get(parsed[name]), []).append(name)
        for names in seen.values():
            if len(names) > 1:
                errors.append(f"{', '.join('site/' + n for n in names)}: share the same {label}")

    for img in sorted(site.rglob("*")):
        if img.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif"} and img.stat().st_size > IMAGE_WARN_BYTES:
            warnings.append(f"{img.relative_to(root)}: {img.stat().st_size // 1000} KB (over {IMAGE_WARN_BYTES // 1000} KB; compress or resize)")

    llms = site / "llms.txt"
    if llms.exists():
        for url in re.findall(r"\]\((\S+?)\)", llms.read_text(encoding="utf-8")):
            if url.startswith(BASE) or not re.match(r"^[a-z]+:", url):
                r = resolve(site, "index.html", url)
                if r and not r[0].exists():
                    errors.append(f"site/llms.txt: link to {url} points to a missing file")

    robots_txt = (site / "robots.txt").read_text(encoding="utf-8") if (site / "robots.txt").exists() else ""
    if f"Sitemap: {BASE}sitemap.xml" not in robots_txt:
        errors.append(f"site/robots.txt: missing 'Sitemap: {BASE}sitemap.xml'")

    errors = list(dict.fromkeys(errors))
    touched = sorted({f for f, _ in fixed})
    if touched and not manual:
        subprocess.run(["git", "add", "--", *touched], cwd=root, check=False)

    lines = [f"{f}: {msg}" for f, msg in fixed] + [f"warning: {w}" for w in warnings]
    if errors:
        print("SEO check failed; fix these before committing:\n  " + "\n  ".join(errors)
              + ("\n" + "\n".join(lines) if lines else ""), file=sys.stderr)
        return 2
    if manual:
        print("\n".join(lines) or "SEO check passed.")
    elif lines:
        msg = "SEO hook: " + "; ".join(lines) + (" (fixes staged)" if touched else "")
        print(json.dumps({"systemMessage": msg,
                          "hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": msg}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
