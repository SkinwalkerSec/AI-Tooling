# AI-Tooling

Red-team tooling and reference material for AI systems.

## MCP servers

Original MCP servers, written from scratch against each tool's official API/driver:

- [`mythic-mcp/`](mythic-mcp/): operator actions against a [Mythic C2](https://github.com/its-a-feature/Mythic) server
- [`bloodhound-mcp/`](bloodhound-mcp/): attack-path queries against a [BloodHound](https://github.com/SpecterOps/BloodHound) Neo4j database
- [`nmap-mcp/`](nmap-mcp/): host discovery and port/service scans via nmap, with a scope guard

Each is an independent Python project with its own `pyproject.toml`, README, and `.env.example`.

## Reference material

- [`prompt-injection/`](prompt-injection/): a taxonomy of system-prompt / secret-extraction
  techniques (OWASP LLM07), a payload list, and a deliberately-vulnerable practice app with a
  runner that reports which payloads leaked its canary secret.
- [`insecure-output/`](insecure-output/): bugs from LLM output used without sanitisation
  (OWASP LLM02) — XSS from output rendered into HTML, SQL injection from output flowing into a
  query ([`sqli.md`](insecure-output/sqli.md)), and OS command injection from output flowing
  into a shell ([`code_injection.md`](insecure-output/code_injection.md)). Payloads, worked
  reflected/stored scenarios, and a practice app (LLMShip) with a built-in exfil listener and a
  probe script.

## Authorized use only

Everything here is for lab environments, CTFs, and engagements where you already have
permission to operate against the targets and instances involved.
