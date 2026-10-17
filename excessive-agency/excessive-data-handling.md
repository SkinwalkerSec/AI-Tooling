# Excessive Data Handling & Insecure Storage

Methodology for identifying and exploiting insecure data storage in ML/AI-integrated web
applications. When an application processes data beyond what is needed (violating data
minimization) and stores it insecurely, the combined impact is magnified --- sensitive
training data, inference logs, user inputs, and intermediate results become prime targets.

> Authorized use only. Run these against your own systems, a lab, or a scoped engagement.

---

## Attack surface summary

| Component | Risk | What to look for |
|---|---|---|
| **LLM query logs** | Chat inputs logged with sensitive data (PII, medical, payment) | Database tables storing raw queries and responses |
| **Exposed data stores** | Database files, backups, or dumps accessible via web | `.db`, `.sql`, `.sqlite`, `.bak`, `.dump` files in web root |
| **Web frontend / API** | Standard web vulns (directory traversal, SQLi, IDOR) exposing ML data | Unprotected endpoints, misconfigured static file serving |
| **Excessive collection** | App collects data unnecessary for its ML function | Credit card numbers in a console-recommendation chatbot, medical data in plaintext logs |

---

## Phase 1 --- Reconnaissance & directory brute-forcing

The ML model is only one part of the attack surface. The surrounding web application
(frontends, APIs, data pipelines) can expose stored data directly.

```bash
gobuster dir -u http://<TARGET>:<PORT>/ \
  -w /usr/share/seclists/Discovery/Web-Content/raft-small-words.txt \
  -x .db,.txt,.html,.sql,.sqlite,.bak,.dump,.csv,.json,.log
```

**What to watch for:**

- Database files served as static assets (e.g. `/storage.db`, `/database.db`, `/backup.sql`)
- Log files containing query history (`/logs/`, `/debug.log`)
- API endpoints returning raw data (`/api/queries`, `/api/users`)
- Status codes 200 on file extensions that should never be publicly served

---

## Phase 2 --- Retrieve exposed data stores

When directory brute-forcing reveals a database or dump file, pull it down:

```bash
wget http://<TARGET>:<PORT>/database.db
```

Identify the file type:

```bash
file database.db
```

Common results and how to handle them:

| `file` output | Format | Tool |
|---|---|---|
| `SQLite 3.x database` | SQLite | `sqlite3 database.db .dump` |
| `ASCII text, with very long lines` | SQL dump (plaintext) | `cat` / `grep` / `less` |
| `data` or `MySQL` | MySQL binary / InnoDB | `strings` then `mysqlfrm` if needed |

---

## Phase 3 --- Analyze the schema and data

For a plaintext SQL dump:

```bash
# Show all table definitions
grep -E "^CREATE TABLE" database.db

# Extract LLM query logs specifically
grep -A5 "llm_queries" database.db

# Find credit card patterns (basic Luhn-candidate 16-digit numbers)
grep -oP '\b[0-9]{13,19}\b' database.db

# Find anything that looks like sensitive PII
grep -iE '(credit.?card|ssn|password|medical|diagnosis|condition)' database.db
```

For SQLite:

```bash
sqlite3 database.db ".tables"
sqlite3 database.db ".schema llm_queries"
sqlite3 database.db "SELECT * FROM llm_queries;"
```

---

## Phase 4 --- Identify excessive data handling violations

Map what the application collects against what it actually needs for its stated function.

| Application function | Legitimate data needs | Excessive data (violation) |
|---|---|---|
| Console recommendation based on medical condition | General preference category | Raw medical diagnosis stored in plaintext query logs |
| Order placement | Payment token via PCI-compliant processor | Raw credit card number in chat log / database |
| User profiling | Anonymized interaction metadata | IP address + full query text + user ID linked together |

**Key indicators of excessive handling:**

- Chat messages logged verbatim including sensitive fields the LLM solicited
- No distinction between transient conversation context and persistent storage
- Sensitive data stored with the same (or weaker) controls as general application data
- Data retained indefinitely with no purge policy

---

## Phase 5 --- Assess downstream impact

Once you have the data, document the exposure:

```
llm_queries table:
  - user_id: links queries to registered accounts
  - ip_address: ties activity to network identity
  - query: contains raw user input (credit cards, medical info)
  - response: contains LLM output (may reflect/repeat sensitive input)
```

Chain with other findings:

- **Credential reuse**: if `users` table has password hashes, check for weak hashing (MD5, unsalted SHA)
- **Session data**: if sessions are stored, check for token leakage
- **Cross-reference**: user IDs from `llm_queries` map to `users` table for full identity resolution

---

## Payload reference table

| Goal | Command |
|---|---|
| Directory brute-force with data extensions | `gobuster dir -u http://<T>:<P>/ -w <wordlist> -x .db,.txt,.html,.sql,.sqlite,.bak,.dump,.csv,.json,.log` |
| Download exposed database | `wget http://<T>:<P>/database.db` |
| Identify file type | `file database.db` |
| Dump SQLite tables | `sqlite3 database.db ".tables"` |
| Dump SQLite schema | `sqlite3 database.db ".schema <table>"` |
| Extract all LLM queries | `sqlite3 database.db "SELECT * FROM llm_queries;"` |
| Grep for credit cards | `grep -oP '\b[0-9]{13,19}\b' database.db` |
| Grep for PII keywords | `grep -iE '(credit.?card\|ssn\|password\|medical\|diagnosis)' database.db` |

---

## Lessons learned

1. **The ML model is not the only target.** Standard web application security testing
   (directory brute-forcing, endpoint enumeration) is essential when assessing AI
   applications. The surrounding infrastructure often has the weakest links.

2. **Excessive data collection amplifies every other vulnerability.** An exposed database is
   bad; an exposed database full of medical records and credit card numbers that the
   application had no business collecting is catastrophic.

3. **LLM chat logs are high-value targets.** Applications that log raw queries and responses
   create a single artifact containing everything users were prompted to disclose. If the
   LLM solicits sensitive data, the logs inherit that sensitivity.

4. **Data minimization is a security control, not just a compliance checkbox.** Collecting
   only what is needed for the application's function limits the blast radius when (not if)
   a storage vulnerability is exploited.

5. **Defense expectations.** Properly secured applications enforce: encrypted storage at
   rest, backend access controls on all data endpoints, PCI DSS-compliant payment flows
   (never raw card numbers in chat), data retention policies with automated purging, and
   separation of log sensitivity levels.
