# Verification run

Recorded 2026-10-23 on the build machine, against the server in this repo
running locally (`python server.py`, endpoint `http://127.0.0.1:8000/mcp`).
All requests are plain curl POSTs with headers
`Content-Type: application/json` and
`Accept: application/json, text/event-stream`.

## 1. initialize (protocolVersion 2025-11-25)

Request body:

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"curl-test","version":"1.0"}}}
```

Response (SSE framed):

```
event: message
data: {"jsonrpc":"2.0","id":1,"result":{"capabilities":{"prompts":{"listChanged":false},"resources":{"listChanged":false,"subscribe":false},"tools":{"listChanged":false}},"instructions":"Tools for quick developer research: summarize GitHub repos and their READMEs, check open issues, and summarize pasted text.","protocolVersion":"2025-11-25","serverInfo":{"name":"dev-research-assistant","version":""}}}
```

The server negotiated protocolVersion 2025-11-25, as requested.

## 2. tools/list

```
- repo_readme_summary
- repo_open_issues
- repo_info
- summarize_text
```

## 3. tools/call repo_info

Arguments: `{"owner":"modelcontextprotocol","repo":"python-sdk"}`

```
modelcontextprotocol/python-sdk
Description: The official Python SDK for Model Context Protocol servers and clients
Stars: 24653  Forks: 4072  Open issues+PRs: 367
Main language: Python  License: MIT
URL: https://github.com/modelcontextprotocol/python-sdk
```

## 4. tools/call repo_open_issues

Arguments: `{"owner":"modelcontextprotocol","repo":"python-sdk","limit":3}`

```
modelcontextprotocol/python-sdk has 83 open issues (first page, PRs excluded).
- #3747: Progress callbacks run concurrently, out of order, and after `call_tool()` returns
- #3745: typing.Dict[str, X] return annotation is wrapped in {"result": ...}, unlike dict[str, X]
- #3737: Examples demonstrate ToolAnnotations only on a tool where they change nothing
```

## 5. tools/call summarize_text

Arguments: a six-sentence paragraph about the Model Context Protocol,
`max_sentences: 2`.

```
A server exposes tools, resources, and prompts over JSON-RPC. Clients discover those capabilities with a handshake and then call tools as the model needs them.
```

## 6. tools/call repo_readme_summary

Arguments: `{"owner":"modelcontextprotocol","repo":"python-sdk"}`

```
README of modelcontextprotocol/python-sdk (4561 chars). Summary:

MCP Python SDK Python implementation of the Model Context Protocol (MCP) ...
Documentation The documentation lives at . With this SDK you can: Build MCP
servers that expose tools, resources, and prompts to any MCP host Build MCP
clients that connect to any MCP server Speak every standard transport:
stdio, Streamable HTTP, and SSE Requirements Python 3.11+. ...
```

(truncated here; the tool returned the full five-sentence summary)

## Note on GitHub rate limits

The build machine shares one egress IP, and GitHub caps unauthenticated
API calls at 60 per hour per IP, so during this session the limit was hit
intermittently. When that happens the GitHub tools return a plain message
instead of an error:

```
GitHub API rate limit hit for this IP. Unauthenticated calls are capped at
60 per hour; set the GITHUB_TOKEN env var and restart the server for a much
higher limit, or try again in a few minutes.
```

Every tool above returned real live data in the runs recorded here.
