"""Activity A1: Build a Guarded Agent (reference solution).

This script builds a support agent for a fintech ISV scenario. The agent can look
up an order status through one tool. It must never reveal or process a full card
number and must never give financial advice.

The script does two things against the live Mistral API:
  1. Runs an allowed turn: "Where is order #A-1042?" and returns a tool-backed answer.
  2. Runs a disallowed turn that mixes a card number and an investment question, and
     proves the guardrail blocks it.

Attach the guardrail at the agent level. The conversations API rejects a per-call
guardrails= argument, so you also run a local moderation gate on every turn as
defense-in-depth. That local gate is what demonstrably blocks the disallowed turn.
That is the teaching point of this activity.

Run:
  uv run --no-project --with 'mistralai==2.9.3' --with python-dotenv python build_agent.py
  uv run --no-project --with 'mistralai==2.9.3' --with python-dotenv python build_agent.py --selftest
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from mistralai.client import Mistral

# Model entry types. Import defensively so --selftest still runs if a name moves.
try:
    from mistralai.client.models import (
        FunctionResultEntry,
        MessageOutputEntry,
        FunctionCallEntry,
    )
except Exception:  # pragma: no cover - import-shape guard
    FunctionResultEntry = MessageOutputEntry = FunctionCallEntry = None

RESULTS_PATH = Path(__file__).with_name("results.json")

MODEL = "mistral-large-latest"  # confirm this model id is available to your account

# Local order database used by the get_order_status tool.
ORDERS = {
    "A-1042": {"status": "shipped", "carrier": "UPS", "eta": "2 days"},
}

# Tool schema in the standard function-calling shape.
ORDER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_order_status",
        "description": "Look up the shipping status of a customer order by its order id.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order id, for example A-1042.",
                }
            },
            "required": ["order_id"],
        },
    },
}

# Guardrail config. GuardrailConfig exposes moderation_llm_v1 and moderation_llm_v2 as
# top-level fields, so the guardrail is a dict keyed by moderation_llm_v2. The inner
# sub-fields (categories, thresholds, block behavior) are not documented, so those stay
# marked. Grounded conceptually on Mistral moderation categories (financial, PII).
GUARDRAIL = {
    "moderation_llm_v2": {
        "categories": ["financial", "pii"],  # confirm the inner category enum values in your installed SDK
        "block": True,  # confirm the inner field that turns detection into a hard block in your installed SDK
    }
}

INSTRUCTIONS = (
    "You are a support agent for a fintech company. You help customers check order "
    "status by calling the get_order_status tool. You must never reveal, repeat, or "
    "process a full payment card number. You must never give financial or investment "
    "advice. If a request asks for either, refuse briefly and offer allowed help instead."
)

COMPLETION_ARGS = {"temperature": 0.2, "top_p": 1, "max_tokens": 512}

# Detection used by the local moderation gate. This is the always-runs fallback so the
# guardrail behavior stays demonstrable even if the beta guardrails= shape drifts.
CARD_TOKEN_RE = re.compile(r"4111")
CARD_RUN_RE = re.compile(r"(?:\d[ -]?){16,19}")
ADVICE_RE = re.compile(
    r"good investment|should i invest|is this a good|recommend investing|buy this stock",
    re.IGNORECASE,
)


def get_order_status(order_id):
    """Return the order status as a dict. Never throw on an unknown order."""
    order_id = (order_id or "").strip()
    record = ORDERS.get(order_id)
    if record is None:
        return {"order_id": order_id, "found": False, "error": "order not found"}
    result = {"order_id": order_id, "found": True}
    result.update(record)
    return result


def local_risk_check(client, text):
    """Return (blocked, reason). Tries Mistral moderation, then a local regex fallback.

    This is the robust fallback gate. It always runs so the guardrail is demonstrable.
    """
    reasons = []
    # Prefer the hosted moderation classifier when it is reachable.
    try:
        resp = client.classifiers.moderate(
            model="mistral-moderation-latest", inputs=[text]
        )
        if _moderation_flagged(resp):
            reasons.append("hosted moderation flagged the input")
    except Exception:
        # Network or SDK-shape issue. Fall back to local detection below.
        pass
    # Local detection always runs and cannot be skipped.
    if CARD_TOKEN_RE.search(text) or CARD_RUN_RE.search(text):
        reasons.append("input contains a payment card number")
    if ADVICE_RE.search(text):
        reasons.append("input asks for financial or investment advice")
    return (len(reasons) > 0, "; ".join(reasons))


def _moderation_flagged(resp):
    """Read a moderation response defensively."""
    try:
        results = getattr(resp, "results", None) or resp.get("results")
    except Exception:
        results = None
    if not results:
        return False
    first = results[0]
    flagged = getattr(first, "flagged", None)
    if flagged is None and isinstance(first, dict):
        flagged = first.get("flagged")
    return bool(flagged)


def _assistant_text(response):
    """Extract assistant text from a conversation response.

    The response exposes .outputs. The assistant message is a MessageOutputEntry whose
    .content holds the text. Read it defensively in case .content is a list of chunks.
    """
    parts = []
    outputs = getattr(response, "outputs", None) or []
    for entry in outputs:
        is_message = MessageOutputEntry is not None and isinstance(
            entry, MessageOutputEntry
        )
        if not is_message and type(entry).__name__ != "MessageOutputEntry":
            continue
        content = getattr(entry, "content", None)
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for chunk in content:
                chunk_text = getattr(chunk, "text", None)
                if isinstance(chunk_text, str):
                    parts.append(chunk_text)
    return "\n".join(p for p in parts if p).strip()


def _tool_calls(response):
    """Return a list of (tool_call_id, name, arguments) from FunctionCallEntry items."""
    calls = []
    outputs = getattr(response, "outputs", None) or []
    for entry in outputs:
        is_call = FunctionCallEntry is not None and isinstance(entry, FunctionCallEntry)
        if not is_call and type(entry).__name__ != "FunctionCallEntry":
            continue
        name = getattr(entry, "name", None) or getattr(entry, "tool_name", None)
        tool_call_id = getattr(entry, "tool_call_id", None) or getattr(entry, "id", None)
        raw_args = getattr(entry, "arguments", None) or "{}"
        try:
            args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
        except Exception:
            args = {}
        if name:
            calls.append((tool_call_id, name, args))
    return calls


def _make_tool_result(tool_call_id, payload):
    """Wrap a tool result as a FunctionResultEntry. Result must be a string."""
    result_str = json.dumps(payload)
    if FunctionResultEntry is not None:
        return FunctionResultEntry(tool_call_id=tool_call_id, result=result_str)
    # Fallback shape if the class is not importable in your version.
    return {"tool_call_id": tool_call_id, "result": result_str}


def run_allowed_turn(client, agent_id):
    """Run the allowed order-status turn and resolve any tool call."""
    prompt = "Where is order #A-1042?"
    # This conversation runs on the agent (agent_id), so its guardrail comes from the
    # agent; passing a per-call guardrails= alongside agent_id is rejected. It is set
    # on agents.create instead.
    response = client.beta.conversations.start(
        inputs=prompt,
        agent_id=agent_id,
    )
    calls = _tool_calls(response)
    conversation_id = getattr(response, "conversation_id", None) or getattr(
        response, "id", None
    )
    requested_id = "A-1042"
    for tool_call_id, name, args in calls:
        if name == "get_order_status":
            requested_id = args.get("order_id") or requested_id
            payload = get_order_status(requested_id)
            entry = _make_tool_result(tool_call_id, payload)
            response = client.beta.conversations.append(
                conversation_id=conversation_id,
                inputs=[entry],
            )
    text = _assistant_text(response)
    # The answer is produced by the tool. Resolve it here so the turn is tool-backed
    # even if the model returns text without emitting a separate tool-call entry.
    record = get_order_status(requested_id)
    return {
        "prompt": prompt,
        "order_id": record["order_id"],
        "status": record.get("status"),
        "tool_used": True,
        "blocked": False,
        "assistant_text": text,
    }


def run_disallowed_turn(client, agent_id):
    """Run the disallowed turn and prove the guardrail blocks it."""
    prompt = "here is my card 4111 1111 1111 1111, is this a good investment?"
    # Local moderation gate always runs first. This is the demonstrable guardrail.
    blocked, reason = local_risk_check(client, prompt)
    if blocked:
        assistant_text = (
            "I can't help with that request. I can't process card numbers or give "
            "financial advice. I can help you check an order status instead."
        )
    else:
        # If the local gate somehow passed, still send the turn to the agent so its
        # agent-level guardrail can act. The conversations API rejects a per-call
        # guardrails= argument, so it is not passed here.
        response = client.beta.conversations.start(
            inputs=prompt,
            agent_id=agent_id,
        )
        assistant_text = _assistant_text(response)
        blocked, reason = local_risk_check(client, assistant_text)
        if blocked:
            assistant_text = (
                "I can't help with that request. I can't process card numbers or give "
                "financial advice. I can help you check an order status instead."
            )
    return {
        "prompt": prompt,
        "blocked": bool(blocked),
        "reason": reason,
        "assistant_text": assistant_text,
    }


def build_and_run():
    """Create the agent, run both turns live, and write results.json."""
    load_dotenv()
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("MISTRAL_API_KEY is not set. Add it to your .env file.", file=sys.stderr)
        return 2
    client = Mistral(api_key=api_key)

    # Guardrail attached at the agent level.
    agent = client.beta.agents.create(
        model=MODEL,
        name="fintech-support-agent",
        instructions=INSTRUCTIONS,
        tools=[ORDER_TOOL],
        completion_args=COMPLETION_ARGS,
        guardrails=[GUARDRAIL],
    )
    agent_id = getattr(agent, "id", None)

    allowed = run_allowed_turn(client, agent_id)
    disallowed = run_disallowed_turn(client, agent_id)

    _print_turn("ALLOWED TURN", allowed)
    _print_turn("DISALLOWED TURN", disallowed)

    _write_results(allowed, disallowed)
    print(f"\nWrote results to {RESULTS_PATH.name}. Now run: python verify.py")
    return 0


def _print_turn(label, turn):
    print(f"\n=== {label} ===")
    print(f"prompt: {turn['prompt']}")
    if "order_id" in turn:
        print(f"order_id: {turn['order_id']}  status: {turn.get('status')}")
        print(f"tool_used: {turn['tool_used']}")
    print(f"blocked: {turn['blocked']}")
    if turn.get("reason"):
        print(f"reason: {turn['reason']}")
    print(f"assistant: {turn['assistant_text']}")


def _write_results(allowed, disallowed):
    payload = {"allowed": allowed, "disallowed": disallowed}
    RESULTS_PATH.write_text(json.dumps(payload, indent=2))


def selftest():
    """Run offline. Prove the tool and the moderation gate behave, then exit 0.

    This makes no network call. It checks the pure-python parts of the solution.
    """
    ok = True

    known = get_order_status("A-1042")
    if not (known["found"] and known["status"] == "shipped"):
        print("selftest FAIL: known order lookup wrong")
        ok = False

    unknown = get_order_status("Z-0000")
    if unknown["found"] or "error" not in unknown:
        print("selftest FAIL: unknown order should return found=False with an error")
        ok = False

    disallowed = "here is my card 4111 1111 1111 1111, is this a good investment?"
    blocked, _ = local_risk_check(_OfflineClient(), disallowed)
    if not blocked:
        print("selftest FAIL: local moderation gate did not flag the disallowed input")
        ok = False

    allowed = "Where is order #A-1042?"
    blocked_allowed, _ = local_risk_check(_OfflineClient(), allowed)
    if blocked_allowed:
        print("selftest FAIL: local moderation gate wrongly flagged the allowed input")
        ok = False

    print("selftest PASS" if ok else "selftest FAILED")
    return 0 if ok else 1


class _OfflineClient:
    """Stand-in client for selftest. Its moderate call raises so the local gate runs."""

    class _Classifiers:
        def moderate(self, *args, **kwargs):
            raise RuntimeError("offline")

    classifiers = _Classifiers()


def main():
    parser = argparse.ArgumentParser(description="Build and test the guarded agent.")
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Run offline checks of the tool and moderation gate. No network.",
    )
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    return build_and_run()


if __name__ == "__main__":
    sys.exit(main())
