# A3: Connector Choice (starter)

Pick the path you can run safely. Least privilege is the rule either way.

## Primary path: Featured OAuth connector

Featured connectors include Google Drive, SharePoint, Outlook, Gmail, Slack, Notion, and Jira. During OAuth consent, grant **read access only**. Connectors run under **per-function permissions**, so scope each function deliberately rather than granting the whole account.

- Best when: you have a personal or sandbox account for one of the featured tools.
- Least-privilege check: at the consent screen, decline any write or delete scope you do not need for a read.

> `[VERIFY]` the exact connector list, the consent screen, and the per-function permission labels against the live Connectors UI at capture.

## Complex / stretch path: MCP connector

Use this if you have a remote MCP server or endpoint. Treat the server as **untrusted until reviewed**: check its authentication method and what it is allowed to call before you connect.

Grounded MCP facts (Model Context Protocol spec, 2025-11-25):

- A remote MCP server is reached over **Streamable HTTP** at an MCP endpoint (for example `https://mcp.example.com/mcp`).
- Requests authenticate with an HTTP header: `Authorization: Bearer <access-token>`.
- Servers may require an **OAuth authorization** flow (the client is redirected to consent, then the server binds the granted token to your identity).

See `../solution/mcp-config-example.md` for the connection shape. `[VERIFY]` the exact "add MCP connector" fields and consent flow in the Vibe Work UI.

## Decision aid

| If you have... | Choose |
|---|---|
| A personal Drive / test channel / sandbox ticket | Featured OAuth connector (Standard) |
| Your own remote MCP server or endpoint | MCP connector (stretch) |
| Neither | The captured walkthrough; check against the reference outcome |
