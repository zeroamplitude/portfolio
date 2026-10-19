#!/usr/bin/env python3
"""Preview the site locally the way GitHub Pages serves it.

  python3 tools/serve.py [port]     # default 8000; serves site/

Like GitHub Pages, /x serves x.html when it exists (the case studies use
extensionless URLs such as /case-studies/holdline), and /dir/ serves dir/index.html.
"""
import functools
import http.server
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        local = Path(super().translate_path(path))
        clean = path.split("?", 1)[0].split("#", 1)[0]
        if not clean.endswith("/") and local.suffix == "" and local.with_name(local.name + ".html").is_file():
            return str(local.with_name(local.name + ".html"))
        return str(local)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    handler = functools.partial(Handler, directory=str(SITE))
    print(f"Serving site/ at http://localhost:{port}/")
    http.server.ThreadingHTTPServer(("", port), handler).serve_forever()
