# References

Reading and tooling for system-prompt extraction and prompt injection.

## Standards and taxonomies

- OWASP Top 10 for LLM Applications: `LLM01 Prompt Injection`, `LLM07 System Prompt Leakage`
  https://genai.owasp.org/llm-top-10/
- MITRE ATLAS (adversarial ML tactics and techniques)
  https://atlas.mitre.org/

## Papers

- Schulhoff et al., "Ignore This Title and HackAPrompt: Exposing Systemic Vulnerabilities of
  LLMs Through a Global Prompt Hacking Competition" (2023)
- Greshake et al., "Not what you've signed up for: Compromising Real-World LLM-Integrated
  Applications with Indirect Prompt Injection" (2023)
- Perez and Ribeiro, "Ignore Previous Prompt: Attack Techniques For Language Models" (2022)
- Zou et al., "Universal and Transferable Adversarial Attacks on Aligned Language Models"
  (GCG suffixes, 2023)
- Chao et al., "Jailbreaking Black Box Large Language Models in Twenty Queries" (PAIR, 2023)
- Anil et al., "Many-shot Jailbreaking" (Anthropic, 2024)
- Russinovich et al., "Great, Now Write an Article About That: The Crescendo Multi-Turn
  Jailbreak" (Microsoft, 2024)

## Practice

- Lakera Gandalf: https://gandalf.lakera.ai/
- GPT Prompt Attack / "system prompt leak" challenge collections
- HackAPrompt playground and dataset

## Tooling

- NVIDIA garak (LLM vulnerability scanner): https://github.com/NVIDIA/garak
- Microsoft PyRIT (Python Risk Identification Toolkit): https://github.com/Azure/PyRIT
- promptmap (prompt injection tester): https://github.com/utkusen/promptmap
- promptfoo (eval and red-team harness): https://github.com/promptfoo/promptfoo

## Commentary

- Simon Willison, prompt injection series: https://simonwillison.net/tags/prompt-injection/
- learnprompting.org, Prompt Hacking section: https://learnprompting.org/docs/prompt_hacking/introduction
