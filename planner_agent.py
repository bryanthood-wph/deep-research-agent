from pydantic import BaseModel, Field
from agents import Agent, ModelSettings

HOW_MANY_SEARCHES = 3

INSTRUCTIONS = """Return exactly three specific, different search terms for the query.

CRITICAL REQUIREMENTS:
- Each search query MUST include subindustry keywords AND location
- Use provided synonyms where helpful to vary search terms
- DO NOT include excluded industries in any search query
- Avoid generic terms without subindustry qualifiers (e.g., "competitors" alone is forbidden)
- Each query should target the specific subindustry in the specific location

EXAMPLES (guides, not templates):
- For "bankruptcy law" in "Johnson City, TN": "bankruptcy attorney Johnson City TN", "chapter 7 lawyer Johnson City", "bankruptcy law firm Johnson City Tennessee"
- For "EV charger installation" in "Arlington, VA": "EV charger installer Arlington VA", "electric vehicle charging installation Arlington", "EV charger electrician Arlington Virginia"
- For "plumbing services" in "Austin, TX": "plumber Austin TX", "plumbing contractor Austin Texas", "plumbing repair Austin"

Output structure (JSON):
{
  "searches": [
    {"reason": "brief justification", "query": "subindustry-specific search term with location"},
    {"reason": "brief justification", "query": "subindustry-specific search term with location"},
    {"reason": "brief justification", "query": "subindustry-specific search term with location"}
  ]
}"""


class WebSearchItem(BaseModel):
    reason: str = Field(
        description="Your reasoning for why this search is important to the query."
    )
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="A list of web searches to perform to best answer the query."
    )


planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
    model_settings=ModelSettings(max_output_tokens=200, temperature=0.2),
)
