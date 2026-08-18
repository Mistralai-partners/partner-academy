#!/usr/bin/env python
"""Task 3 (STARTER) - Scope the right surface, and call feasibility honestly.

The scoping exercise: a technical seller reads a customer's requirement and, on
the spot, names the correct AI Studio surface AND says honestly whether the
request is feasible exactly as stated. Getting the surface right wins
credibility; catching the "not as asked, here is the right way" cases wins trust
(course B1, B2, B4, B5).

Your job: write the decision rules in `decide()` so every scenario resolves to
the grounded surface and the honest `feasible_as_asked` verdict. The starter
mis-routes tool scenarios to Chat Completions and marks everything feasible.

Grounded rules (all from the pinned docs - do not invent):
  - web_search / code_interpreter are NOT supported on Chat Completions; they
    require the Conversations & Agents API.
    (agents/agent-tools/websearch.md, agents/agent-tools/code_interpreter.md)
  - Structured extraction from documents at volume -> Document AI Annotations.
    (document-processing/annotations.md, overview.md)
  - Grounding answers in the customer's own docs as a MANAGED service ->
    Libraries (managed RAG). (knowledge-rag/rag_quickstart.md)
  - Transcription -> Voxtral; realtime is NOT compatible with `diarize`, so
    "live + who-spoke" is not feasible as one model.
    (audio/speech_to_text/realtime_transcription.md)
  - Simple stateless single-turn generation with no tools -> Chat Completions.
    (conversations/chat-completion.md)

Offline task: pure decision logic, no API calls.
"""
import sys

# Surface vocabulary (return exactly one of these strings).
SURFACES = {"chat_completions", "conversations_agents", "document_ai", "rag_library", "voxtral"}

SCENARIOS = [
    {
        "id": "S1",
        "ask": "We want the assistant to browse the web for fresh prices, but our "
               "platform can only call the /v1/chat/completions endpoint.",
        "needs_web_or_code_tool": True,
        "endpoint": "chat_completions_only",
        "doc_extraction": False,
        "ground_private_docs_managed": False,
        "transcription": False,
        "realtime": False,
        "needs_diarization": False,
    },
    {
        "id": "S2",
        "ask": "Extract vendor, invoice number, and total as typed JSON from about "
               "50,000 scanned invoices every month.",
        "needs_web_or_code_tool": False,
        "endpoint": None,
        "doc_extraction": True,
        "ground_private_docs_managed": False,
        "transcription": False,
        "realtime": False,
        "needs_diarization": False,
    },
    {
        "id": "S3",
        "ask": "Ground our support chatbot in our private policy PDFs. We want a "
               "managed service that ingests, vectorizes, and searches them for us.",
        "needs_web_or_code_tool": False,
        "endpoint": None,
        "doc_extraction": False,
        "ground_private_docs_managed": True,
        "transcription": False,
        "realtime": False,
        "needs_diarization": False,
    },
    {
        "id": "S4",
        "ask": "Live-caption a support call in real time AND label who is speaking.",
        "needs_web_or_code_tool": False,
        "endpoint": None,
        "doc_extraction": False,
        "ground_private_docs_managed": False,
        "transcription": True,
        "realtime": True,
        "needs_diarization": True,
    },
    {
        "id": "S5",
        "ask": "Summarize a single pasted paragraph. No tools, one turn, and no "
               "conversation data stored on your cloud.",
        "needs_web_or_code_tool": False,
        "endpoint": None,
        "doc_extraction": False,
        "ground_private_docs_managed": False,
        "transcription": False,
        "realtime": False,
        "needs_diarization": False,
    },
    {
        "id": "S6",
        "ask": "A multi-turn analyst assistant that must run Python to compute "
               "results. No endpoint restriction on our side.",
        "needs_web_or_code_tool": True,
        "endpoint": None,
        "doc_extraction": False,
        "ground_private_docs_managed": False,
        "transcription": False,
        "realtime": False,
        "needs_diarization": False,
    },
]

# Acceptance rubric (surface, feasible_as_asked) - what an honest scope produces.
EXPECTED = {
    "S1": ("conversations_agents", False),
    "S2": ("document_ai", True),
    "S3": ("rag_library", True),
    "S4": ("voxtral", False),
    "S5": ("chat_completions", True),
    "S6": ("conversations_agents", True),
}


def decide(s):
    """Return (surface, feasible_as_asked) for one scenario.

    BUG: this routes ANY tool need straight to Chat Completions, and it reports
    every request as feasible - so it misses the two "not as asked" cases.
    TODO: apply the grounded rules above. Route by capability first, then judge
    feasibility (web/code on a chat-completions-only stack is not feasible; live
    transcription with diarization is not feasible as one model).
    """
    if s["needs_web_or_code_tool"]:
        surface = "chat_completions"
    elif s["doc_extraction"]:
        surface = "document_ai"
    elif s["ground_private_docs_managed"]:
        surface = "rag_library"
    elif s["transcription"]:
        surface = "voxtral"
    else:
        surface = "chat_completions"
    feasible_as_asked = True
    return surface, feasible_as_asked


def main():
    failures = []
    for s in SCENARIOS:
        got = decide(s)
        assert got[0] in SURFACES, f"{s['id']}: unknown surface {got[0]!r}"
        exp = EXPECTED[s["id"]]
        mark = "ok" if got == exp else "XX"
        print(f"  [{mark}] {s['id']}: got={got}  expected={exp}")
        if got != exp:
            failures.append(s["id"])
    if failures:
        raise AssertionError(f"mis-scoped scenarios: {', '.join(failures)}")
    print("TASK3 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK3 FAIL: {e}")
        sys.exit(1)
