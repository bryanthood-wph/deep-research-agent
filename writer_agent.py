from pydantic import BaseModel, Field
from agents import Agent, ModelSettings

INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query and compact search findings.\n"
    "Produce a concise brief in markdown.\n"
    "Length: 1–3 pages, between 250 and 500 words total.\n"
    "Structure:\n"
    "- Executive summary: 4–6 bullets (terse).\n"
    "- Main findings: 6–10 bullets with short evidence (root domains only).\n"
    "- Top 5 recommended actions (one line each).\n"
    "Constraints: stay within 250–500 words; avoid tables; avoid fluff; be precise."
)


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
    model_settings=ModelSettings(max_output_tokens=900, temperature=0.3),
)
