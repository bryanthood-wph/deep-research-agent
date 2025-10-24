# Import agent execution framework - Runner executes agents, trace/gen_trace_id enable observability
from agents import Runner, trace, gen_trace_id
# Import all specialized agents and their output types - order reflects execution pipeline
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
# Import asyncio for parallel search execution - critical for performance with multiple searches
import asyncio

# Orchestrator class coordinating all agents in sequence: plan → search → write → email
class ResearchManager:

    # Main entry point coordinating full research pipeline - yields status updates for UI feedback
    # Order is critical: each step depends on previous step's output
    async def run(self, query: str):
        """ Run the deep research process, yielding the status updates and the final report"""
        # Initialize tracing before any agent execution for complete observability
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("Starting research...")
            # Step 1: Plan searches - must happen first to know what to search for
            search_plan = await self.plan_searches(query)
            yield "Searches planned, starting to search..."
            # Step 2: Execute searches - depends on search_plan from step 1
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            # Step 3: Write report - depends on search_results from step 2 and original query
            report = await self.write_report(query, search_results)
            yield "Report written, sending email..."
            # Step 4: Send email - depends on report from step 3
            await self.send_email(report)
            yield "Email sent, research complete"
            # Final yield delivers complete report to UI
            yield report.markdown_report
        
    # Generate search plan using planner_agent - first agent in pipeline, no dependencies
    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        # Return as WebSearchPlan type for type safety in downstream perform_searches method
        return result.final_output_as(WebSearchPlan)

    # Execute all searches in parallel for speed - depends on search_plan structure from plan_searches
    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Perform the searches to perform for the query """
        print("Searching...")
        num_completed = 0
        # Create all search tasks at once for parallel execution - critical for performance
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        # Process completed tasks as they finish, not in order - improves latency
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")
        print("Finished searching")
        return results

    # Execute single search using search_agent - called in parallel by perform_searches
    async def search(self, item: WebSearchItem) -> str | None:
        """ Perform a search for the query """
        # Include both query and reason to give search_agent context for better summarization
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            # Return None on failure so perform_searches can skip failed searches
            return None

    # Synthesize search results into cohesive report - depends on completed search_results and original query
    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """ Write the report for the query """
        print("Thinking about report...")
        # Provide both original query for context and search results as source material
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )

        print("Finished writing report")
        # Return as ReportData type to access structured fields (summary, markdown_report, questions)
        return result.final_output_as(ReportData)
    
    # Send formatted email with report - depends on completed report from write_report
    async def send_email(self, report: ReportData) -> None:
        print("Writing email...")
        # Pass markdown_report field specifically, not entire ReportData object
        await Runner.run(
            email_agent,
            report.markdown_report,
        )
        print("Email sent")