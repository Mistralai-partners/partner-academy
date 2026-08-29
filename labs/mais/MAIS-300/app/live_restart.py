"""Task 4 live proof: restart a conversation from an earlier entry.

Run: uv run --no-project --with 'mistralai==1.9.11' --with python-dotenv \
       python live_restart.py
Grounded: conversations.start / append build a thread; get_history returns ordered
entries with ids; restart(conversation_id, inputs, from_entry_id) branches into a
NEW conversation, leaving the original untouched.
"""
import os

from dotenv import load_dotenv
from mistralai import Mistral

from mais.entries import pick_branch_entry, is_isolated_branch

load_dotenv("/Users/victor.rojo/source/course-automation/.env")


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    r1 = client.beta.conversations.start(
        inputs="My favorite color is blue. Please acknowledge in one word.",
        model="mistral-small-latest",
    )
    conv_id = r1.conversation_id
    client.beta.conversations.append(
        conversation_id=conv_id,
        inputs="Actually change it: my favorite color is now green. Acknowledge.",
    )
    history = client.beta.conversations.get_history(conversation_id=conv_id)
    entries = history.entries
    # Branch from the FIRST user turn (before the color was changed to green).
    branch_id = pick_branch_entry(entries, role="user", occurrence=1)
    print(f"original conversation: {conv_id}")
    print(f"branching from entry:  {branch_id}")
    r3 = client.beta.conversations.restart(
        conversation_id=conv_id,
        inputs="What is my favorite color? Answer with one word.",
        from_entry_id=branch_id,
    )
    branched_id = r3.conversation_id
    print(f"branched conversation: {branched_id}")
    isolated = is_isolated_branch(conv_id, branched_id)
    print("isolated (new conversation):", isolated)
    assert isolated, "restart did not create a new, isolated conversation"
    print("OK")


if __name__ == "__main__":
    main()
