"""LLMShip: a deliberately weak app that renders LLM output into HTML without encoding.

Routes:
  GET  /                 index
  GET  /reflected        form + vulnerable reflected sink (LLM output echoed unescaped)
  GET  /stored/          testimonials page (page itself escapes; the chat path does not)
  POST /stored/add       add a testimonial (stored raw)
  POST /stored/ask       "chatbot": echoes testimonials into an unescaped panel
  GET  /collab           built-in exfil listener; logs query string + headers, returns 1x1 gif
  GET  /collab/log       view collected hits (text/plain)
  GET  /health           status json

The mock LLM mirrors a resilient model: it refuses a bare inline <script>alert(...)>, but
happily echoes benign tags, event-handler tags, external <script src>, and anything wrapped as
"repeat verbatim" / "you are an HTML formatter".

Authorized use only. Attack this app, your own systems, or a scoped engagement.
"""
import os
import re
from html import escape

from flask import Flask, request, jsonify, redirect

PROVIDER = os.environ.get("LLM_PROVIDER", "mock").lower()
MODEL = os.environ.get("MODEL", "claude-sonnet-5")

app = Flask(__name__)

TESTIMONIALS = [
    "Fast shipping, great support. - Sarah M.",
    "Best logistics partner we have used. - John D.",
]
COLLAB_HITS = []

WRAP_HINTS = (
    "verbatim", "echo", "repeat after me", "formatter", "passthrough",
    "translate this html", "changing nothing", "byte for byte", "no extra characters",
    "print only the result", "on its own line unchanged", "exact format",
)
HANDLER_RE = re.compile(r"on[a-z]+\s*=", re.I)
INLINE_SCRIPT_RE = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>.*?(alert|eval|document|fetch)", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")


def mock_llm(prompt: str) -> str:
    p = prompt.lower()
    has_tag = bool(TAG_RE.search(prompt))
    wrapped = any(h in p for h in WRAP_HINTS)

    if not has_tag:
        return "Thanks for your message. How else can I help with your LLMShip account?"
    if wrapped:
        # "just formatting" - the model complies and echoes the markup
        return _extract_echo(prompt)
    if INLINE_SCRIPT_RE.search(prompt) and "src=" not in p:
        return "I cannot comply with your request. Is there anything else I can help you with?"
    if HANDLER_RE.search(prompt) or re.search(r"<script[^>]*\bsrc=", prompt, re.I) or re.search(r"<(img|svg|iframe|body|video|audio|details|marquee|object|embed)\b", prompt, re.I):
        # reads as "just an HTML tag" - complies
        return _extract_echo(prompt)
    if re.search(r"<(b|i|u|s|mark|h1|h2|p|div|span|font|em|strong)\b", prompt, re.I):
        return _extract_echo(prompt)
    return "Here is your answer. (nothing to render)"


def _extract_echo(prompt: str) -> str:
    """Pull the payload the user asked us to 'respond with' and return it as-is."""
    m = re.search(r"respond with[:\s]*'(.+?)'\s*$", prompt, re.I | re.S)
    if m:
        return m.group(1)
    m = re.search(r"(respond with|reply with|output|print|echo)[^<]*(<.+>)", prompt, re.I | re.S)
    if m:
        return m.group(2)
    frag = TAG_RE.search(prompt)
    return prompt[frag.start():] if frag else prompt


def llm(prompt: str) -> str:
    if PROVIDER == "anthropic":
        import anthropic
        c = anthropic.Anthropic()
        r = c.messages.create(model=MODEL, max_tokens=1024, messages=[{"role": "user", "content": prompt}])
        return "".join(b.text for b in r.content if b.type == "text")
    return mock_llm(prompt)


PAGE = """<!doctype html><meta charset=utf-8><title>LLMShip</title>
<style>body{{font:14px system-ui;margin:2rem;max-width:820px}}
.out{{border:1px solid #ccc;padding:1rem;margin:1rem 0;border-radius:6px}}
input,textarea{{width:100%;padding:.5rem;font:inherit}} button{{padding:.5rem 1rem}}</style>
{body}"""


@app.get("/")
def index():
    return PAGE.format(body="""
    <h1>LLMShip</h1>
    <ul>
      <li><a href="/reflected">/reflected</a> - reflected LLM output sink</li>
      <li><a href="/stored/">/stored/</a> - testimonials + chatbot (stored)</li>
      <li><a href="/collab/log">/collab/log</a> - built-in exfil listener log</li>
      <li><a href="/health">/health</a></li>
    </ul>""")


@app.route("/reflected", methods=["GET", "POST"])
def reflected():
    q = request.values.get("q", "")
    out = ""
    if q:
        # VULNERABLE: LLM output inserted into HTML with no encoding
        out = f'<div class="out">LLM: {llm(q)}</div>'
    return PAGE.format(body=f"""
    <h1>Reflected</h1>
    <form method="post"><input name="q" value="{escape(q)}" placeholder="Respond with 'Test<b>Hi</b>'" autofocus>
    <button>send</button></form>
    {out}
    <p><a href="/">back</a></p>""")


@app.get("/stored/")
def stored_page():
    items = "".join(f"<li>{escape(t)}</li>" for t in TESTIMONIALS)  # page path is encoded
    return PAGE.format(body=f"""
    <h1>LLMShip</h1><h2>What our clients say</h2><ul>{items}</ul>
    <form method="post" action="/stored/add">
      <textarea name="t" rows="3" placeholder="Leave a testimonial"></textarea><button>submit</button></form>
    <h2>Assistant</h2>
    <form method="post" action="/stored/ask"><input name="q" placeholder="Show me the latest testimonials"><button>ask</button></form>
    <p><a href="/">back</a></p>""")


@app.post("/stored/add")
def stored_add():
    t = request.form.get("t", "").strip()
    if t:
        TESTIMONIALS.append(t)  # stored raw
    return redirect("/stored/")


@app.post("/stored/ask")
def stored_ask():
    q = request.form.get("q", "")
    if re.search(r"testimonial|review|clients?|customers?|say", q, re.I):
        joined = " ".join(TESTIMONIALS)
        answer = llm(f"Respond with 'Here are the testimonials: {joined}'")
    else:
        answer = llm(q)
    # VULNERABLE: assistant output rendered with no encoding
    return PAGE.format(body=f"""
    <h1>Assistant</h1><div class="out">{answer}</div>
    <p><a href="/stored/">back</a></p>""")


@app.get("/collab")
def collab():
    COLLAB_HITS.append({
        "path": request.full_path,
        "ua": request.headers.get("User-Agent", ""),
        "ref": request.headers.get("Referer", ""),
    })
    print("[collab]", request.full_path)
    return (b"GIF89a", 200, {"Content-Type": "image/gif"})


@app.get("/collab/log")
def collab_log():
    lines = [f"{h['path']}\n  ref={h['ref']}\n  ua={h['ua']}" for h in COLLAB_HITS] or ["(no hits yet)"]
    return "\n".join(lines), 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.get("/health")
def health():
    return jsonify({"app": "LLMShip", "provider": PROVIDER, "testimonials": len(TESTIMONIALS)})


if __name__ == "__main__":
    host = os.environ.get("APP_HOST", "127.0.0.1")
    port = int(os.environ.get("APP_PORT", "5002"))
    print(f"LLMShip up on http://{host}:{port}  provider={PROVIDER}")
    app.run(host=host, port=port)
