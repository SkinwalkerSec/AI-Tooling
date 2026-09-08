# nmap-mcp

An MCP server that exposes nmap scans as tools, for use from Claude Desktop or any other MCP
client. Shells out to the real `nmap` binary (arguments passed as a list, never through a shell,
so nothing in a target string can inject extra flags) and parses its XML output into structured
results.

Intended for authorized engagements/labs only.

## Scope guard

If `NMAP_ALLOWED_CIDR` is set, every target (IP, hostname, or CIDR) is checked against it before
nmap ever runs, and hostnames are resolved and checked by their resolved address. Leave it unset
only for throwaway local labs where you don't need the guardrail.

## Tools

| Tool | Description |
|---|---|
| `host_discovery` | Ping sweep a range to see which hosts are up |
| `quick_scan` | Fast scan of the 100 most common ports (no root required) |
| `port_scan` | TCP connect scan with optional service/version detection and a custom port list |
| `os_detection` | OS fingerprinting (`-O`) -- needs nmap running with raw-socket privileges |

## Setup

```bash
cd nmap-mcp
uv venv
uv pip install -e .
cp .env.example .env   # set NMAP_ALLOWED_CIDR to your lab range
```

## Claude Desktop config

```json
{
  "mcpServers": {
    "nmap_mcp": {
      "command": "/absolute/path/to/nmap-mcp/.venv/bin/nmap-mcp"
    }
  }
}
```

`os_detection` needs nmap to run with raw-socket privileges. If Claude Desktop itself isn't
running as root, either grant the `nmap` binary `cap_net_raw` (`sudo setcap cap_net_raw+eip
$(which nmap)`) or skip that tool and rely on `port_scan` + `-sV` for fingerprinting instead.
