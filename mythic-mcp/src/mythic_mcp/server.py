"""
mythic-mcp: an MCP server exposing Mythic C2 operator actions as tools.

Talks to Mythic entirely through the official `mythic` scripting package
(https://pypi.org/project/mythic/), which wraps Mythic's REST/GraphQL API.
No credentials are ever hardcoded here -- everything comes from environment
variables (see .env.example), and connections are made lazily on first use.
"""

import asyncio
import os

import mythic
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

load_dotenv()

mcp = MCPServer("mythic-mcp")

_mythic_instance = None
_login_lock = asyncio.Lock()


def _env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(
            f"{name} is not set. Copy .env.example to .env, fill it in, "
            "and make sure your MCP client loads it (see README)."
        )
    return value


async def _get_mythic():
    """Lazily authenticate to Mythic and cache the session."""
    global _mythic_instance
    async with _login_lock:
        if _mythic_instance is None:
            _mythic_instance = await mythic.login(
                username=_env("MYTHIC_USERNAME"),
                password=_env("MYTHIC_PASSWORD"),
                server_ip=_env("MYTHIC_SERVER_IP", "localhost"),
                server_port=int(_env("MYTHIC_SERVER_PORT", "7443")),
                ssl=_env("MYTHIC_SSL", "true").lower() != "false",
                timeout=-1,
            )
    return _mythic_instance


@mcp.tool()
async def list_callbacks() -> list[dict]:
    """List all active Mythic callbacks (id, host, user, IP, integrity level, last checkin)."""
    m = await _get_mythic()
    callbacks = await mythic.get_all_active_callbacks(mythic=m)
    return [
        {
            "display_id": c.get("display_id"),
            "host": c.get("host"),
            "user": c.get("user"),
            "ip": c.get("ip"),
            "integrity_level": c.get("integrity_level"),
            "payload_type": c.get("payload_type", {}).get("ptype")
            if isinstance(c.get("payload_type"), dict)
            else c.get("payload_type"),
            "last_checkin": c.get("last_checkin"),
            "active": c.get("active"),
        }
        for c in callbacks
    ]


@mcp.tool()
async def list_payloads() -> list[dict]:
    """List all payloads built in the current Mythic operation."""
    m = await _get_mythic()
    payloads = await mythic.get_all_payloads(mythic=m)
    return [
        {
            "uuid": p.get("uuid"),
            "description": p.get("description"),
            "payload_type": p.get("payload_type", {}).get("ptype")
            if isinstance(p.get("payload_type"), dict)
            else p.get("payload_type"),
            "os": p.get("os"),
            "deleted": p.get("deleted"),
        }
        for p in payloads
    ]


@mcp.tool()
async def list_operations() -> list[dict]:
    """List Mythic operations visible to the authenticated user."""
    m = await _get_mythic()
    operations = await mythic.get_all_operations(mythic=m)
    return [
        {"id": o.get("id"), "name": o.get("name"), "complete": o.get("complete")}
        for o in operations
    ]


@mcp.tool()
async def task_callback(callback_display_id: int, command_name: str, parameters: str = "") -> dict:
    """
    Issue a task (command) to a specific Mythic callback.

    This actually executes the given command on the target through the
    callback -- only call it when you intend to run that command against
    that host.
    """
    m = await _get_mythic()
    task = await mythic.issue_task(
        mythic=m,
        command_name=command_name,
        parameters=parameters,
        callback_display_id=callback_display_id,
    )
    return {
        "task_display_id": task.get("display_id"),
        "status": task.get("status"),
        "command": command_name,
        "callback_display_id": callback_display_id,
    }


@mcp.tool()
async def get_task_output(task_display_id: int, timeout_seconds: int = 60) -> str:
    """Wait for and return the output of a previously issued Mythic task."""
    m = await _get_mythic()
    output = await mythic.waitfor_for_task_output(
        mythic=m,
        task_display_id=task_display_id,
        timeout=timeout_seconds,
    )
    if isinstance(output, bytes):
        return output.decode(errors="replace")
    return str(output)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
