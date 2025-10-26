"""
SMB Decision Briefs orchestrator.
Plans searches → gathers results → writes brief → optionally emails report.
"""

import asyncio
from agents import Runner, trace, gen_trace_id
from planner_agent import planner_agent, WebSearchPlan, WebSearchItem
from search_agent import search_agent
from writer_agent import writer_agent, ReportData
from email_agent import send_email
from brief_templates import writer_instructions

async def _search_all(plan: WebSearchPlan) -> list[str]:
    """Run all searches concurrently and return text results."""
    async def one(item: WebSearchItem) -> str | None:
        try:
            r = await Runner.run(search_agent, f"Search term: {item.query}\nReason: {item.reason}")
            return str(r.final_output)
        except Exception:
            return None

    tasks = [asyncio.create_task(one(s)) for s in plan.searches]
    return [r for r in await asyncio.gather(*tasks) if r]

async def generate_brief(query: str, template: str, biz: str, location: str, email: bool = False) -> ReportData:
    """Full brief generation pipeline."""
    tid = gen_trace_id()
    with trace("SMB Brief", trace_id=tid):
        # 1. Build the research plan
        plan_result = await Runner.run(planner_agent, f"Query: {query}")
        plan = plan_result.final_output_as(WebSearchPlan)

        # 2. Perform searches concurrently
        search_results = await _search_all(plan)

        # 3. Compose writer prompt
        instructions = writer_instructions(template, biz, location)
        writer_prompt = f"Original query: {query}\nSummarized search results: {search_results}"

        # 4. Generate report
        writer_result = await Runner.run(writer_agent, f"{instructions}\n\n{writer_prompt}")
        report = writer_result.final_output_as(ReportData)

        # 5. Optionally email
        if email:
            subject = f"{template} Brief: {biz} – {location}"
            html_body = report.markdown_report.replace("\n", "<br>")
            send_email(subject, html_body)

        return report
