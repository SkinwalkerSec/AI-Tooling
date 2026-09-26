"""
bloodhound-mcp: an MCP server exposing BloodHound's Neo4j graph as tools.

Talks directly to the Neo4j instance BloodHound populates, using the
official `neo4j` Python driver. No credentials are hardcoded -- everything
comes from environment variables (see .env.example).

Query tools are read-only by construction (Cypher run in a read
transaction, plus a keyword guard). The one tool that mutates data
(`mark_principal_owned`) is separate and explicit, matching how operators
actually use BloodHound (marking nodes owned as an engagement progresses).
"""

import os
import re

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from neo4j import AsyncGraphDatabase

load_dotenv()

mcp = MCPServer("bloodhound-mcp")

_driver = None

# Blocked in the read path: write keywords, plus LOAD CSV and apoc procedures,
# which are technically reads but let a query touch the filesystem / make
# outbound requests (file:// local read, http:// SSRF). A read transaction
# alone would not stop those.
_WRITE_KEYWORDS = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|LOAD\s+CSV|CALL\s+apoc\.)\b",
    re.IGNORECASE,
)


def _env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(
            f"{name} is not set. Copy .env.example to .env, fill it in, "
            "and make sure your MCP client loads it (see README)."
        )
    return value


def _get_driver():
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            _env("NEO4J_URI", "bolt://localhost:7687"),
            auth=(_env("NEO4J_USERNAME", "neo4j"), _env("NEO4J_PASSWORD")),
        )
    return _driver


async def _run_read(query: str, parameters: dict | None = None) -> list[dict]:
    if _WRITE_KEYWORDS.search(query):
        raise ValueError(
            "This tool only runs read queries. Write keywords "
            "(CREATE/MERGE/DELETE/SET/REMOVE/DROP) and filesystem/network "
            "keywords (LOAD CSV, apoc procedures) are rejected."
        )
    driver = _get_driver()
    async with driver.session() as session:
        async def work(tx):
            result = await tx.run(query, parameters or {})
            return [record.data() async for record in result]

        return await session.execute_read(work)


@mcp.tool()
async def run_cypher(query: str, parameters: dict | None = None) -> list[dict]:
    """
    Run a read-only Cypher query against the BloodHound Neo4j database.

    Rejected if the query contains write keywords (CREATE, MERGE, DELETE,
    SET, REMOVE, DROP) or filesystem/network keywords (LOAD CSV, apoc
    procedures). Use for ad-hoc graph exploration beyond the canned queries
    below.
    """
    return await _run_read(query, parameters)


@mcp.tool()
async def shortest_paths_to_domain_admins(domain: str) -> list[dict]:
    """
    Find shortest attack paths from any non-Domain-Admin principal to the
    Domain Admins group for the given domain (e.g. "CORP.LOCAL").
    """
    query = """
    MATCH (dst:Group)
    WHERE dst.name STARTS WITH 'DOMAIN ADMINS@' AND toUpper(dst.domain) = toUpper($domain)
    MATCH p = shortestPath((src)-[*1..15]->(dst))
    WHERE src <> dst AND NOT src:Group
    RETURN
        src.name AS start_node,
        [n IN nodes(p) | n.name] AS path_nodes,
        [r IN relationships(p) | type(r)] AS path_edges
    LIMIT 200
    """
    return await _run_read(query, {"domain": domain})


@mcp.tool()
async def kerberoastable_users(domain: str | None = None) -> list[dict]:
    """List enabled users with an SPN set (Kerberoastable), excluding krbtgt."""
    query = """
    MATCH (u:User)
    WHERE u.hasspn = true AND u.enabled = true AND NOT toUpper(u.name) STARTS WITH 'KRBTGT'
      AND ($domain IS NULL OR toUpper(u.domain) = toUpper($domain))
    RETURN u.name AS name, u.domain AS domain, u.pwdlastset AS pwd_last_set
    ORDER BY u.pwdlastset ASC
    LIMIT 500
    """
    return await _run_read(query, {"domain": domain})


@mcp.tool()
async def unconstrained_delegation_computers(domain: str | None = None) -> list[dict]:
    """List computers configured with unconstrained Kerberos delegation."""
    query = """
    MATCH (c:Computer)
    WHERE c.unconstraineddelegation = true
      AND ($domain IS NULL OR toUpper(c.domain) = toUpper($domain))
    RETURN c.name AS name, c.domain AS domain, c.enabled AS enabled
    LIMIT 500
    """
    return await _run_read(query, {"domain": domain})


@mcp.tool()
async def owned_principals() -> list[dict]:
    """List all principals currently marked 'owned' in this BloodHound database."""
    query = """
    MATCH (n {owned: true})
    RETURN n.name AS name, labels(n) AS labels, n.domain AS domain
    LIMIT 1000
    """
    return await _run_read(query, {})


@mcp.tool()
async def mark_principal_owned(name: str, node_type: str) -> dict:
    """
    Mark a principal as owned (write operation). node_type must be one of
    User, Computer, Group, OU, GPO, Domain, Container -- matching BloodHound's
    node labels.
    """
    allowed_types = {"User", "Computer", "Group", "OU", "GPO", "Domain", "Container"}
    if node_type not in allowed_types:
        raise ValueError(f"node_type must be one of {sorted(allowed_types)}")

    query = f"""
    MATCH (n:{node_type} {{name: $name}})
    SET n.owned = true
    RETURN n.name AS name, labels(n) AS labels
    """
    driver = _get_driver()
    async with driver.session() as session:
        async def work(tx):
            result = await tx.run(query, {"name": name})
            return [record.data() async for record in result]

        rows = await session.execute_write(work)
    if not rows:
        raise ValueError(f"No {node_type} node named {name!r} found")
    return rows[0]


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
