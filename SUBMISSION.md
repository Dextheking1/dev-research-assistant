# Devpost Submission Draft: Dev Research Assistant

## Project name

Dev Research Assistant (self-hosted MCP server)

## Track

Alexa+ (self-hosted MCP server route). Mini challenge: Open Source.

## Short description

A small self-hosted MCP server that gives an AI assistant live developer
research tools: summarize a GitHub repo and its README, list its open
issues, and summarize pasted text. Any MCP client, including an Alexa+
Agent Skill, can connect to it over Streamable HTTP and call the tools.

## What was built

One Python file, `server.py`, built on the official MCP Python SDK.
It implements the Model Context Protocol spec 2025-11-25 over
Streamable HTTP, serving on a `/mcp` endpoint. It exposes four tools:

- `repo_readme_summary(owner, repo)`: fetches the repo README through the
  public GitHub API and returns an extractive summary.
- `repo_open_issues(owner, repo, limit)`: counts open issues (pull requests
  excluded) and lists the most recent ones with titles.
- `repo_info(owner, repo)`: description, stars, forks, main language,
  license.
- `summarize_text(text, max_sentences)`: extractive summary of any text,
  no network needed.

The summarizer is a small frequency-based extractive summarizer written for
this project, shared by the README tool and the text tool.

## How it works

An MCP client connects to the server, runs the standard initialize
handshake, lists the tools, and calls them with JSON arguments. The GitHub
tools call the public GitHub API at runtime (httpx, async), so results are
live. The server runs stateless over Streamable HTTP, binds localhost by
default, and can be put on any host with the `HOST` and `PORT` env vars.
It runs with two commands: pip install from `requirements.txt`, then
`python server.py`. Local verification (initialize, tools/list, tools/call
with real output) is recorded in VERIFY.md in the repo.

## Why it matters

Developers constantly context-switch to GitHub to answer simple questions:
what is this repo, is it active, what is broken right now. Putting those
answers behind MCP tools means a voice or chat assistant can answer them
in one step, with live data, from any repo. The server is tiny and generic,
so adding a new research tool is a few lines of Python.

## Product feedback (MCP tooling)

What I used: the official MCP Python SDK and the MCP spec
2025-11-25 Streamable HTTP transport, plus the public GitHub API.

What worked: the SDK made the server itself almost trivial. Decorate a
Python function, get a schema, a tools/list entry, and the full JSON-RPC
and transport handling for free. The Streamable HTTP transport worked with
plain curl for testing, which made debugging fast. Type hints turning
into tool schemas automatically is the right default.

What needs work: the jump from "works on localhost with curl" to "an
Alexa+ skill connects to it" is the least documented part. A short,
official end-to-end walkthrough that goes from a local MCP server to a
registered Alexa+ Agent Skill calling it, including hosting and auth
expectations, would cut the onboarding time a lot. Error messages when a
client sends the wrong Accept header are also cryptic for a first-time
server author.

Would I build again: yes. The SDK is solid; the missing piece is the
last-mile guide from local server to a live skill.

## Open Source mini challenge

This project itself is open source (MIT, this repo). Contribution made
during the hackathon window by the same author:

- Contribution URL: https://github.com/ruvnet/ruflo/pull/4416
- GitHub username: Dextheking1
- What was done: Security fix in the ruflo (claude-flow) repository,
  found by auditing its public source code and verified locally. The
  pull request was reviewed and merged on October 23, 2026, inside the
  hackathon window.
