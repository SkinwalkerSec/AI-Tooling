# References

Reading and tooling for function-calling security, improper output handling, excessive agency,
and vulnerable backend functions.

## Standards and taxonomies

- OWASP Top 10 for LLM Applications: `LLM01 Prompt Injection`, `LLM05 Improper Output
  Handling`, and `LLM06 Excessive Agency`
  https://genai.owasp.org/llm-top-10/
- OWASP LLM05:2025 Improper Output Handling
  https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/
- OWASP LLM06:2025 Excessive Agency
  https://genai.owasp.org/llmrisk/llm062025-excessive-agency/
- OWASP Top 10 for Agentic Applications: `ASI02 Tool Misuse and Exploitation` and `ASI05
  Unexpected Code Execution`
  https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/
- CWE-95: Improper Neutralization of Directives in Dynamically Evaluated Code (`eval` injection)
  https://cwe.mitre.org/data/definitions/95.html
- CWE-89: Improper Neutralization of Special Elements used in an SQL Command (SQL injection)
  https://cwe.mitre.org/data/definitions/89.html

## Function-calling guidance

- OpenAI function calling guide: structured function definitions, argument schemas, and strict
  schema adherence
  https://developers.openai.com/api/docs/guides/function-calling
- OpenAI safety best practices: constrain inputs, validate outputs, and retain human review for
  high-impact actions
  https://platform.openai.com/docs/guides/safety-best-practices
- Python documentation: `eval()` and `exec()` execute arbitrary code and must not receive
  untrusted input
  https://docs.python.org/3/library/functions.html#eval
- SQLite query language and built-in metadata interfaces
  https://www.sqlite.org/lang.html
  https://www.sqlite.org/pragma.html#pragma_table_info

## Defensive testing

- NVIDIA garak (LLM vulnerability scanner): https://github.com/NVIDIA/garak
- Microsoft PyRIT (Python Risk Identification Toolkit): https://github.com/Azure/PyRIT
- promptfoo (LLM eval and red-team harness): https://github.com/promptfoo/promptfoo
- OWASP Web Security Testing Guide, SQL injection testing:
  https://owasp.org/www-project-web-security-testing-guide/

