"""A3 solution: a long-running support-triage workflow.

Each interaction primitive is matched to its need:

  - add_notification  SIGNAL: fire-and-forget append; the entrypoint wakes on it
                      via wait_condition instead of busy-looping.
  - get_status        QUERY: synchronous, read-only. It never mutates state.
  - set_priority      UPDATE: mutates state, runs a small activity, and returns a
                      confirmation the caller reads synchronously.
"""

import mistralai.workflows as workflows
from datetime import timedelta  # noqa: F401  (available for wait_condition timeouts)


class PriorityError(ValueError):
    """Raised when an update is asked to set an out-of-range priority."""


# Valid case-priority band. Kept small so the stretch task is easy to prove.
MIN_PRIORITY = 1
MAX_PRIORITY = 5


@workflows.workflow.define(name="support_triage")
class SupportTriageWorkflow:
    def __init__(self) -> None:
        self.case_id: str = ""
        self.status: str = "open"
        self.priority: int = 1
        # Each entry: {"message": str, "priority": int}
        self.notifications: list[dict] = []
        # Cursor: how many notifications the workflow has already reacted to.
        self.processed: int = 0

    @workflows.workflow.entrypoint
    async def run(self, case_id: str) -> dict:
        self.case_id = case_id
        self.status = "running"

        # Stay alive for the life of the case. wait_condition suspends the
        # workflow until a new notification arrives (or the case closes), so a
        # signal wakes it durably and cheaply, with no busy-wait.
        while self.status == "running":
            await workflows.workflow.wait_condition(
                lambda: len(self.notifications) > self.processed
                or self.status != "running"
            )
            # React to newly arrived notifications WITHOUT discarding them, so a
            # status query always reflects the full case history. Advancing the
            # cursor (rather than clearing the list) is what keeps the query and
            # the workflow in agreement.
            self.processed = len(self.notifications)

        return {
            "case_id": self.case_id,
            "status": self.status,
            "processed": self.processed,
        }

    @workflows.workflow.signal(name="add_notification")
    async def add_notification(self, message: str, priority: int = 1) -> None:
        # Fire-and-forget: append and return nothing. The declared params are the
        # payload contract; the SDK rejects extra or mistyped fields with HTTP 422.
        self.notifications.append({"message": message, "priority": priority})

    @workflows.workflow.query(name="get_status")
    def get_status(self) -> dict:
        # Non-async, read-only. A query must be side-effect-free: it reports state
        # and never changes it.
        return {
            "status": self.status,
            "priority": self.priority,
            "notifications": list(self.notifications),
            "notification_count": len(self.notifications),
        }

    @workflows.workflow.update(name="set_priority")
    async def set_priority(self, priority: int) -> dict:
        # An update is the right primitive when the caller needs a confirmed
        # result. It may mutate state and may run activities (await them).
        # Enforce the valid band HERE, in the update, so a bad request is
        # rejected before state changes and the caller is told why. A signal
        # could not do this: it returns nothing, so the caller would never learn
        # the request was refused.
        if not (MIN_PRIORITY <= priority <= MAX_PRIORITY):
            raise PriorityError(
                f"priority {priority} is out of range "
                f"[{MIN_PRIORITY}, {MAX_PRIORITY}]; state unchanged"
            )

        previous = self.priority
        # Run a tiny activity to record the change, then mutate state. An activity
        # is a module-level function decorated with @workflows.activity(); call it
        # from inside the handler by awaiting it directly.
        note = await record_priority_change(self.case_id, previous, priority)
        self.priority = priority

        return {
            "ok": True,
            "case_id": self.case_id,
            "previous_priority": previous,
            "priority": self.priority,
            "note": note,
        }


@workflows.activity()
async def record_priority_change(case_id: str, previous: int, new: int) -> str:
    return f"case {case_id}: priority {previous} -> {new}"
