"""Turn Google Form responses into recipe pages.

Reads the form's response sheet (published to the web as CSV) and writes one
Markdown file per new response into _recipes/. Responses already imported are
listed in scripts/imported.txt, so deleting a recipe file won't bring it back.

Usage:
    FORM_CSV_URL=https://docs.google.com/.../pub?output=csv python scripts/import_form.py
    python scripts/import_form.py path/to/responses.csv
"""

import csv
import html
import io
import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECIPES = ROOT / "_recipes"
LEDGER = Path(__file__).resolve().parent / "imported.txt"

# Form question text -> field. Matching is case-insensitive "contains".
FIELDS = {
    "title": ["recipe name", "name of the recipe", "recipe title", "title"],
    "author": ["your name", "submitted by", "who"],
    "category": ["category", "type of dish", "course"],
    "servings": ["serves", "servings"],
    "prep_time": ["prep"],
    "cook_time": ["cook time", "cooking time", "bake time"],
    "ingredients": ["ingredient"],
    "instructions": ["instruction", "directions", "steps", "method"],
    "notes": ["note", "story", "tips"],
    "photo": ["photo", "picture", "image"],
}


def load_rows(source):
    if source.startswith("http"):
        with urllib.request.urlopen(source, timeout=30) as resp:
            text = resp.read().decode("utf-8-sig")
    else:
        text = Path(source).read_text(encoding="utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def map_headers(headers):
    mapping = {}
    for field, keys in FIELDS.items():
        for h in headers:
            hl = h.lower()
            if h not in mapping.values() and any(k in hl for k in keys):
                mapping[field] = h
                break
    return mapping


def clean(text):
    # Escape HTML so nothing typed into the form can run on the site,
    # and neutralise Liquid tags so Jekyll doesn't try to interpret them.
    text = html.escape((text or "").strip(), quote=False)
    return text.replace("{%", "{ %").replace("{{", "{ {")


def lines(text):
    out = []
    for line in clean(text).splitlines():
        line = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip()
        if line:
            out.append(line)
    return out


def photo_url(url):
    url = (url or "").strip()
    if not url.startswith("http"):
        return ""
    # Google Drive share links -> directly embeddable image
    m = re.search(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?.*id=)([\w-]+)", url)
    if m:
        return f"https://lh3.googleusercontent.com/d/{m.group(1)}"
    return url


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "recipe"


def parse_date(ts):
    for fmt in ("%m/%d/%Y %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(ts, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return datetime.now().strftime("%Y-%m-%d")


def build(row, m):
    get = lambda f: (row.get(m[f], "") if f in m else "").strip()
    title = get("title")
    front = {
        "title": title,
        "author": get("author"),
        "category": get("category"),
        "servings": get("servings"),
        "prep_time": get("prep_time"),
        "cook_time": get("cook_time"),
        "photo": photo_url(get("photo")),
        "date": parse_date(row.get("Timestamp", "")),
    }
    fm = "\n".join(
        f"{k}: {json.dumps(clean(v).replace('\"', '%22' if k == 'photo' else '&quot;'), ensure_ascii=False)}"
        for k, v in front.items() if v
    )
    body = []
    ing = lines(get("ingredients"))
    if ing:
        body += ["## Ingredients", ""] + [f"- {i}" for i in ing] + [""]
    steps = lines(get("instructions"))
    if steps:
        body += ["## Instructions", ""] + [f"{n}. {s}" for n, s in enumerate(steps, 1)] + [""]
    notes = clean(get("notes"))
    if notes:
        body += ["## Notes", "", notes, ""]
    return title, f"---\n{fm}\n---\n\n" + "\n".join(body)


def main():
    source = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("FORM_CSV_URL", "")
    if not source:
        print("No FORM_CSV_URL set; nothing to import.")
        return
    rows = load_rows(source)
    if not rows:
        print("No responses yet.")
        return
    m = map_headers(rows[0].keys())
    if "title" not in m:
        sys.exit(f"Couldn't find a recipe-name question. Columns: {list(rows[0].keys())}")

    done = set(LEDGER.read_text(encoding="utf-8").splitlines()) if LEDGER.exists() else set()
    RECIPES.mkdir(exist_ok=True)
    added = 0
    for row in rows:
        key = f"{row.get('Timestamp', '')}|{row.get(m['title'], '').strip()}"
        if key in done or not row.get(m["title"], "").strip():
            continue
        title, content = build(row, m)
        base = slugify(title)
        path, n = RECIPES / f"{base}.md", 2
        while path.exists():
            path, n = RECIPES / f"{base}-{n}.md", n + 1
        path.write_text(content, encoding="utf-8")
        done.add(key)
        added += 1
        print(f"Added {path.name}")

    LEDGER.write_text("\n".join(sorted(done)) + "\n", encoding="utf-8")
    print(f"{added} new recipe(s).")


if __name__ == "__main__":
    main()
