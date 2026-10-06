"""Shared helpers for the SEO skill scripts. Python stdlib only."""
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://nicholasdesouza.com/"
ROOT = Path(__file__).resolve().parents[4]
SITE = ROOT / "site"
UA = "Mozilla/5.0 (compatible; portfolio-seo-skill/1.0)"


class Fetch:
    """Result of one HTTP request: status (None on failure), headers, body, error."""

    def __init__(self, url, status=None, headers=None, body=b"", error=None):
        self.url, self.status, self.headers, self.body, self.error = url, status, headers or {}, body, error

    @property
    def limited(self):
        """True when the failure is this environment (proxy, DNS, rate limit), not the site."""
        return (self.status is None or self.status == 429 or "x-deny-reason" in self.headers
                or "Tunnel connection failed" in (self.error or ""))

    def text(self):
        return self.body.decode("utf-8", "replace")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def fetch(url, method="GET", data=None, headers=None, timeout=20):
    """One request, no redirect following."""
    body = json.dumps(data).encode() if isinstance(data, (dict, list)) else data
    h = {"User-Agent": UA, **({"Content-Type": "application/json"} if body else {}), **(headers or {})}
    req = urllib.request.Request(url, data=body, method=method, headers=h)
    try:
        with _opener.open(req, timeout=timeout) as r:
            return Fetch(url, r.status, {k.lower(): v for k, v in r.headers.items()}, r.read())
    except urllib.error.HTTPError as e:
        return Fetch(url, e.code, {k.lower(): v for k, v in e.headers.items()}, e.read() or b"", str(e))
    except Exception as e:  # DNS, TLS, proxy refusal, timeout
        return Fetch(url, None, error=str(e))


def fetch_chain(url, limit=10):
    """Follow redirects by hand. Returns the list of Fetch hops; the last is the final response."""
    hops = []
    for _ in range(limit):
        f = fetch(url)
        hops.append(f)
        if f.status not in (301, 302, 303, 307, 308) or "location" not in f.headers:
            break
        url = urllib.parse.urljoin(url, f.headers["location"])
    return hops


def get_json(url, data=None, method=None):
    f = fetch(url, method=method or ("POST" if data is not None else "GET"), data=data)
    try:
        return f, json.loads(f.body) if f.body else None
    except ValueError:
        return f, None


class PageMeta(HTMLParser):
    """Everything SEO-relevant in one HTML document."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self.meta, self.canonical = "", {}, None
        self.headings, self.links, self.imgs, self.ld = [], [], [], []
        self.lang = None
        self._stack, self._text, self._skip = [], [], 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "meta" and (a.get("property") or a.get("name")):
            self.meta[a.get("property") or a.get("name")] = a.get("content", "")
        elif tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "img":
            self.imgs.append(a)
        if tag == "br" and self._stack:
            self._stack[-1][1] += " "
        if tag in ("title", "h1", "h2", "h3"):
            self._stack.append([tag, ""])
        if tag in ("script", "style", "svg"):
            self._skip += 1
            if tag == "script" and a.get("type") == "application/ld+json":
                self._stack.append(["ld", ""])

    def handle_endtag(self, tag):
        if tag in ("script", "style", "svg"):
            self._skip = max(0, self._skip - 1)
        want = "ld" if tag == "script" else tag
        if self._stack and self._stack[-1][0] == want:
            kind, text = self._stack.pop()
            if kind == "title":
                self.title = text.strip()
            elif kind == "ld":
                self.ld.append(text)
            else:
                self.headings.append((kind, " ".join(text.split())))

    def handle_data(self, data):
        if self._stack:
            self._stack[-1][1] += data
        if not self._skip:
            self._text.append(data)

    @property
    def words(self):
        return len(re.findall(r"\w+", " ".join(self._text)))

    def schema_types(self):
        types = []

        def walk(v):
            if isinstance(v, list):
                for i in v:
                    walk(i)
            elif isinstance(v, dict):
                t = v.get("@type")
                if t:
                    types.extend([t] if isinstance(t, str) else t)
                for x in v.values():
                    walk(x)

        for block in self.ld:
            try:
                walk(json.loads(block))
            except ValueError:
                types.append("(invalid JSON-LD)")
        return types


def parse(html):
    p = PageMeta()
    p.feed(html)
    return p


def local_pages():
    """{filename: PageMeta} for every page in site/."""
    return {f.name: parse(f.read_text(encoding="utf-8")) for f in sorted(SITE.glob("*.html"))}


def page_url(name):
    return BASE if name == "index.html" else BASE + name


def emit(data, as_json, render):
    """Print JSON or a human-readable rendering."""
    print(json.dumps(data, indent=2, ensure_ascii=False) if as_json else render(data))
