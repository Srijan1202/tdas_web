"""Inject the extracted data into the page template.

    python build_site.py   (run from the site folder's build/ directory)

Writes ../index.html (published page body; the publishing host adds the document skeleton)
and ../standalone.html (the same page wrapped in a full HTML document, to open from disk).
"""
import os

here = os.path.dirname(os.path.abspath(__file__))
tpl = open(os.path.join(here, "template.html"), encoding="utf-8").read()
data = open(os.path.join(here, "site_data.json"), encoding="utf-8").read()
assert tpl.count("__DATA__") == 1
page = tpl.replace("__DATA__", data)
root = os.path.dirname(here)
open(os.path.join(root, "index.html"), "w", encoding="utf-8", newline="\n").write(page)
head, sep, body = page.partition("</style>")
standalone = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
              "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
              + head + sep + "\n</head>\n<body>\n" + body + "\n</body>\n</html>\n")
open(os.path.join(root, "standalone.html"), "w", encoding="utf-8", newline="\n").write(standalone)
print("wrote index.html", len(page), "bytes and standalone.html")
