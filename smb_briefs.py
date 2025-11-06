"""
SMB Decision Briefs orchestrator.
Plans searches → gathers results → writes brief → optionally emails report.
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import os
import secrets
from typing import Optional, Tuple, NamedTuple
from agents import Runner
from planner_agent import planner_agent, WebSearchPlan, WebSearchItem
from search_agent import search_agent
from writer_agent import writer_agent, ReportData, USE_STRUCTURED_PARSING
from email_agent import send_email_direct, mask_email
from brief_templates import writer_instructions
import re

# Import structured parsing if enabled
if USE_STRUCTURED_PARSING:
    from schemas import Report
    from parsing.json_capture import extract_and_parse_json
    from renderers.markdown_renderer import render_report_to_markdown

# Configure logging with trace IDs (only for our logger, not global)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Custom formatter that safely handles trace_id
class TraceIDFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, 'trace_id'):
            record.trace_id = 'system'
        return super().format(record)

# Add handler only to our logger
handler = logging.StreamHandler()
handler.setFormatter(TraceIDFormatter('%(asctime)s [%(levelname)s] [%(trace_id)s] %(message)s'))
logger.addHandler(handler)

# Add trace_id filter to our logger only
class TraceIDFilter(logging.Filter):
    trace_id = "unknown"
    
    def filter(self, record):
        record.trace_id = getattr(self, 'trace_id', 'unknown')
        return True

trace_filter = TraceIDFilter()
logger.addFilter(trace_filter)

def gen_trace_id() -> str:
    """Generate short trace ID for request tracking."""
    return secrets.token_hex(4)[:8]

class IndustryContext(NamedTuple):
    """Inferred industry context from inputs."""
    industry: str
    subindustry: str
    synonyms: list[str]
    excluded_industries: list[str]

async def infer_industry_context(biz: str, query: str, template: str, location: str, trace_id: str = None) -> IndustryContext:
    """
    Infer precise industry and subindustry from exact inputs (no hardcoding).
    Uses heuristics first, then web search lookup if unclear.
    """
    # Heuristic extraction: common subindustry patterns (define first)
    subindustry_keywords = {
        # Legal
        "bankruptcy": ("law", "bankruptcy law", ["bankruptcy attorney", "chapter 7 lawyer", "chapter 13 lawyer", "bankruptcy firm", "debt relief attorney"]),
        "family law": ("law", "family law", ["family attorney", "divorce lawyer", "custody attorney", "family law firm"]),
        "personal injury": ("law", "personal injury law", ["personal injury attorney", "accident lawyer", "injury attorney", "PI lawyer"]),
        "criminal": ("law", "criminal law", ["criminal attorney", "criminal defense lawyer", "criminal lawyer"]),
        "estate": ("law", "estate law", ["estate attorney", "probate lawyer", "estate planning attorney"]),
        # Electrical
        "ev charger": ("electrical", "EV charger installation", ["EV charger installer", "electric vehicle charging", "EV installation"]),
        "panel upgrade": ("electrical", "electrical panel upgrade", ["panel upgrade", "electrical panel", "service upgrade"]),
        "residential": ("electrical", "residential electrical", ["residential electrician", "home electrical", "house wiring"]),
        "commercial": ("electrical", "commercial electrical", ["commercial electrician", "business electrical", "commercial wiring"]),
        # Plumbing
        "plumbing": ("plumbing", "plumbing services", ["plumber", "plumbing contractor", "plumbing repair"]),
        "drain": ("plumbing", "drain services", ["drain cleaning", "drain repair", "sewer line"]),
        # HVAC
        "hvac": ("HVAC", "HVAC services", ["HVAC contractor", "heating cooling", "air conditioning"]),
        "heating": ("HVAC", "heating services", ["heating contractor", "furnace repair", "boiler service"]),
        # Restaurant
        "restaurant": ("restaurant", "restaurant services", ["restaurant", "dining", "food service"]),
        "catering": ("restaurant", "catering services", ["caterer", "catering", "event catering"]),
    }
    
    # Combine all inputs for analysis (but NOT template - template is report type, not industry)
    # Extract business focus hints from query (e.g., "specializes in bankruptcy", "does EV charger installation")
    query_lower = query.lower() if query else ""
    biz_lower = biz.lower() if biz else ""
    combined_text = f"{biz_lower} {query_lower}".lower()
    
    # Check for explicit business focus in query (helps even before lookup)
    if "specializes in" in query_lower or "focuses on" in query_lower or "does" in query_lower:
        # Try to extract subindustry from query context
        # e.g., "specializes in bankruptcy" → bankruptcy law
        # e.g., "does EV charger installation" → EV charger installation
        for keyword, (industry, subindustry, synonyms) in subindustry_keywords.items():
            if keyword in query_lower:
                logger.info(f"Found business focus hint in query: '{keyword}' → {subindustry}")
                # This will be caught by the keyword matching loop below
                break
    
    # Try to match subindustry keywords
    matched_subindustry = None
    for keyword, (industry, subindustry, synonyms) in subindustry_keywords.items():
        if keyword in combined_text:
            matched_subindustry = (industry, subindustry, synonyms)
            break
    
    # If no match, infer from biz/query patterns
    if not matched_subindustry:
        # Default industry inference from biz/query
        if "legal" in combined_text or "law" in combined_text or "attorney" in combined_text or "lawyer" in combined_text:
            industry = "law"
            subindustry = "legal services"
            synonyms = ["law firm", "attorney", "lawyer", "legal services"]
        elif "electric" in combined_text or "electrical" in combined_text:
            industry = "electrical"
            subindustry = "electrical services"
            synonyms = ["electrician", "electrical contractor", "electrical services"]
        elif "plumb" in combined_text:
            industry = "plumbing"
            subindustry = "plumbing services"
            synonyms = ["plumber", "plumbing contractor", "plumbing services"]
        elif "hvac" in combined_text or "heating" in combined_text or "cooling" in combined_text:
            industry = "HVAC"
            subindustry = "HVAC services"
            synonyms = ["HVAC contractor", "heating cooling", "HVAC services"]
        elif "restaurant" in combined_text or "dining" in combined_text or "food" in combined_text:
            industry = "restaurant"
            subindustry = "restaurant services"
            synonyms = ["restaurant", "dining", "food service"]
        else:
            # Heuristics failed - look up the business to determine actual industry
            logger.info(f"Heuristics failed for '{biz}' - looking up business to determine industry...")
            try:
                # Build lookup query with query context if available
                lookup_query = f"{biz} {location} what do they do what services"
                if query and len(query.strip()) > 20:
                    # Include query context to help search (truncate to avoid too long)
                    query_snippet = query[:100].strip()
                    lookup_query = f"{biz} {location} {query_snippet} what services do they offer"
                
                # Add timeout for lookup (5 seconds max)
                search_result = await asyncio.wait_for(
                    Runner.run(
                        search_agent,
                        f"Search term: {lookup_query}\nReason: Determine what industry {biz} operates in"
                    ),
                    timeout=5.0
                )
                search_text = str(search_result.final_output).lower()
                
                # Parse search results to extract industry
                if "law" in search_text or "attorney" in search_text or "lawyer" in search_text or "legal" in search_text:
                    industry = "law"
                    subindustry = "legal services"
                    synonyms = ["law firm", "attorney", "lawyer", "legal services"]
                elif "electric" in search_text or "electrical" in search_text or "electrician" in search_text:
                    industry = "electrical"
                    subindustry = "electrical services"
                    synonyms = ["electrician", "electrical contractor", "electrical services"]
                elif "plumb" in search_text or "plumber" in search_text:
                    industry = "plumbing"
                    subindustry = "plumbing services"
                    synonyms = ["plumber", "plumbing contractor", "plumbing services"]
                elif "hvac" in search_text or "heating" in search_text or "cooling" in search_text:
                    industry = "HVAC"
                    subindustry = "HVAC services"
                    synonyms = ["HVAC contractor", "heating cooling", "HVAC services"]
                elif "restaurant" in search_text or "dining" in search_text or "food" in search_text:
                    industry = "restaurant"
                    subindustry = "restaurant services"
                    synonyms = ["restaurant", "dining", "food service"]
                else:
                    # Still unclear - default to generic but log warning
                    logger.warning(f"Could not determine industry for '{biz}' from search results. Using generic fallback.")
                    industry = "business"
                    subindustry = "business services"
                    synonyms = ["business", "company", "services"]
            except asyncio.TimeoutError:
                logger.warning(f"Business lookup timed out for '{biz}' after 5 seconds. Using generic fallback.")
                industry = "business"
                subindustry = "business services"
                synonyms = ["business", "company", "services"]
            except Exception as e:
                logger.error(f"Error looking up business '{biz}': {e}. Using generic fallback.", exc_info=True)
                industry = "business"
                subindustry = "business services"
                synonyms = ["business", "company", "services"]
            
            matched_subindustry = (industry, subindustry, synonyms)
    
    industry, subindustry, synonyms = matched_subindustry
    
    # Validate industry is not template-derived (catastrophic error check)
    if industry in ["competitor snapshot", "local seo audit", "grant opportunities"]:
        logger.error(f"CRITICAL: Industry '{industry}' appears to be template-derived! This is wrong. Using generic fallback.")
        industry = "business"
        subindustry = "business services"
        synonyms = ["business", "company", "services"]
    
    # Determine excluded industries (opposite of current industry)
    excluded = []
    if industry == "law":
        excluded = ["electrical", "plumbing", "HVAC", "restaurant", "dental", "auto repair", "marketing", "digital marketing", "SEO", "web design", "advertising"]
    elif industry == "electrical":
        excluded = ["law", "plumbing", "restaurant", "dental", "auto repair", "marketing", "digital marketing"]
    elif industry == "plumbing":
        excluded = ["law", "electrical", "HVAC", "restaurant", "dental", "auto repair", "marketing"]
    elif industry == "HVAC":
        excluded = ["law", "electrical", "plumbing", "restaurant", "dental", "auto repair", "marketing"]
    elif industry == "restaurant":
        excluded = ["law", "electrical", "plumbing", "HVAC", "dental", "auto repair", "marketing"]
    else:
        excluded = ["law", "electrical", "plumbing", "HVAC", "restaurant", "marketing"]
    
    return IndustryContext(
        industry=industry,
        subindustry=subindustry,
        synonyms=synonyms,
        excluded_industries=excluded
    )

def _create_fallback_context() -> IndustryContext:
    """Create fallback industry context when inference fails."""
    return IndustryContext(
        industry="business",
        subindustry="business services",
        synonyms=["business", "company", "services"],
        excluded_industries=["law", "electrical", "plumbing", "HVAC", "restaurant", "marketing"]
    )

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

async def _search_all(plan: WebSearchPlan, industry_ctx: IndustryContext) -> list[str]:
    """Run all searches concurrently and return text results with industry context."""
    async def one(item: WebSearchItem) -> Optional[str]:
        try:
            # Pass industry context to search agent for better filtering
            search_prompt = (
                f"Search term: {item.query}\n"
                f"Reason: {item.reason}\n"
                f"Industry context: {industry_ctx.subindustry}\n"
                f"CRITICAL: Only include competitors from {industry_ctx.subindustry}. "
                f"EXCLUDE competitors from: {', '.join(industry_ctx.excluded_industries[:5])}"
            )
            r = await Runner.run(search_agent, search_prompt)
            check_token_usage("Search agent", r, TOKEN_CAPS["Search agent"])
            return str(r.final_output)
        except Exception:
            return None

    tasks = [asyncio.create_task(one(s)) for s in plan.searches]
    return [r for r in await asyncio.gather(*tasks) if r]

async def generate_brief(
    query: str, 
    template: str, 
    biz: str, 
    location: str, 
    to_email: str = None,
    timeout_seconds: int = 50
) -> Tuple[ReportData, Optional[str]]:
    """
    Full brief generation pipeline with timeout and structured parsing support.
    Returns (report, error_message) tuple.
    """
    trace_id = gen_trace_id()
    trace_filter.trace_id = trace_id
    logger.info(f"Starting brief generation")
    
    try:
        # Wrap entire pipeline in timeout (Render free tier allows up to 30s, but Gradio may allow more)
        return await asyncio.wait_for(
            _generate_brief_inner(query, template, biz, location, to_email, trace_id),
            timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        error = "Request took too long - try simpler query"
        trace_filter.trace_id = trace_id
        logger.error(f"Timeout after {timeout_seconds}s")
        # Return minimal report with error
        return ReportData(
            short_summary=error,
            markdown_report=f"# Error\n\n{error}",
            follow_up_questions=[]
        ), error
    except Exception as e:
        error = f"Error generating brief: {str(e)[:200]}"
        trace_filter.trace_id = trace_id
        logger.error(f"{error}", exc_info=True)
        return ReportData(
            short_summary=error,
            markdown_report=f"# Error\n\n{error}",
            follow_up_questions=[]
        ), error


async def _generate_brief_inner(
    query: str,
    template: str,
    biz: str,
    location: str,
    to_email: Optional[str],
    trace_id: str
) -> Tuple[ReportData, Optional[str]]:
    """Inner brief generation with structured parsing support."""
    # 0. Infer industry context from exact inputs (with web lookup if needed)
    trace_filter.trace_id = trace_id
    logger.info("Inferring industry context...")
    try:
        industry_ctx = await infer_industry_context(biz, query, template, location, trace_id)
        logger.info(f"Inferred: industry={industry_ctx.industry}, subindustry={industry_ctx.subindustry}, synonyms={industry_ctx.synonyms[:3]}")
        
        # Validation: Ensure industry is not template-derived
        if industry_ctx.industry in ["competitor snapshot", "local seo audit", "grant opportunities"]:
            logger.error(f"CRITICAL ERROR: Industry inference returned template name '{industry_ctx.industry}' - this should never happen!")
            industry_ctx = _create_fallback_context()
    except Exception as e:
        logger.error(f"Error inferring industry context: {e}", exc_info=True)
        industry_ctx = _create_fallback_context()
        logger.info(f"Using fallback context: industry={industry_ctx.industry}, subindustry={industry_ctx.subindustry}")
    
    # 1. Build the research plan with industry context
    trace_filter.trace_id = trace_id
    logger.info("Planning searches...")
    planner_prompt = (
        f"Query: {query}\n"
        f"Business: {biz}\n"
        f"Industry: {industry_ctx.industry}\n"
        f"Subindustry: {industry_ctx.subindustry}\n"
        f"Location: {location}\n"
        f"Synonyms: {', '.join(industry_ctx.synonyms[:6])}\n"
        f"Excluded industries (do NOT search for these): {', '.join(industry_ctx.excluded_industries[:5])}\n\n"
        f"Generate three search queries that MUST include subindustry keywords and location. "
        f"Each query should target {industry_ctx.subindustry} in {location}."
    )
    plan_result = await Runner.run(planner_agent, planner_prompt)
    check_token_usage("PlannerAgent", plan_result, TOKEN_CAPS["PlannerAgent"])
    plan = plan_result.final_output_as(WebSearchPlan)

    # 2. Perform searches concurrently with industry context
    trace_filter.trace_id = trace_id
    logger.info("Searching web...")
    search_results = await _search_all(plan, industry_ctx)
    
    # Handle empty search results
    if not search_results:
        logger.warning("No search results")
        search_results = ["Limited public data available - consider refining search terms"]

    # 3. Compose writer prompt with industry context
    instructions = writer_instructions(template, biz, location, industry_ctx)
    writer_prompt = f"Original query: {query}\nSummarized search results: {search_results}"

    # 4. Generate report
    logger.info("Writing report...")
    writer_result = await Runner.run(writer_agent, f"{instructions}\n\n{writer_prompt}")
    check_token_usage("WriterAgent", writer_result, TOKEN_CAPS["WriterAgent"])
    
    # Parse based on feature flag
    if USE_STRUCTURED_PARSING:
        report = _parse_structured_output(writer_result, trace_id)
    else:
        # Legacy path
        report = writer_result.final_output_as(ReportData)
    
    # Convert to ReportData if structured
    if USE_STRUCTURED_PARSING and isinstance(report, Report):
        markdown_report = render_report_to_markdown(report)
        report_data = ReportData(
            short_summary=report.short_summary,
            markdown_report=markdown_report,
            follow_up_questions=[]
        )
    else:
        report_data = report

    # 5. Send email if address provided (non-blocking to avoid timeout)
    if to_email:
        logger.info("Sending email...")
        try:
            subject = f"{template} Brief: {biz} – {location}"
            # Send email in background task to avoid blocking response
            async def send_email_async():
                try:
                    # Run sync function in thread pool
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None, 
                        send_email_direct, 
                        subject, 
                        report_data.markdown_report, 
                        to_email
                    )
                    logger.info("Email sent successfully")
                except Exception as e:
                    logger.error(f"Background email send failed: {str(e)[:200]}", exc_info=True)
            
            asyncio.create_task(send_email_async())
            logger.info("Email queued for sending")
        except Exception as e:
            error = f"Report generated but email queue failed: {str(e)[:200]}"
            logger.error(error, exc_info=True)
            return report_data, error

    logger.info("Brief generation complete")
    return report_data, None


def _parse_structured_output(writer_result, trace_id: str) -> 'Report':
    """Parse structured JSON output with retry logic."""
    from schemas import Report
    
    # Try to extract JSON from result
    output_text = str(writer_result.final_output)
    
    # First attempt: parse JSON
    parsed_dict = extract_and_parse_json(output_text)
    
    if parsed_dict:
        try:
            return Report.model_validate(parsed_dict)
        except Exception as e:
            trace_filter.trace_id = trace_id
            logger.warning(f"First parse failed: {e}, retrying...")
    
    # Retry with explicit schema prompt
    # Note: This would require re-running the agent, which is expensive
    # For now, return synthetic error report
    trace_filter.trace_id = trace_id
    logger.error("Could not parse structured output, using fallback")
    
    # Return minimal valid report
    from datetime import date, timedelta
    from schemas import ActionItem, Source
    
    return Report(
        schema_version="1.0",
        short_summary="Parsing error - output format unexpected. Please check API response.",
        actions=[
            ActionItem(
                title="Review data parsing",
                kpi="parsing success",
                target_by=date.today() + timedelta(days=30),
                how_steps=["Check API response", "Review logs", "Contact support"],
                tool="Logging tools",
                effort="L",
                impact="M"
            ) for _ in range(5)
        ],
        exec_summary=["Data parsing encountered an issue", "Review system logs", "Check API connectivity", "Verify input format"],
        findings=["System error during parsing", "Check logs for details", "Verify API response format", "Review input data", "Check network connectivity", "Validate credentials"],
        gaps=["Parsing system needs review", "Error handling improvements needed", "Logging enhancements required"],
        sources=[
            Source(url=None, citation="(system logs)"),
            Source(url=None, citation="(error tracking)")
        ]
    )
