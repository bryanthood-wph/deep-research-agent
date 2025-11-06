import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager
import re

load_dotenv(override=True)

# Task templates
TASK_TEMPLATES = {
    "Competitor snapshot": "Top 5 competitors near {city}. Include pricing, offers, differentiators, and SEO notes. Actions for next 14 days.",
    "Local SEO audit": "{Business name}, {city}. Check NAP, GBP, citations, site speed, on-page. Prioritize fixes by effort/impact.",
    "Grant opportunities": "Active grants for {business type} in {state/city}. Include eligibility, deadlines, award sizes. 2-week prep checklist.",
    "Summarize a URL": "Summarize: {URL}. Pull dates, key numbers, and 3 actions I can do this month.",
    "Compare vendors/products": "Compare {Vendor A} vs {Vendor B} for {use case}. Criteria: cost, support, features, lock-in. Recommend one.",
    "Quick facts": "Key stats for {topic} (last 12 months). Use primary sources. Include 3 next actions.",
    "Other": ""
}


def compile_query(task: str, raw_text: str) -> tuple[str, str]:
    """Compile query from task and text, checking for unfilled placeholders"""
    # Check for unfilled placeholders
    if re.search(r'\{[^}]+\}', raw_text):
        return None, "Please fill all placeholders (text in {curly braces})"
    
    # Optionally append seasonality note for non-Other tasks
    query = raw_text.strip()
    if task != "Other" and query:
        query += " Consider next 30-90 day seasonality."
    
    return query, None


async def run_research(task: str, query_text: str, user_email: str):
    """Run research and send via email"""
    # Compile query
    final_query, error = compile_query(task, query_text)
    if error:
        yield f"❌ {error}"
        return
    
    if not user_email or not user_email.strip():
        yield "❌ Email address is required"
        return
    
    # Run research with email delivery
    async for status in ResearchManager().run(final_query, user_email):
        yield status


def update_template(task: str):
    """Update textarea when task is selected"""
    return TASK_TEMPLATES.get(task, "")


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    gr.Markdown("### We'll email a ready-to-use brief. Choose a task and fill the blanks.")
    
    with gr.Row():
        task_selector = gr.Dropdown(
            choices=list(TASK_TEMPLATES.keys()),
            label="Pick a task",
            value="Other",
            interactive=True
        )
    
    query_textbox = gr.Textbox(
        label="Describe the outcome",
        placeholder="List location, timeframe, and what success looks like.",
        lines=4,
        value=""
    )
    
    email_input = gr.Textbox(
        label="Where should we send it?",
        placeholder="you@company.com",
        type="email"
    )
    
    run_button = gr.Button("Generate & Send Brief", variant="primary")
    
    status_output = gr.Markdown(label="Status", value="")
    
    # Wire up task selector to prefill textarea
    task_selector.change(
        fn=update_template,
        inputs=[task_selector],
        outputs=[query_textbox]
    )
    
    # Wire up submit button
    run_button.click(
        fn=run_research,
        inputs=[task_selector, query_textbox, email_input],
        outputs=[status_output]
    )

ui.launch(inbrowser=True)
