"""ابزارهای کمکی PDF برای build.cjs (نیازمند pymupdf).

  python3 pdftools.py markers <pdf>          → JSON: {"L01": 5, ...}
  python3 pdftools.py preview <pdf> <outdir> → تصویر PNG هر صفحه
"""
import json
import os
import re
import sys

import pymupdf as fitz

fitz.TOOLS.mupdf_display_errors(False)
fitz.TOOLS.mupdf_display_warnings(False)


def markers(pdf):
    found = {}
    with fitz.open(pdf) as doc:
        for i, page in enumerate(doc):
            for m in re.findall(r"@@([A-Za-z0-9_-]+)@@", page.get_text()):
                found.setdefault(m, i + 1)
    print(json.dumps(found))


def preview(pdf, outdir):
    os.makedirs(outdir, exist_ok=True)
    for f in os.listdir(outdir):
        if f.endswith(".png"):
            os.remove(os.path.join(outdir, f))
    with fitz.open(pdf) as doc:
        for i, page in enumerate(doc):
            page.get_pixmap(dpi=int(os.environ.get("DPI", 80))).save(os.path.join(outdir, f"p{i + 1:03d}.png"))
        print(f"{len(doc)} pages → {outdir}")


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    {"markers": markers, "preview": preview}[cmd](*args)
