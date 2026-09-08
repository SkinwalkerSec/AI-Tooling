# bloodhound-mcp

An MCP server that exposes [BloodHound](https://github.com/SpecterOps/BloodHound)'s Neo4j
attack-path graph as tools, for use from Claude Desktop or any other MCP client. Built directly
against the official [`neo4j`](https://pypi.org/project/neo4j) 

Intended for authorised use only where you already run BloodHound against collected
data.

## Tools

| Tool | Description |
|---|---|
| `run_cypher` | Ad-hoc read-only Cypher query (write keywords are rejected) |
| `shortest_paths_to_domain_admins` | Shortest attack paths to a domain's Domain Admins group |
| `kerberoastable_users` | Enabled users with an SPN set |
| `unconstrained_delegation_computers` | Computers with unconstrained Kerberos delegation |
| `owned_principals` | Principals currently marked owned |
| `mark_principal_owned` | Mark a principal owned (the one write tool, explicit and separate) |

## Setup

```bash
cd bloodhound-mcp
uv venv
uv pip install -e .
cp .env.example .env   # fill in your Neo4j creds
```

## Claude Desktop config

```json
{
  "mcpServers": {
    "bloodhound_mcp": {
      "command": "/absolute/path/to/bloodhound-mcp/.venv/bin/bloodhound-mcp"
    }
  }
}
```

Credentials are read from `.env` in this directory (via `python-dotenv`). Never put
credentials directly in `claude_desktop_config.json`.
