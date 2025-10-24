# Import structured data models and agent framework for defining agent behavior and output schemas
from pydantic import BaseModel, Field
from agents import Agent

# Define number of search queries to generate - affects search breadth vs depth tradeoff
HOW_MANY_SEARCHES = 5

# Agent instructions use HOW_MANY_SEARCHES to ensure consistent output length
INSTRUCTIONS = f"You are a helpful research assistant. Given a query, come up with a set of web searches \
to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for."

# Define individual search item structure - must precede WebSearchPlan since it's used in its list
class WebSearchItem(BaseModel):
    reason: str = Field(
        description="Your reasoning for why this search is important to the query."
    )
    query: str = Field(description="The search term to use for the web search.")


# Define complete search plan structure - aggregates WebSearchItems defined above
class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="A list of web searches to perform to best answer the query."
    )


# Instantiate planner agent - requires all components above (INSTRUCTIONS, WebSearchPlan with nested WebSearchItem)
# output_type enforces structured response matching WebSearchPlan schema
planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)
