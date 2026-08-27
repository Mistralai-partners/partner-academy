# A3: Scenario Card

You are preparing a task that needs one live input from a system of record: a recent file, a ticket, or a channel message. Rather than copy-paste it by hand, you wire that tool to Vibe under a least-privilege scope and let the task pull it in.

## Your task

Ask Vibe to produce a short summary that must include **one named item** pulled from a connected tool. For example:

- "Summarize the file **Q3-plan.pdf** from my Drive and list its three main sections."
- "Pull the latest message in the **#launch-test** channel and quote it."
- "Get ticket **PROJ-142** and state its current status."

The point is not the summary. The point is that a real, named item from an external system is present in the output, pulled through a connector you scoped to read-only.

## Two paths (pick one)

- **Primary (Standard):** a Featured OAuth connector (Google Drive, SharePoint, Outlook, Gmail, Slack, Notion, Jira, and others). Grant read access only.
- **Complex / stretch:** an MCP (Model Context Protocol) connector, if you have a server or endpoint. See `../solution/mcp-config-example.md`.

No tool to connect? Follow the lab's screenshots and check against `../solution/reference-outcome.md`. The lab still counts.

## Self-contained note

A3 needs only one connectable tool (or the lab's screenshots). It uses no Library, Skill, or output from another lab.
