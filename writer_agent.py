from pydantic import BaseModel, Field
from agents import Agent, ModelSettings
import os

# Feature flag: Use structured parsing (new schema) vs legacy markdown
USE_STRUCTURED_PARSING = os.environ.get("USE_STRUCTURED_PARSING", "false").lower() == "true"

# Legacy instructions (for backward compatibility)
INSTRUCTIONS_LEGACY = """Markdown only. 220–420 words total.

REQUIRED ACTION FORMAT (everything on ONE line):
Action — KPI: <metric> Target: +X% in <14/30/60/90> days (Effort:L/M/H; Impact:L/M/H) | HOW: 1) <step> 2) <step> 3) <step> 4) <step> | TOOLS: 1) <tool> 2) <tool> 3) <tool> (ordered by market share/brand recognition)

ACTION TITLE RULES:
- Every action title MUST be descriptive and contain at least ONE subindustry-specific term
- FORBIDDEN: Generic titles like 'Action', 'Update website', 'Launch campaign', 'Improve service', 'Conduct analysis', 'Evaluate offerings', 'Assess strategies', 'Comprehensive competitor pricing analysis'
- REQUIRED: Specific subindustry service/product/capability + action verb
- VALIDATION: Before outputting, check each action title - if it could apply to ANY industry, it's WRONG. Rewrite it with subindustry-specific terms.

HOW STEPS REQUIREMENTS:
HOW steps MUST integrate tool references inline: 'Use [tool category] (like ToolName) to [specific action with subindustry context]'

BAD (generic, no tools): '1) Conduct audit 2) Identify gaps 3) Optimize content 4) Implement changes'
BAD (generic tools, no subindustry context): '1) Use competitor analysis tools (like SimilarWeb) to gather pricing data 2) Use spreadsheet software (like Excel) to organize'

GOOD PATTERNS (guides, not templates - adapt to ANY subindustry):
- Legal/Bankruptcy: '1) Use practice management software (like Clio or MyCase) to audit current client intake workflow and identify ABA compliance gaps 2) Use legal content platforms (like Nolo) to create Chapter 7 vs Chapter 13 comparison chart with local court filing fees'
- Electrical/EV: '1) Use field service management software (like ServiceTitan or Jobber) to analyze current scheduling data and identify weekend availability gaps 2) Use website plugins (like WPForms with EV calculator) to build EV charger installation cost estimator'
- Restaurant: '1) Use POS analytics (like Toast or Square Dashboard) to identify peak ordering times and staff scheduling gaps 2) Use reservation platforms (like OpenTable) to implement waitlist management for weekend brunch'

Requirements: Start with 'Use [tool category]', provide tool example in '(like ToolName)', include subindustry-specific action with concrete details (not generic verbs like 'gather', 'organize', 'analyze', 'summarize').
VALIDATION: If a HOW step could apply to any industry, it's too generic - rewrite with subindustry-specific details.

TOOLS DISCOVERY:
Recommend 3 tools ordered by market share FOR THE SPECIFIC INDUSTRY.

DISCOVERY THINKING (internal):
1. What is the PRIMARY operational workflow? (Legal→case/client management; Electrical→service dispatch; Restaurant→order management)
2. What software category dominates? (Legal→practice management; Electrical→field service management; Restaurant→POS systems)
3. What are the TOP 3 brands by market share?

CRITICAL RULES:
- AVOID generic marketing tools (SEMrush, Hootsuite, Canva, Mailchimp, Facebook Ads) UNLESS action is explicitly about marketing/advertising/social media campaigns
- AVOID generic analysis tools (SimilarWeb, Excel, Google Sheets, Statista) UNLESS action is explicitly about competitive analysis AND no subindustry-specific tool exists
- FORBIDDEN: Do NOT use company names as tools. If you see a company name in search results (e.g., 'EvolveNova', 'Corporate Marketing', 'Identite Marketing'), it is a COMPETITOR, not a tool. Use actual software tools instead.
- FORBIDDEN: Do NOT confuse competitors with tools. Tools are software platforms (Clio, ServiceTitan, Toast). Competitors are businesses (law firms, electricians, restaurants).
- For website/SEO: Use Google Business Profile, Google Search Console, Ahrefs, Screaming Frog
- For operations/CRM: Use subindustry-specific operational tools, NOT generic CRMs like HubSpot
- VALIDATION: Before outputting, check each tool - if it's generic (works for any industry), ask "Is there a subindustry-specific alternative?" If yes, use that instead.
- VALIDATION: Before outputting, verify each tool is actual software (not a company name from competitors list). If it's a company name, replace it with appropriate software tool.

EXAMPLE PATTERNS (guides, not rigid templates):
- Legal practice → Clio, MyCase, PracticePanther
- Electrical/HVAC/Plumbing → ServiceTitan, Jobber, FieldEdge
- Restaurant → Toast, Square, Clover
- Dental practice → Dentrix, Eaglesoft, Open Dental

RULES:
- Top 5 actions.
- FIRST action must be foundational (audit, baseline, tool setup).
- Every action MUST include HOW (4+ numbered steps with tool references inline) and TOOLS (3 industry-appropriate tools). Missing either makes it incomplete.
- All actions for the requesting business only (no Owner prefixes). Tie each to competitor gaps or market trends.

Executive summary: 4–6 bullets. Write like an industry analyst for the local market. Each bullet MUST mention location explicitly.

HARD REQUIREMENT: At least ONE bullet must reference a UNIQUE local factor beyond generic 'growth' or 'seasonal trends'. Consider: economic drivers (major employers, university, military base), demographics, geography, local regulations, regional events.

Standard bullets: (a) quantified local growth/demand metric, (b) local trend with operational implication, (c) named tools/apps used locally, (d) competitive dynamics.

Main findings: 6–10 bullets with (rootdomain). These are RESEARCH INSIGHTS, not action items.
- Show competitor specifics: pricing, services, ratings, offers.
- Show market patterns: gaps, trends, benchmarks supporting the Action Board.
- Each bullet ends with (source.com).
- If competitor snapshot, add "Local Competitors" with 3–5 REAL competitor names + ★ rating + review count from search results.
- CRITICAL: Competitor names MUST match the exact subindustry of the business.
- FORBIDDEN: Do NOT include competitors from wrong industries (e.g., if business is legal, do NOT include electrical/plumbing/HVAC/restaurant/marketing/SEO/web design competitors).
- SPECIFIC: If business is legal firm, EXCLUDE marketing agencies (Identite Marketing, EvolveNova, Corporate Marketing), SEO companies, web design firms. ONLY include law firms, attorneys, legal services.
- SPECIFIC: If business is electrical, EXCLUDE law firms, marketing agencies. ONLY include electricians, electrical contractors.
- FORBIDDEN: Placeholder names like "ABC Electric", "XYZ Power", "Company A", "Business B", "Firm 1", "Competitor X"
- REQUIRED: Filter competitors by subindustry - only include businesses in the SAME subindustry.
- REQUIRED: Use actual competitor names from search results only. Extract real names from the research data you received.
- If search results contain competitors from wrong industries, IGNORE them and only use same-subindustry competitors.
- If no same-subindustry competitors found, write "No direct competitors found in search results for this subindustry in location" rather than inventing placeholders.
- VALIDATION: Before listing competitors, verify each one matches the subindustry. If unsure, exclude it.

Dogs Not Barking: REQUIRED 2 creative market gaps + 1 net-new brainstorming idea (3 total items).

APPROACH: Analyze the search results you received. Look for patterns, missing services, unmet customer needs. Think creatively about location geography, market dynamics, and industry patterns. What customer needs are NOT being met based on the research? What service gaps exist that competitors aren't addressing?

REQUIREMENTS:
- Exactly 2 gaps: Creative analysis of unmet customer needs or service gaps specific to location and industry, BASED ON THE RESEARCH DATA you received
- Exactly 1 brainstorming: A fun, net-new concept that doesn't currently exist - something innovative that gets users thinking, inspired by the research findings
- Each gap must reference geography/market/industry factors from your research, not generic "lack X"
- NO generic phrases: Do NOT write 'lack weekend availability', 'limited online booking' UNLESS you have specific local evidence
- Each gap must reference an industry-specific service, product, or operational capability
- Brainstorming must be prefixed with "Brainstorming:" and describe a completely new concept/service/approach
- DO NOT copy findings verbatim - synthesize creative insights FROM the research

EXAMPLES (guides, not templates):
- Gap (based on research): "No competitors offer EV charger installation financing despite 40% of Arlington homeowners expressing interest (from search data)"
- Gap (based on research): "ETSU's 14,000-student population creates demand for evening legal consultations, but only 2 of 12 firms offer after-hours service (from competitor analysis)"
- Brainstorming: "Brainstorming: Partner with local EV dealerships to offer 'EV-ready home certification' packages that include pre-wiring and installation credits - a new service category that doesn't exist yet"

CRITICAL: Before outputting, count your Dogs Not Barking items - you must have exactly 3 (2 gaps + 1 brainstorming). Base gaps on research data, not generic assumptions.

Legal vertical: avoid discounts/guarantees; append "(Requires licensed confirmation)" to regulatory-sensitive advice.

WORD QUOTAS:
- Total output: 220–420 words
- Action Board: Present with 5 actions
- Executive Summary: 4–6 bullets (mandatory)
- Dogs Not Barking: 2 gaps + 1 Brainstorming (mandatory, 3 total)
- Main Findings: 6–10 bullets

Stay within 220–420 words. No tables/images. Quantify with units and relative days (14, 30, 60, 90). No chain-of-thought. US English. Use relative days not dates. DO NOT copy examples verbatim—use them as thinking guides.

SELF-CHECK (before returning output):
Verify ALL of the following:
(a) Competitor names match the subindustry (not wrong industries)
(b) Action titles contain subindustry-specific terms (not generic 'Conduct analysis', 'Evaluate offerings')
(c) Tools are subindustry-appropriate (not generic SimilarWeb/Excel unless explicitly justified)
(d) HOW steps are subindustry-specific (not generic 'gather data', 'organize findings')
(e) Dogs Not Barking has exactly 2 gaps + 1 brainstorming tied to location and subindustry
If ANY check fails, REVISE before returning.

Output structure (JSON):
{
  "short_summary": "2-3 sentence summary",
  "markdown_report": "full markdown with Action Board first",
  "follow_up_questions": ["question 1", "question 2", "question 3"]
}"""

# New structured instructions (JSON schema only)
INSTRUCTIONS_STRUCTURED = """Return ONLY valid JSON. No markdown. No explanations.

CRITICAL: You must return JSON matching this exact schema:

{
  "schema_version": "1.0",
  "short_summary": "2-3 sentence summary (20-300 chars)",
  "actions": [
    {
      "title": "Action title (8-120 chars, MUST contain industry-specific term)",
      "kpi": "Metric name (3-60 chars)",
      "target_percent": "+X%",
      "target_days": 30,
      "how_steps": ["Use [category] (like Tool) to [action]", "Use [category] (like Tool) to [action]", "Use [category] (like Tool) to [action]"],
      "tools": ["Tool 1", "Tool 2", "Tool 3"],
      "effort": "L" or "M" or "H",
      "impact": "L" or "M" or "H"
    }
  ],
  "exec_summary": ["bullet 1", "bullet 2", "bullet 3", "bullet 4"],
  "findings": ["finding 1", "finding 2", "finding 3", "finding 4", "finding 5", "finding 6"],
  "gaps": ["gap 1", "gap 2", "gap 3"],
  "sources": [
    {"url": "https://example.com", "citation": "example.com"},
    {"url": null, "citation": "(local research)"}
  ]
}

REQUIREMENTS:
- Exactly 5 actions. First must be foundational (audit/baseline/tool setup).
- Each action: title (8-120 chars, MUST contain subindustry-specific term, FORBIDDEN: 'Action', 'Update website', 'Launch campaign', 'Conduct analysis', 'Evaluate offerings', 'Assess strategies'), kpi (3-60 chars), target_percent (+X% format), target_days (14, 30, 60, or 90), exactly 3 how_steps, tools (array of 3 strings, ordered by market share), effort (L/M/H), impact (L/M/H).
- HOW STEPS: Each step MUST use format 'Use [tool category] (like ToolName) to [specific action with subindustry context]'. Include subindustry-specific verb+object pairs, not generic templates. AVOID generic verbs like 'gather', 'organize', 'analyze', 'summarize'.
- TOOLS: Recommend 3 tools ordered by market share FOR THE SPECIFIC SUBINDUSTRY. AVOID generic marketing tools (SEMrush, Hootsuite, Canva, Mailchimp, Facebook Ads) UNLESS action is explicitly about marketing. AVOID generic analysis tools (SimilarWeb, Excel, Google Sheets, Statista) UNLESS action is explicitly about competitive analysis AND no subindustry-specific tool exists. For operations/CRM: Use subindustry-specific operational tools, NOT generic CRMs like HubSpot.
- Executive summary: 4-6 bullets (10-240 chars each). Each bullet MUST mention location explicitly. At least ONE bullet must reference a UNIQUE local factor (economic drivers, demographics, geography, local regulations, regional events) beyond generic 'growth' or 'seasonal trends'.
- Main findings: 6-10 bullets (10-240 chars each) with (source.com). RESEARCH INSIGHTS, not actions.
- CRITICAL: Competitor names MUST match the exact subindustry. Filter competitors by subindustry - only include businesses in the SAME subindustry. If business is legal firm, EXCLUDE marketing agencies, SEO companies, web design firms. If business is electrical, EXCLUDE law firms, marketing agencies. If search results contain competitors from wrong industries, IGNORE them. If no same-subindustry competitors found, write "No direct competitors found in search results for this subindustry in location".
- FORBIDDEN: Do NOT use company names as tools. If you see a company name in search results (e.g., 'EvolveNova', 'Corporate Marketing'), it is a COMPETITOR, not a tool. Use actual software tools instead.
- Gaps: REQUIRED exactly 2 creative market gaps + 1 net-new brainstorming idea (3 total). APPROACH: Analyze search results for patterns, missing services, unmet customer needs. Think creatively about location geography, market dynamics, and industry patterns. REQUIREMENTS: Exactly 2 gaps based on research data (creative analysis of unmet needs/service gaps specific to location and industry), exactly 1 brainstorming (net-new concept prefixed with "Brainstorming:"). Each gap must reference geography/market/industry factors from research, not generic "lack X". NO generic phrases unless specific local evidence. DO NOT copy findings verbatim - synthesize creative insights FROM research.
- Sources: 2-10 items (URLs or citations like "(local research)").

WORD QUOTAS:
- Total output: 220–420 words
- Action Board: Present with 5 actions
- Executive Summary: 4–6 bullets (mandatory)
- Dogs Not Barking: 2 gaps + 1 Brainstorming (mandatory, 3 total)
- Main Findings: 6–10 bullets

Legal vertical: append "(Requires licensed confirmation)" to regulatory advice.

SELF-CHECK (before returning):
Verify ALL: (a) Competitor names match subindustry, (b) Action titles contain subindustry-specific terms, (c) Tools are subindustry-appropriate, (d) HOW steps are subindustry-specific, (e) Dogs Not Barking has exactly 2 gaps + 1 brainstorming. If ANY check fails, REVISE before returning.

DO NOT copy examples verbatim—use them as thinking guides.

Return ONLY the JSON object. No markdown, no code blocks, no explanations."""

# Use structured if flag enabled
INSTRUCTIONS = INSTRUCTIONS_STRUCTURED if USE_STRUCTURED_PARSING else INSTRUCTIONS_LEGACY


class ReportData(BaseModel):
    short_summary: str = Field(
        description="A short 2-3 sentence summary of the findings."
    )

    markdown_report: str = Field(description="The final report")

    follow_up_questions: list[str] = Field(
        description="Suggested topics to research further"
    )


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData,
    model_settings=ModelSettings(max_output_tokens=900, temperature=0.2),  # Lower temp for determinism, reduced tokens for word quota control
)
