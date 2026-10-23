# Dev Research Assistant (MCP Server)

A small, self-hosted MCP server that gives an AI assistant quick developer
research tools: summarize a GitHub repo and its README, check what issues are
open, and summarize pasted text. Built for the Amazon Developer Hackathon
2026, Alexa+ track, as a self-hosted MCP server an Alexa+ Agent Skill can
connect to.

## What it does

The server speaks the Model Context Protocol (spec 2025-11-25) over
Streamable HTTP and exposes four tools:

| Tool | What it returns |
| --- | --- |
| `repo_readme_summary` | Fetches a public GitHub repo README and returns an extractive summary of it |
| `repo_open_issues` | Counts open issues of a repo (PRs excluded) and lists the most recent ones |
| `repo_info` | Stars, forks, main language, license, description of a repo |
| `summarize_text` | Extractive summary of any text you pass in |

Example questions an agent can answer with these tools:

- "What is the modelcontextprotocol/python-sdk repo about?"
- "How many open issues does facebook/react have right now, and what are the newest ones?"
- "Summarize this changelog for me."

## How it maps to the Alexa+ track

Alexa+ Agent Skills can call MCP servers to reach tools and live data. This
project is that server side: a standards-compliant MCP server, self-hosted,
running over Streamable HTTP. Any MCP client (an Alexa+ Agent Skill, or a
local client like the MCP Inspector) can connect to the `/mcp` endpoint,
list the tools, and call them. The tools hit the public GitHub API at
runtime, so answers are live data, not canned text.

## Run it

Needs Python 3.10 or newer.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python server.py
```

The server binds `127.0.0.1:8000` and serves the MCP endpoint at
`http://127.0.0.1:8000/mcp`. Set `HOST` and `PORT` env vars to change the
bind address or port. Set `GITHUB_TOKEN` if you want a higher GitHub API
rate limit; it works without one for light use.

## Quick test

With the server running, in another terminal:

```bash
curl -s -X POST http://127.0.0.1:8000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"curl-test","version":"1.0"}}}'
```

Then `tools/list` and `tools/call` with the same headers. See VERIFY.md for
a recorded run with real output.

## Layout

- `server.py` - the whole server (official Python MCP SDK)
- `requirements.txt` - dependencies (`mcp`, `httpx`)
- `VERIFY.md` - recorded local verification run
- `SUBMISSION.md` - Devpost submission draft

## License

MIT, see LICENSE. Copyright Benjamin Kincses.
