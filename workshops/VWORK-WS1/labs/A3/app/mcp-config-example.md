# A3: MCP Connector Config Example (stretch path)

The connection shape for wiring a remote MCP (Model Context Protocol) server to Vibe. The MCP transport and auth below are grounded in the MCP specification (2025-11-25). The Vibe-Work-specific "add MCP connector" form field labels must be confirmed against the live product.

## What a remote MCP connection requires

A remote MCP server is a service that exposes tools over HTTP. To connect one you need:

1. **The MCP endpoint URL.** Reached over **Streamable HTTP**, conventionally the `/mcp` path:
 ```
 https://your-mcp-server.example/mcp
 ```
 The client sends JSON-RPC messages via HTTP POST to this endpoint and may open an SSE stream via HTTP GET for server-to-client messages.

 Point this at your organization's read-only MCP server. If you don't operate one yet, you can run the official reference server locally (`npx -y @modelcontextprotocol/server-everything`) and expose it over HTTP, or use any remote MCP server your team runs. Prefer a read-only server so the connector can only pull, not mutate.

2. **Authentication (only if the server requires it).** A public read-only server may need none, so you can skip this step for it. When a server does require auth, it expects an HTTP Authorization header on every request:
 ```
 Authorization: Bearer <access-token>
 ```
 Servers commonly require an **OAuth authorization** flow: the client redirects you to the server's consent screen, you approve a scoped level of access, and the server binds the granted token to your identity. Prefer OAuth with least-privilege scopes over a long-lived static token where the server supports it.

## The shape you enter in Vibe

```
Connector type: MCP # confirm exact option label in-app
Server URL: https://your-mcp-server.example/mcp # the Streamable HTTP endpoint
Auth: None for this public example; OAuth (preferred) or Bearer token for servers that require it # confirm exact field labels in-app
Scope granted: read-only for the class of item you will pull
```

Confirm the literal field names, whether SSE-only legacy servers are accepted, and the consent flow, against the Vibe "add MCP connector" UI.

## Trust posture (do this before connecting)

- Confirm you know **who operates the server** and over what data.
- Review its **auth method** (OAuth with scoped consent is safer than a shared static token).
- Review **what tools it exposes** (what it can call). Treat the server as untrusted until you have.
- Grant the **minimum scope** for the one class of item you will pull.

## Expected outcome

Once connected, ask Vibe to pull one named item through the MCP tool (same as the Featured path). The connected action succeeds when the specific item or id is present in the task output. See `reference-outcome.md`.
