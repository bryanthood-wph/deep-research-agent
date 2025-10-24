# Import agent framework components - WebSearchTool provides web search capability, ModelSettings enforces tool usage
from agents import Agent, WebSearchTool, ModelSettings

# Define search behavior emphasizing brevity and density - output feeds into writer_agent so must be concise
INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "produce a concise summary of the results. The summary must 2-3 paragraphs and less than 300 "
    "words. Capture the main points. Write succintly, no need to have complete sentences or good "
    "grammar. This will be consumed by someone synthesizing a report, so its vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary itself."
)

# Instantiate search agent - requires INSTRUCTIONS defined above
# WebSearchTool with "low" context saves tokens since multiple searches run in parallel
# tool_choice="required" forces agent to use search tool rather than just generating text
search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)
