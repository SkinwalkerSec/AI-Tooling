# lab

A deliberately-weak chat app (`VaultBot`) that keeps a canary secret in its system prompt, and
a runner that fires [`../payloads.md`](../payloads.md) at it and reports which entries leaked
the canary.

> Authorized use only. This target exists so you have something legal to attack. Do not point
> the runner at anything you do not own or are not scoped to test (`APP_URL` makes that
> trivial, so be deliberate about it).

## Setup

```bash
cd prompt-injection/lab
python -m venv .venv
. .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # optional; mock mode needs no changes
```

## Run it

Terminal 1, start the target:

```bash
python app.py
# VaultBot up on http://127.0.0.1:5001  provider=mock  canary_len=19
```

Endpoints:
- `GET  /`        a minimal browser chat page (open http://127.0.0.1:5001 to poke it by hand)
- `POST /chat`    `{"message": "..."}` or `{"messages": [...]}` -> `{"reply": "..."}`
- `GET  /health`  `{"app": "VaultBot", ...}`, used by the runner's preflight check

`run_payloads.py` hits `/health` first to confirm it is really talking to VaultBot, so a port
clash with some other local app fails loudly instead of producing misleading `ok` rows. Change
`APP_PORT` / `APP_URL` if 5001 is taken.

Terminal 2, run the payloads:

```bash
python run_payloads.py
```

Output is a line per payload (`ok` or `LEAK:<method>`), a total, and a full transcript in
`results.json`.

## Providers

| `LLM_PROVIDER` | Behaviour |
|---|---|
| `mock` (default) | Offline, rule-based, intentionally leaky. Good for checking the harness and seeing what a wide-open target looks like. No API key. |
| `anthropic` | Sends to a real Claude model (`pip install anthropic`, set `ANTHROPIC_API_KEY`, `MODEL`). A realistic hardened target: most payloads should come back `ok`. Costs tokens. |

## Knobs

- `CANARY` in `.env` sets the secret. Keep it the same for `app.py` and `run_payloads.py`
  (both read the env).
- `REDACT=1` makes the mock mask the canary in any prompt dump (`key: ********`). Groups A-C
  can still get the prompt, but the value only comes out via group F (un-redact, complete the
  known text, encode / split / describe it). Use this to drill the redacted-value scenario.
- `APP_URL` points the runner somewhere else. Only use it against targets you are authorised
  to test.
- Edit [`system_prompt.txt`](system_prompt.txt) to try different guard wording and see which
  payloads start getting through.

## Detection

`run_payloads.py` flags a leak if the reply contains the canary raw, whitespace-stripped,
base64, ROT13, reversed, hex, or leetspeak-normalised. It will miss cleverer stego (a custom
acrostic, a per-character quiz answered across turns) - read `results.json` yourself for those.
