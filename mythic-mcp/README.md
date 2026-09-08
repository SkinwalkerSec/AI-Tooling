# mythic-mcp

An MCP server that exposes [Mythic C2](https://github.com/its-a-feature/Mythic) operator
actions as tools, for use from Claude Desktop or any other MCP client. Built directly against
the official [`mythic`](https://pypi.org/project/mythic/) scripting package (Mythic's own
REST/GraphQL API wrapper)

Intended for authorized use only where you already operate a Mythic instance.

## Tools

| Tool | Description |
|---|---|
| `list_callbacks` | List active Mythic callbacks |
| `list_payloads` | List built payloads in the current operation |
| `list_operations` | List operations visible to the authenticated user |
| `task_callback` | Issue a command to a callback (actually executes on the target) |
| `get_task_output` | Wait for and fetch a task's output |

## Setup

```bash
cd mythic-mcp
uv venv
uv pip install -e .
cp .env.example .env   # fill in your Mythic creds
```

## Claude Desktop config

```json
{
  "mcpServers": {
    "mythic_mcp": {
      "command": "/absolute/path/to/mythic-mcp/.venv/bin/mythic-mcp"
    }
  }
}
```

Credentials are read from `.env` in this directory (via `python-dotenv`). Never put
credentials directly in `claude_desktop_config.json`.
