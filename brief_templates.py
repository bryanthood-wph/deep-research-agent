"""
Preset texts and a helper to build writer instructions for SMB Decision Briefs.

Functions:
- writer_instructions(template: str, biz: str, location: str) -> str
"""

TEMPLATES: dict[str, str] = {
    "Competitor Snapshot": (
        "Top 5 local competitors near {location}. Pricing, offers, and site SEO notes. "
        "End with 5 actions for the next 14 days."
    ),
    "Local SEO Audit": (
        "Audit {biz} in {location}: NAP consistency, priority keywords, Google Business Profile, "
        "citations, and site speed. Prioritize fixes by effort and impact."
    ),
    "Grant Opportunities": (
        "Active grants for {biz} in {location}: eligibility, deadlines, award sizes, and a prep checklist."
    ),
}

def writer_instructions(template: str, biz: str, location: str) -> str:
    ctx = TEMPLATES[template].format(biz=biz, location=location)
    return (
        "You produce an SMB Decision Brief.\n"
        f"Context: {ctx}\n"
        "Sections: Executive summary (5 bullets); Main brief (5–7 pages, markdown); "
        "Top actions (5 with effort/impact); Sources (links)."
    )
