"""
nmap-mcp: an MCP server exposing nmap scans as tools.

Shells out to the real `nmap` binary (no shell=True, arguments passed as a
list, so nothing in a target/port string can inject extra flags) and parses
its XML output into structured results.

Scope is enforced: if NMAP_ALLOWED_CIDR is set, every target is checked
against it before nmap ever runs. Hostnames are resolved and the resolved
IP is checked. Leave NMAP_ALLOWED_CIDR unset only for throwaway local labs
where you don't need the guardrail.
"""

import asyncio
import ipaddress
import os
import socket
import xml.etree.ElementTree as ET

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

load_dotenv()

mcp = MCPServer("nmap-mcp")

DEFAULT_TIMEOUT_SECONDS = 300


def _allowed_networks() -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    raw = os.environ.get("NMAP_ALLOWED_CIDR", "").strip()
    if not raw:
        return []
    return [ipaddress.ip_network(cidr.strip(), strict=False) for cidr in raw.split(",")]


def _resolve(target: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    try:
        return ipaddress.ip_address(target)
    except ValueError:
        pass
    try:
        return ipaddress.ip_address(socket.gethostbyname(target))
    except (socket.gaierror, ValueError) as exc:
        raise ValueError(f"Could not resolve target {target!r}: {exc}") from exc


def _check_scope(target: str) -> None:
    """Raise if target falls outside NMAP_ALLOWED_CIDR (when that's set)."""
    networks = _allowed_networks()
    if not networks:
        return

    try:
        # A bare CIDR/single-IP target, e.g. "10.10.10.0/24" or "10.10.10.5".
        candidate = ipaddress.ip_network(target, strict=False)
    except ValueError:
        # Not an IP/CIDR literal -- resolve it as a hostname instead.
        addr = _resolve(target)
        in_scope = any(addr in net for net in networks)
    else:
        if candidate.num_addresses == 1:
            in_scope = any(candidate.network_address in net for net in networks)
        else:
            in_scope = any(candidate.subnet_of(net) for net in networks)

    if not in_scope:
        allowed = ", ".join(str(n) for n in networks)
        raise ValueError(
            f"{target!r} is outside the configured scan scope (NMAP_ALLOWED_CIDR={allowed})"
        )


async def _run_nmap(args: list[str], timeout: int = DEFAULT_TIMEOUT_SECONDS) -> ET.Element:
    proc = await asyncio.create_subprocess_exec(
        "nmap",
        *args,
        "-oX",
        "-",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise TimeoutError(f"nmap did not finish within {timeout}s")

    if proc.returncode != 0:
        raise RuntimeError(f"nmap exited {proc.returncode}: {stderr.decode(errors='replace').strip()}")

    return ET.fromstring(stdout)


def _parse_hosts(root: ET.Element) -> list[dict]:
    hosts = []
    for host_el in root.findall("host"):
        status = host_el.find("status")
        if status is not None and status.get("state") != "up":
            continue

        addresses = [
            {"addr": a.get("addr"), "type": a.get("addrtype")}
            for a in host_el.findall("address")
        ]
        hostnames = [h.get("name") for h in host_el.findall("hostnames/hostname")]

        ports = []
        for port_el in host_el.findall("ports/port"):
            state_el = port_el.find("state")
            service_el = port_el.find("service")
            ports.append(
                {
                    "port": int(port_el.get("portid")),
                    "protocol": port_el.get("protocol"),
                    "state": state_el.get("state") if state_el is not None else None,
                    "service": service_el.get("name") if service_el is not None else None,
                    "product": service_el.get("product") if service_el is not None else None,
                    "version": service_el.get("version") if service_el is not None else None,
                }
            )

        os_matches = [
            {"name": m.get("name"), "accuracy": m.get("accuracy")}
            for m in host_el.findall("os/osmatch")
        ]

        hosts.append(
            {
                "addresses": addresses,
                "hostnames": hostnames,
                "ports": ports,
                "os_matches": os_matches,
            }
        )
    return hosts


@mcp.tool()
async def host_discovery(target: str) -> list[dict]:
    """
    Find which hosts are up in a target range, without port scanning them.
    target: a single IP, hostname, or CIDR range (e.g. "10.10.10.0/24").
    """
    _check_scope(target)
    root = await _run_nmap(["-sn", target])
    return _parse_hosts(root)


@mcp.tool()
async def quick_scan(target: str) -> list[dict]:
    """
    Fast scan of the 100 most common ports (TCP connect scan, no root
    required). Good first pass before a full port_scan.
    """
    _check_scope(target)
    root = await _run_nmap(["-sT", "-T4", "-F", target])
    return _parse_hosts(root)


@mcp.tool()
async def port_scan(target: str, ports: str | None = None, service_detection: bool = True) -> list[dict]:
    """
    TCP connect scan of a target (no root required). By default scans
    nmap's default top-1000 ports; pass ports (e.g. "22,80,443" or
    "1-1024") to narrow or widen it. service_detection runs -sV to
    identify service names/versions on open ports.
    """
    _check_scope(target)
    args = ["-sT", "-T4"]
    if service_detection:
        args.append("-sV")
    if ports:
        args += ["-p", ports]
    args.append(target)
    root = await _run_nmap(args, timeout=600)
    return _parse_hosts(root)


@mcp.tool()
async def os_detection(target: str) -> list[dict]:
    """
    Attempt OS fingerprinting against a target. Requires nmap to run with
    raw-socket privileges (root/CAP_NET_RAW) -- if the server process
    isn't privileged, this will raise a clear error rather than silently
    doing a normal scan.
    """
    _check_scope(target)
    root = await _run_nmap(["-O", target])
    return _parse_hosts(root)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
