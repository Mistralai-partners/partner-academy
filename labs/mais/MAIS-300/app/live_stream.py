"""Task 1 live proof: stream a conversation and fold the event stream.

Run: uv run --no-project --with 'mistralai==2.9.4' --with python-dotenv \
       python live_stream.py
Grounded: client.beta.conversations.start_stream(inputs=..., model=...) ->
EventStream[ConversationEvents]; each item has .event (type str) and .data.
"""
import os

from dotenv import load_dotenv
from mistralai.client import Mistral

from mais.streaming import fold_events

load_dotenv("/Users/victor.rojo/source/course-automation/.env")


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    stream = client.beta.conversations.start_stream(
        inputs="In one short sentence, what is retrieval-augmented generation?",
        model="mistral-small-latest",
    )
    seen_types = []

    def tap(events):
        for ev in events:
            seen_types.append(ev.event)
            yield ev

    result = fold_events(tap(stream))
    print("event types seen:", sorted(set(seen_types)))
    print("terminated:", result.terminated, "| error:", result.error)
    print("final text:", result.text[:200])
    assert result.terminated, "stream never terminated"
    assert result.text, "no text accumulated"
    print("OK")


if __name__ == "__main__":
    main()
