"""A3 starter: a long-running support-triage workflow.

This is a runnable skeleton. The worker auto-discovers workflows under
src/workflows/, so keep this file here. Three interaction handlers are stubbed:

  - add_notification  (should be a SIGNAL: fire-and-forget, no return)
  - get_status        (should be a QUERY: synchronous, read-only)
  - set_priority      (should be an UPDATE: mutates state and returns a value)

Two of them are wired to the WRONG behavior on purpose. Find the symptom, then
match the right primitive to each need. See TASKS.md for the guided build.
"""

import mistralai.workflows as workflows
from datetime import timedelta  # noqa: F401  (used once you add a timeout)


@workflows.workflow.define(name="support_triage")
class SupportTriageWorkflow:
    def __init__(self) -> None:
        # Case-level state. This is what every interaction reads or changes.
        self.case_id: str = ""
        self.status: str = "open"
        self.priority: int = 1
        # Notifications arrive over time. Each entry: {"message": str, "priority": int}
        self.notifications: list[dict] = []
        # Cursor: how many notifications the workflow has already reacted to.
        self.processed: int = 0

    @workflows.workflow.entrypoint
    async def run(self, case_id: str) -> dict:
        self.case_id = case_id
        self.status = "running"

        # The workflow must stay alive for the life of the case and react when a
        # notification arrives, without pinning the CPU.
        while self.status == "running":
            # TODO: notifications never wake the workflow
            # This loop spins as fast as it can and never suspends until new work
            # exists. Because it never yields on a change in state, a delivered
            # signal is not observed durably and the loop burns cycles instead of
            # waiting. A status query taken after a signal shows stale state.
            if len(self.notifications) > self.processed:
                self.processed = len(self.notifications)

        return {
            "case_id": self.case_id,
            "status": self.status,
            "processed": self.processed,
        }

    @workflows.workflow.signal(name="add_notification")
    async def add_notification(self, message: str, priority: int = 1) -> None:
        # A signal is fire-and-forget: record the notification. Declaring the
        # params here is the payload contract the SDK validates (extra or
        # mistyped fields are rejected with HTTP 422).
        self.notifications.append({"message": message, "priority": priority})

    @workflows.workflow.query(name="get_status")
    def get_status(self) -> dict:
        # TODO: this query mutates state — that is the wrong primitive here
        # A dashboard reads status; a read must never change what it reports.
        self.processed += 1
        return {
            "status": self.status,
            "priority": self.priority,
            "notifications": list(self.notifications),
            "notification_count": len(self.notifications),
        }

    @workflows.workflow.update(name="set_priority")
    async def set_priority(self, priority: int) -> dict:
        # TODO: an agent needs to change the case priority and get a confirmation
        # back. Implement the update so it mutates self.priority and RETURNS a
        # confirmation the caller can read synchronously.
        raise NotImplementedError("set_priority update handler is not implemented yet")
