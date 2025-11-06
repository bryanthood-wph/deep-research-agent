# prompts/common.py
"""Shared prompt constants for action-first research system."""

GLOBAL_HARDENING = (
    "No chain-of-thought. Obey required structure and length exactly. "
    "If inputs are incomplete, produce best-effort but label unknowns. "
    "Do not invent facts or sources. US English. Use relative days (14, 30, 60, 90) not dates."
)

ACTION_LINE_SPEC = (
    "[Owner optional] Action — KPI: <metric> Target: +X% in <14/30/60/90> days "
    "(Effort: L/M/H; Impact: L/M/H)"
)

# Micro examples for token economy
EXAMPLE_ACTIONS = {
    "search": "Marketing Launch fall tune-up email — KPI: booked appts Target: +25% in 30 days (Effort: M; Impact: H)",
    "writer": "Ops Add Saturday service block — KPI: jobs/day Target: +20% in 14 days (Effort: M; Impact: M)",
    "smb": "Owner Update GBP holiday hours — KPI: direction requests Target: +12% in 14 days (Effort: L; Impact: M)",
    "email": "Sales Call lapsed quotes — KPI: closes Target: +20% in 30 days (Effort: M; Impact: H)",
}

