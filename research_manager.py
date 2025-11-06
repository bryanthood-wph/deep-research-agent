from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent, send_email_direct, mask_email
import asyncio
import re


class ResearchManager:
    def validate_email(self, email: str) -> bool:
        """Validate email format and reject multiple recipients"""
        if not email or not email.strip():
            return False
        # Check for multiple recipients
        if any(sep in email for sep in [',', ';', ' ']):
            return False
        # Simple regex validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None
    
    async def run(self, query: str, to_email: str = None):
        """Run the deep research process, yielding the status updates and sending via email"""
        # Validate email is required
        if not to_email or not self.validate_email(to_email):
            yield "Error: Valid email address is required"
            return
        
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            masked = mask_email(to_email)
            print(f"Starting research for {masked}")
            yield f"Starting research for {masked}..."
            
            search_plan = await self.plan_searches(query)
            yield "Searches planned, starting to search..."
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            report = await self.write_report(query, search_results)
            yield "Report written, sending email..."
            result = await self.send_email(report, to_email)
            yield f"Email sent to {result['to']}"

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """Plan the searches to perform for the query"""
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """Perform the searches to perform for the query"""
        print("Searching...")
        num_completed = 0
        tasks = [
            asyncio.create_task(self.search(item)) for item in search_plan.searches
        ]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")
        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """Perform a search for the query"""
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """Write the report for the query"""
        print("Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )

        print("Finished writing report")
        return result.final_output_as(ReportData)

    async def send_email(self, report: ReportData, to_email: str) -> dict:
        print("Writing email...")
        # Use direct email send to pass recipient
        # Generate subject from report summary
        subject = f"Research Brief: {report.short_summary[:50]}"
        result = send_email_direct(subject, report.markdown_report, to_email)
        print(f"Email sent to {result['to']}")
        return result
