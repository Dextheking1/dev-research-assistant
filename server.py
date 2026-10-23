"""Dev Research Assistant: a small self-hosted MCP server.

Implements the Model Context Protocol over Streamable HTTP (MCP spec
2025-11-25) using the official Python MCP SDK (MCPServer).

Tools:
  - repo_readme_summary: fetch a public GitHub repo README and summarize it
  - repo_open_issues: count and list recent open issues of a GitHub repo
  - repo_info: basic facts about a GitHub repo (stars, language, description)
  - summarize_text: extractive summary of any pasted text

Run:
  python server.py            (binds 127.0.0.1:8000, MCP endpoint at /mcp)
  PORT=9000 python server.py  (custom port)
"""

import asyncio
import os
import re
from collections import Counter

import httpx
from mcp.server.mcpserver import MCPServer

GITHUB_API = "https://api.github.com"
USER_AGENT = "dev-research-assistant-mcp/1.0"

mcp = MCPServer(
    "dev-research-assistant",
    instructions=(
        "Tools for quick developer research: summarize GitHub repos and "
        "their READMEs, check open issues, and summarize pasted text."
    ),
)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 20]


def _extractive_summary(text: str, max_sentences: int = 5) -> str:
    """Score sentences by word frequency and return the top ones in order."""
    sents = _sentences(text)
    if len(sents) <= max_sentences:
        return " ".join(sents)
    words = re.findall(r"[a-z0-9]+", text.lower())
    freq = Counter(w for w in words if len(w) > 3)
    scored = []
    for idx, sent in enumerate(sents):
        sent_words = re.findall(r"[a-z0-9]+", sent.lower())
        score = sum(freq.get(w, 0) for w in sent_words) / max(len(sent_words), 1)
        scored.append((score, idx, sent))
    top = sorted(scored, reverse=True)[:max_sentences]
    top.sort(key=lambda item: item[1])
    return " ".join(sent for _, _, sent in top)


def _clean_markdown(text: str) -> str:
    """Strip markdown and HTML noise so the summarizer sees plain prose."""
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)          # images
    text = re.sub(r"\[[^\]]*\]\([^)]*\)", " ", text)           # inline links
    text = re.sub(r"^\s*\[[^\]]*\]:\s*\S+.*$", " ", text, flags=re.M)  # link refs
    text = re.sub(r"[#>*`_~|=-]{1,}", " ", text)
    return re.sub(r"\s+", " ", text)


def _github_headers() -> dict:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _client() -> httpx.AsyncClient:
    """GitHub API client.

    Reads the proxy and CA bundle from the environment explicitly instead of
    using httpx env parsing, which breaks on some hosts whose NO_PROXY holds
    bracketed IPv6 entries. On a plain machine with no proxy env vars this is
    just a default client.
    """
    proxy = (
        os.environ.get("HTTPS_PROXY")
        or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY")
        or os.environ.get("http_proxy")
    )
    verify = os.environ.get("SSL_CERT_FILE") or True
    return httpx.AsyncClient(
        timeout=20.0,
        follow_redirects=True,
        proxy=proxy,
        trust_env=False,
        verify=verify,
    )


def _rate_limited(resp: httpx.Response) -> bool:
    return resp.status_code in (403, 429) and (
        resp.headers.get("x-ratelimit-remaining") == "0"
        or "rate limit" in resp.text.lower()
    )


RATE_LIMIT_MSG = (
    "GitHub API rate limit hit for this IP. Unauthenticated calls are capped "
    "at 60 per hour; set the GITHUB_TOKEN env var and restart the server for "
    "a much higher limit, or try again in a few minutes."
)


@mcp.tool()
async def repo_readme_summary(owner: str, repo: str) -> str:
    """Fetch the README of a public GitHub repo and return a short summary.

    Args:
        owner: GitHub user or org that owns the repo, e.g. "modelcontextprotocol"
        repo: Repository name, e.g. "python-sdk"
    """
    async with _client() as client:
        resp = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/readme",
            headers={**_github_headers(), "Accept": "application/vnd.github.raw+json"},
        )
    if _rate_limited(resp):
        return RATE_LIMIT_MSG
    if resp.status_code == 404:
        return f"No README found for {owner}/{repo} (or the repo is private)."
    resp.raise_for_status()
    text = resp.text
    cleaned = _clean_markdown(text)
    summary = _extractive_summary(cleaned, max_sentences=5)
    return (
        f"README of {owner}/{repo} ({len(text)} chars). Summary:\n\n{summary}"
    )


@mcp.tool()
async def repo_open_issues(owner: str, repo: str, limit: int = 10) -> str:
    """Count open issues of a public GitHub repo and list the most recent ones.

    Pull requests are excluded from the count and the list.

    Args:
        owner: GitHub user or org that owns the repo
        repo: Repository name
        limit: How many recent issues to list (default 10, max 30)
    """
    limit = max(1, min(limit, 30))
    async with _client() as client:
        resp = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/issues",
            params={"state": "open", "per_page": 100, "sort": "created", "direction": "desc"},
            headers=_github_headers(),
        )
    if _rate_limited(resp):
        return RATE_LIMIT_MSG
    if resp.status_code == 404:
        return f"Repo {owner}/{repo} not found (or private)."
    resp.raise_for_status()
    issues = [i for i in resp.json() if "pull_request" not in i]
    lines = [f"{owner}/{repo} has {len(issues)} open issues (first page, PRs excluded)."]
    for issue in issues[:limit]:
        lines.append(f"- #{issue['number']}: {issue['title']}")
    return "\n".join(lines)


@mcp.tool()
async def repo_info(owner: str, repo: str) -> str:
    """Return basic facts about a public GitHub repo.

    Args:
        owner: GitHub user or org that owns the repo
        repo: Repository name
    """
    async with _client() as client:
        resp = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}", headers=_github_headers()
        )
    if _rate_limited(resp):
        return RATE_LIMIT_MSG
    if resp.status_code == 404:
        return f"Repo {owner}/{repo} not found (or private)."
    resp.raise_for_status()
    data = resp.json()
    return (
        f"{data['full_name']}\n"
        f"Description: {data.get('description') or '(none)'}\n"
        f"Stars: {data['stargazers_count']}  Forks: {data['forks_count']}  "
        f"Open issues+PRs: {data['open_issues_count']}\n"
        f"Main language: {data.get('language') or 'unknown'}  "
        f"License: {(data.get('license') or {}).get('spdx_id', 'none')}\n"
        f"URL: {data['html_url']}"
    )


@mcp.tool()
def summarize_text(text: str, max_sentences: int = 5) -> str:
    """Summarize a block of text with an extractive summary.

    Args:
        text: The text to summarize
        max_sentences: Maximum sentences in the summary (default 5)
    """
    if not text.strip():
        return "No text provided."
    return _extractive_summary(text, max_sentences=max(1, min(max_sentences, 20)))


if __name__ == "__main__":
    asyncio.run(
        mcp.run_streamable_http_async(
            host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", "8000")),
            stateless_http=True,
        )
    )
