#!/usr/bin/env python
"""Task 4 (SOLUTION) - Right-size the architecture, and choose the handoff mode.

The highest-value scoping judgment a technical seller makes: telling a genuine
multi-agent case from a single-agent-with-tools case, and refusing to
over-engineer. A customer proposing a five-agent chain for a linear, single-domain
job is a trap; the honest recommendation is often simpler, and saying so earns
more trust than agreeing. When multi-agent IS warranted, you also pick the
handoff execution mode (course B3).

Scope point: warrant multi-agent only when the work spans distinct specialist
domains; a linear chain of deterministic tool calls in one domain is a single
agent with tools. When multi-agent is warranted, pick client-side execution
whenever a human must inspect or gate each delegation, otherwise server-side.

Grounded rules (from the pinned docs - do not invent):
  - Genuine multi-agent = distinct specialist domains, each needing its own
    tools/instructions; a chain of deterministic tool calls in ONE domain is a
    single agent with tools, not a handoff workflow. (agents/handoffs.md,
    agents/agents-api.md)
  - `handoff_execution` = "server" (default: runs internally on Mistral's cloud)
    or "client" (control returns to the caller so a human can inspect/gate each
    delegation before it runs). (agents/handoffs.md)

Offline task: pure decision logic, no API calls.
"""
import sys

ARCHITECTURES = {"single_agent_with_tools", "multi_agent_handoffs"}
EXEC_MODES = {"server", "client", None}

SCENARIOS = [
    {
        "id": "A1",
        "ask": "Customer proposes 5 agents: fetch order -> look up SKU -> compute "
               "tax -> format receipt -> email it. All deterministic tool calls, "
               "one domain, no independent specialist reasoning.",
        "distinct_specialist_domains": False,
        "must_inspect_each_delegation": False,
    },
    {
        "id": "A2",
        "ask": "A finance assistant hands off to a web-research specialist, then a "
               "quantitative calculator specialist - genuinely distinct domains, "
               "each with its own tools and instructions. Fully automated, latency "
               "sensitive, no human in the loop.",
        "distinct_specialist_domains": True,
        "must_inspect_each_delegation": False,
    },
    {
        "id": "A3",
        "ask": "A distinct legal-review agent hands off to a distinct finance agent, "
               "but a compliance officer must inspect and approve each delegation "
               "before it executes.",
        "distinct_specialist_domains": True,
        "must_inspect_each_delegation": True,
    },
    {
        "id": "A4",
        "ask": "Customer wants 3 agents to answer FAQs from a single knowledge base. "
               "It is one task with one tool.",
        "distinct_specialist_domains": False,
        "must_inspect_each_delegation": False,
    },
]

# Acceptance rubric (architecture, handoff_execution) for an honestly-scoped call.
EXPECTED = {
    "A1": ("single_agent_with_tools", None),
    "A2": ("multi_agent_handoffs", "server"),
    "A3": ("multi_agent_handoffs", "client"),
    "A4": ("single_agent_with_tools", None),
}


def decide(s):
    """Return (architecture, handoff_execution) for one proposal."""
    # Multi-agent is warranted only for genuinely distinct specialist domains.
    if s["distinct_specialist_domains"]:
        architecture = "multi_agent_handoffs"
        # Client-side execution returns control so a human can inspect/gate each
        # delegation; server-side (default) runs the chain internally.
        handoff_execution = "client" if s["must_inspect_each_delegation"] else "server"
    else:
        # Right-size down: a single agent with tools, no handoffs.
        architecture = "single_agent_with_tools"
        handoff_execution = None
    return architecture, handoff_execution


def main():
    failures = []
    for s in SCENARIOS:
        got = decide(s)
        assert got[0] in ARCHITECTURES, f"{s['id']}: unknown architecture {got[0]!r}"
        assert got[1] in EXEC_MODES, f"{s['id']}: unknown exec mode {got[1]!r}"
        exp = EXPECTED[s["id"]]
        mark = "ok" if got == exp else "XX"
        print(f"  [{mark}] {s['id']}: got={got}  expected={exp}")
        if got != exp:
            failures.append(s["id"])
    if failures:
        raise AssertionError(f"mis-sized architectures: {', '.join(failures)}")
    print("TASK4 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK4 FAIL: {e}")
        sys.exit(1)
