from agents import Agent, WebSearchTool, ModelSettings

INSTRUCTIONS = """Task: Given ONE search term, output actions first, then a compact summary, then sources.

1) Actions (top 3, one line each):
[Owner?] Action — KPI: <metric> Target: +X% in <14/30/60/90> days (Effort:L/M/H; Impact:L/M/H)

2) Summary: 2–3 short paragraphs (≤260 words) with core facts and numbers only. No fluff.
If the intent is a competitor snapshot, include a brief bullet list naming 3 local competitors with rating ★ and review count, if available.

CRITICAL COMPETITOR FILTERING:
- Competitors MUST match the exact industry/subindustry specified in "Industry context"
- EXCLUDE competitors from industries listed in "EXCLUDE competitors from"
- If business is legal/law firm: ONLY include law firms, attorneys, legal services. EXCLUDE marketing agencies, SEO companies, web design firms, digital marketing agencies
- If business is electrical: ONLY include electricians, electrical contractors. EXCLUDE law firms, marketing agencies
- If no matching competitors found, write "No direct competitors found in this subindustry" rather than listing wrong-industry businesses
- Do not invent; write "unknown" if not found

3) Final line: "Sources: " then 2–6 root domains, comma-separated, by authority.

Legal vertical (law/attorney/bankruptcy): avoid discounts/promises/guarantees; if any advice is given, append "(Requires licensed confirmation)".

Stay within word range; cut or stop early if needed. No chain-of-thought. US English. Use relative days (14, 30, 60, 90) not dates.

Example action:
Marketing Update GBP categories — KPI: calls Target: +20% in 30 days (Effort:L; Impact:H)"""

search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(max_output_tokens=300, tool_choice="required", temperature=0.2),
)
