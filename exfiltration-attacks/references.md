# References

Reading and tooling for LLM data-exfiltration: the insecure-output-handling sink, prompt-injection
delivery, and the Markdown / rendering behaviour that makes the beacon fire.

## Standards and taxonomies

- OWASP Top 10 for LLM Applications: `LLM01 Prompt Injection` and `LLM02 Insecure Output Handling`
  https://genai.owasp.org/llm-top-10/
- OWASP LLM02:2025 Insecure Output Handling
  https://genai.owasp.org/llmrisk/llm022025-insecure-output-handling/
- OWASP LLM01:2025 Prompt Injection
  https://genai.owasp.org/llmrisk/llm012025-prompt-injection/
- OWASP Top 10 for Agentic Applications: tool misuse and unexpected outbound actions
  https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/
- CWE-200: Exposure of Sensitive Information to an Unauthorized Actor
  https://cwe.mitre.org/data/definitions/200.html

## Markdown, images, and rendering

- Johann Rehberger, "Embrace the Red": Markdown image and data-exfiltration writeups for LLM apps
  https://embracethered.com/blog/
- CommonMark image syntax (`![alt](url)`)
  https://spec.commonmark.org/current/#images
- MDN, Content-Security-Policy `img-src` (limit where images may load from)
  https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/img-src
- MDN, Content-Security-Policy `connect-src`
  https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/connect-src

## Defensive testing

- NVIDIA garak (LLM vulnerability scanner): https://github.com/NVIDIA/garak
- Microsoft PyRIT (Python Risk Identification Toolkit): https://github.com/Azure/PyRIT
- promptfoo (LLM eval and red-team harness): https://github.com/promptfoo/promptfoo
- Interactsh (out-of-band interaction listener): https://github.com/projectdiscovery/interactsh
- `python3 -m http.server` for a quick beacon host and request log

## Related material in this repo

- [`../prompt-injection/`](../prompt-injection/): how the payload reaches the victim (direct and
  indirect prompt injection).
- [`../insecure-output/`](../insecure-output/): the same LLM02 class, including script-based exfil
  and Markdown-image exfil scenarios.
