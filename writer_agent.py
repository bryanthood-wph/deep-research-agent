# Import structured data models and agent framework for defining report structure and agent behavior
from pydantic import BaseModel, Field
from agents import Agent

# Define writing behavior emphasizing depth and coherence - contrasts with search_agent's brevity
# Instructions specify outline-first approach to ensure logical flow from search results
INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content, at least 1000 words."
)

# Define report output structure - captures multiple formats for different consumption contexts
# Order matters: summary for quick review, full report for details, questions for follow-up research
class ReportData(BaseModel):
    short_summary: str = Field(
        description="A short 2-3 sentence summary of the findings."
    )

    markdown_report: str = Field(description="The final report")

    follow_up_questions: list[str] = Field(
        description="Suggested topics to research further"
    )


# Instantiate writer agent - requires both INSTRUCTIONS and ReportData defined above
# output_type=ReportData enforces structured output with all three fields (summary, report, questions)
writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData,
)
