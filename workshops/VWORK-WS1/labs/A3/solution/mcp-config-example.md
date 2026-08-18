# A3: MCP Connector Config Example (solution, stretch path)

The connection shape for wiring a remote MCP (Model Context Protocol) server to Vibe Work. The MCP transport and auth below are grounded in the MCP specification (2025-11-25). The Vibe-Work-specific "add MCP connector" form fields are marked `[VERIFY]` because the exact UI labels must be confirmed against the live product.

## What a remote MCP connection requires

A remote MCP server is a service that exposes tools over HTTP. To connect one you need:

1. **The MCP endpoint URL.** Reached over **Streamable HTTP**, conventionally the `/mcp` path:
 ```
 https://mcp.example.com/mcp
 ```
 The client sends JSON-RPC messages via HTTP POST to this endpoint and may open an SSE stream via HTTP GET for server-to-client messages.

2. **Authentication.** An HTTP Authorization header on every request:
 ```
 Authorization: Bearer <access-token>
 ```
 Servers commonly require an **OAuth authorization** flow: the client redirects you to the server's consent screen, you approve a scoped level of access, and the server binds the granted token to your identity. Prefer OAuth with least-privilege scopes over a long-lived static token where the server supports it.

## The shape you enter in Vibe Work

```
Connector type: MCP # [VERIFY] exact option label
Server URL: https://mcp.example.com/mcp # the Streamable HTTP endpoint
Auth: OAuth (preferred) or Bearer token # [VERIFY] exact field labels
Scope granted: read-only for the class of item you will pull
```

`[VERIFY]` the literal field names, whether SSE-only legacy servers are accepted, and the consent flow, against the Vibe Work "add MCP connector" UI at capture.

## Trust posture (do this before connecting)

- Confirm you know **who operates the server** and over what data.
- Review its **auth method** (OAuth with scoped consent is safer than a shared static token).
- Review **what tools it exposes** (what it can call). Treat the server as untrusted until you have.
- Grant the **minimum scope** for the one class of item you will pull.

## Expected outcome

Once connected, ask Vibe Work to pull one named item through the MCP tool (same as the Featured path). The connected action succeeds when the specific item or id is present in the task output. See `reference-outcome.md`.
