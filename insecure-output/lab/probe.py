"""Fire the tag payloads from ../payloads.md at LLMShip's reflected sink and report which
ones came back rendered unescaped (i.e. a working XSS) vs encoded vs refused.

Usage:
  python probe.py                       # uses ../payloads.md and $APP_URL
  python probe.py path/to/payloads.md
  APP_URL=http://127.0.0.1:5002 python probe.py

For each "- " bullet that contains an HTML tag, the first <...> run is taken as the payload,
sent as  Respond with '<payload>'  , and the reflected HTML is checked:
  RENDERED  the raw tag is present unescaped   -> XSS
  encoded   only the &lt;...&gt; form is present
  refused   the mock declined
  other     no clear signal

Authorized use only. Default target is the bundled lab.
"""
import json
import os
import pathlib
import re
import sys
from html import escape

import requests

APP_URL = os.environ.get("APP_URL", "http://127.0.0.1:5002").rstrip("/")
PAYLOADS = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).parent.parent / "payloads.md"
# grab a full <script>...</script> when present, otherwise a single tag
TAG_RE = re.compile(r"<script\b[\s\S]*?</script>|<[^>\n]+>", re.I)


def preflight():
    try:
        info = requests.get(f"{APP_URL}/health", timeout=5).json()
    except Exception as e:  # noqa: BLE001
        sys.exit(f"cannot reach {APP_URL}/health ({e}). Start app.py or set APP_URL.")
    if info.get("app") != "LLMShip":
        sys.exit(f"{APP_URL} is not LLMShip (got {info!r}). Set APP_URL / APP_PORT.")


def parse(path: pathlib.Path):
    group = technique = "(none)"
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            group = line[3:].strip()
        elif line.startswith("### "):
            technique = line[4:].strip()
        elif line.startswith("- "):
            m = TAG_RE.search(line)
            if m:
                yield group, technique, m.group(0), line[2:].strip()


OUT_RE = re.compile(r'<div class="out">(.*?)</div>', re.S)


def classify(payload_tag: str, page: str):
    # look only at the LLM output panel, not the whole page (the form echoes the query escaped)
    m = OUT_RE.search(page)
    sink = m.group(1) if m else ""
    if payload_tag in sink:
        return "RENDERED"
    if "cannot comply" in sink.lower():
        return "refused"
    if escape(payload_tag) in sink or payload_tag.replace("<", "&lt;") in sink:
        return "encoded"
    return "other"


def main():
    print(f"target : {APP_URL}/reflected")
    print(f"file   : {PAYLOADS}")
    preflight()
    print("-" * 78)
    results, rendered = [], 0
    for i, (group, technique, tag, bullet) in enumerate(parse(PAYLOADS), 1):
        try:
            r = requests.post(f"{APP_URL}/reflected", data={"q": f"Respond with '{tag}'"}, timeout=30)
            verdict = classify(tag, r.text)
        except Exception as e:  # noqa: BLE001
            verdict = f"ERR {e}"
        if verdict == "RENDERED":
            rendered += 1
        label = technique if technique != "(none)" else group
        print(f"{i:>3}  {verdict:<9}  [{label[:26]:<26}]  {tag[:38]}")
        results.append({"n": i, "group": group, "technique": technique, "tag": tag, "verdict": verdict})
    print("-" * 78)
    print(f"{rendered}/{len(results)} payloads rendered unescaped (working XSS)")
    out = pathlib.Path(__file__).parent / "results.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"details written to {out}")


if __name__ == "__main__":
    main()
