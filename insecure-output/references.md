# References

## Standards

- OWASP Top 10 for LLM Applications: `LLM02 Insecure Output Handling`
  https://genai.owasp.org/llm-top-10/
- OWASP XSS: https://owasp.org/www-community/attacks/xss/
- OWASP Cheat Sheets: XSS Prevention, DOM XSS Prevention, Content Security Policy
  https://cheatsheetseries.owasp.org/

## Payload collections

- PortSwigger XSS cheat sheet: https://portswigger.net/web-security/cross-site-scripting/cheat-sheet
- PayloadsAllTheThings, XSS Injection:
  https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/XSS%20Injection
- HTML sanitiser bypass / mutation XSS notes: https://research.securitum.com/dompurify-bypass/

## SQL injection (for `sqli.md`)

- PortSwigger SQL injection cheat sheet (per-engine syntax):
  https://portswigger.net/web-security/sql-injection/cheat-sheet
- PayloadsAllTheThings, SQL Injection (SQLite / MySQL / PostgreSQL / MSSQL / Oracle):
  https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/SQL%20Injection
- SQLite system catalog: `sqlite_master`, `PRAGMA table_info()` —
  https://www.sqlite.org/schematab.html

## Command injection (for `code_injection.md`)

- PayloadsAllTheThings, Command Injection (separators, filter bypasses, blind/OOB):
  https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Command%20Injection
- OWASP Command Injection: https://owasp.org/www-community/attacks/Command_Injection
- PortSwigger OS command injection:
  https://portswigger.net/web-security/os-command-injection
- Reverse-shell one-liners (payload reference): https://www.revshells.com/

## LLM-specific

- PortSwigger Web LLM attacks (insecure output handling section):
  https://portswigger.net/web-security/llm-attacks
- Markdown image / data exfiltration writeups (Johann Rehberger, "Embrace the Red"):
  https://embracethered.com/blog/

## Tooling

- Interactsh (OOB interaction listener): https://github.com/projectdiscovery/interactsh
- XSS Hunter style collectors; Burp Suite Collaborator
- `python3 -m http.server` for a quick payload host and hit log
- DOMPurify (to understand what a sanitiser does and does not stop):
  https://github.com/cure53/DOMPurify
