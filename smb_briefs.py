"""
SMB Decision Briefs orchestrator.
Plans searches → gathers results → writes brief → optionally emails report.
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
from agents import Runner, trace, gen_trace_id
from planner_agent import planner_agent, WebSearchPlan, WebSearchItem
from search_agent import search_agent
from writer_agent import writer_agent, ReportData
from email_agent import send_email_direct
from brief_templates import writer_instructions

# Configure logging for token monitoring
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Token caps for monitoring (must match agent ModelSettings)
TOKEN_CAPS = {
    "PlannerAgent": 200,
    "Search agent": 300,
    "WriterAgent": 900,
    "Email agent": 200,
}

def check_token_usage(agent_name: str, result, cap: int):
    """
    Check if output tokens approach the cap and log warnings.
    Warns at 80%, critical at 90%.
    """
    try:
        # Attempt to extract token usage from result
        usage = getattr(result, 'usage', None)
        if usage:
            completion_tokens = getattr(usage, 'completion_tokens', 0) or getattr(usage, 'output_tokens', 0)
            if completion_tokens > 0:
                pct = (completion_tokens / cap) * 100
                if pct >= 90:
                    logger.warning(
                        f"🚨 CRITICAL: {agent_name} used {completion_tokens}/{cap} tokens ({pct:.0f}%). "
                        f"Output may be truncated, impacting quality!"
                    )
                elif pct >= 80:
                    logger.warning(
                        f"⚠️  WARNING: {agent_name} used {completion_tokens}/{cap} tokens ({pct:.0f}%). "
                        f"Approaching cap—consider reviewing output quality."
                    )
                else:
                    logger.info(f"✓ {agent_name}: {completion_tokens}/{cap} tokens ({pct:.0f}%)")
    except Exception as e:
        logger.debug(f"Could not extract token usage for {agent_name}: {e}")

async def _search_all(plan: WebSearchPlan) -> list[str]:
    """Run all searches concurrently and return text results."""
    async def one(item: WebSearchItem) -> str | None:
        try:
            r = await Runner.run(search_agent, f"Search term: {item.query}\nReason: {item.reason}")
            check_token_usage("Search agent", r, TOKEN_CAPS["Search agent"])
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
        check_token_usage("PlannerAgent", plan_result, TOKEN_CAPS["PlannerAgent"])
        plan = plan_result.final_output_as(WebSearchPlan)

        # 2. Perform searches concurrently
        search_results = await _search_all(plan)

        # 3. Compose writer prompt
        instructions = writer_instructions(template, biz, location)
        writer_prompt = f"Original query: {query}\nSummarized search results: {search_results}"

        # 4. Generate report
        writer_result = await Runner.run(writer_agent, f"{instructions}\n\n{writer_prompt}")
        check_token_usage("WriterAgent", writer_result, TOKEN_CAPS["WriterAgent"])
        report = writer_result.final_output_as(ReportData)

        # 5. Optionally email
        if email:
            subject = f"{template} Brief: {biz} – {location}"
            html_body = report.markdown_report.replace("\n", "<br>")
            send_email_direct(subject, html_body)

        return report
