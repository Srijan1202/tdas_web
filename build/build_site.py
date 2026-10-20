"""Inject the extracted data into the page template.

    python build_site.py   (run from the site folder's build/ directory)

Writes ../index.html (the complete document served by Vercel)
and ../standalone.html (the same document, to open from disk).
"""
import os

here = os.path.dirname(os.path.abspath(__file__))
tpl = open(os.path.join(here, "template.html"), encoding="utf-8").read()
data = open(os.path.join(here, "site_data.json"), encoding="utf-8").read()
assert tpl.count("__DATA__") == 1
page = tpl.replace("__DATA__", data)
root = os.path.dirname(here)
head, sep, body = page.partition("</style>")
document = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
            + head + sep + "\n</head>\n<body>\n" + body + "\n</body>\n</html>\n")
open(os.path.join(root, "index.html"), "w", encoding="utf-8", newline="\n").write(document)
standalone = document
open(os.path.join(root, "standalone.html"), "w", encoding="utf-8", newline="\n").write(standalone)
print("wrote index.html", len(document), "bytes and standalone.html")
