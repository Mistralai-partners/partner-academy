"""WFLOW-TSE1 feasibility (SOLUTION): give the honest architecture answer.

For each customer ask, return a verdict AND the single gating constraint the seller must state out
loud. Winning the technical evaluation means being honest about limits, not over-promising. The
hard cases here are the on-behalf-of (OBO) constraints, which are enforced by the platform and are
exactly where an over-eager demo gets a seller in trouble.

verdict is one of:
- "GO"              fits cleanly as described
- "GO_WITH_CAVEAT" fits, but the customer must accept a stated prerequisite
- "NO_FIT"         cannot be built as stated; the design must change

constraint is one of:
- "none"                              no gating constraint to call out
- "obo_requires_hardened_deployment"  OBO workflows require a hardened deployment to register
- "obo_incompatible_with_schedules"   OBO cannot be combined with schedules (no triggering user)
- "side_effects_go_in_activities"     external I/O must live in an activity to be durable/retried

Grounded in the pinned Workflows docs (SHA a3e0f0c...): building-workflows/on_behalf_of.md,
managing-workflows-in-production/hardened_deployments.md, building-workflows/activities/basics.md,
building-workflows/workflows/determinism.md.
"""
from __future__ import annotations


def assess(scenario_id: str) -> dict:
    if scenario_id == "per_user_connectors":
        # Each user must see their OWN connector data -> OBO (on_behalf_of=True). OBO registers only
        # on a hardened deployment, so this is a GO once the customer accepts that prerequisite.
        return {"verdict": "GO_WITH_CAVEAT", "constraint": "obo_requires_hardened_deployment"}

    if scenario_id == "scheduled_per_user_report":
        # A nightly cron report that ALSO runs as each user's identity cannot be built as stated:
        # OBO cannot be combined with schedules, because a scheduled run has no triggering user.
        return {"verdict": "NO_FIT", "constraint": "obo_incompatible_with_schedules"}

    if scenario_id == "durable_slow_partner_call":
        # A live call to a slow partner API that must survive worker restarts fits cleanly: put the
        # HTTP call in an activity (auto-retried, never replayed) and keep the body deterministic.
        return {"verdict": "GO", "constraint": "side_effects_go_in_activities"}

    raise ValueError(f"unknown scenario_id: {scenario_id}")
