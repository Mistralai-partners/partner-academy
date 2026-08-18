"""WFLOW-TSE1 feasibility (STARTER): give the honest architecture answer.

For each customer ask, return a verdict AND the single gating constraint the seller must state out
loud. Winning the technical evaluation means being honest about limits, not over-promising. The
hard cases here are the on-behalf-of (OBO) constraints, which are enforced by the platform.

Right now assess() says GO to everything with no constraint. That is the over-promise this task
exists to prevent. Fix it so each scenario returns the correct verdict and gating constraint.

verdict is one of: "GO", "GO_WITH_CAVEAT", "NO_FIT"
constraint is one of:
- "none"
- "obo_requires_hardened_deployment"
- "obo_incompatible_with_schedules"
- "side_effects_go_in_activities"

Grounded in the pinned Workflows docs (SHA a3e0f0c...): building-workflows/on_behalf_of.md,
managing-workflows-in-production/hardened_deployments.md, building-workflows/activities/basics.md.
See tasks.md T4.
"""
from __future__ import annotations


def assess(scenario_id: str) -> dict:
    # TODO T4: return the correct verdict + constraint for each scenario.
    #
    # - "per_user_connectors": each user must see their OWN connector data.
    # - "scheduled_per_user_report": a nightly cron report that ALSO runs as each user's identity.
    # - "durable_slow_partner_call": a live call to a slow partner API that must survive restarts.
    #
    # The stub below over-promises. Replace it.
    return {"verdict": "GO", "constraint": "none"}
