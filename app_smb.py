"""
Gradio UI for SMB Decision Briefs (MVP).
"""

from dotenv import load_dotenv
load_dotenv()

import gradio as gr
import asyncio
import re
from smb_briefs import generate_brief
from brief_templates import TEMPLATES
from email_agent import mask_email

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

async def run_brief(query, template, biz, location, to_email):
    # Validate email
    if not to_email or not EMAIL_RE.match(to_email.strip()):
        return "⚠️ Enter a valid email to receive the brief."
    
    # Generate report and send via email
    report = await generate_brief(query, template, biz, location, to_email.strip())
    
    # Return status only, never the report body
    return f"✅ Email sent to **{mask_email(to_email.strip())}**"

def _sync_run(q, t, b, l, e):
    try:
        return asyncio.run(run_brief(q, t, b, l, e))
    except Exception as ex:
        return f"⚠️ Could not generate brief: {str(ex)}"

def create_demo():
    """Create and return the Gradio demo (works with CLI mode)."""
    with gr.Blocks(title="SMB Decision Brief Generator") as demo:
        gr.Markdown("# 🧠 SMB Decision Briefs\nGenerate concise research-based reports for small businesses.")
        with gr.Row():
            template = gr.Dropdown(list(TEMPLATES.keys()), label="Brief Type", value="Competitor Snapshot")
            biz = gr.Textbox(label="Business Name", placeholder="Acme Plumbing")
            location = gr.Textbox(label="Location", placeholder="Austin, TX")
        query = gr.Textbox(
            label="Describe the outcome for this brief",
            placeholder='e.g., "Top 5 bankruptcy competitors in Johnson City; pricing, offers, differentiators; 14-day actions."',
            lines=2
        )
        to_email = gr.Textbox(
            label="Where should we email it?",
            placeholder="you@company.com",
            lines=1
        )
        gr.Markdown("**Delivery:** Email")
        go = gr.Button("Generate Brief 🚀", variant="primary")
        status = gr.Markdown(label="Status")

        go.click(fn=_sync_run, inputs=[query, template, biz, location, to_email], outputs=status)

    return demo

# Create demo at module level for Gradio CLI compatibility
demo = create_demo()

def main():
    """Launch the demo (for direct execution)."""
    # Auto-find available port; use 0.0.0.0 for Render/HF Spaces compatibility
    demo.launch(server_name="0.0.0.0", server_port=None)

if __name__ == "__main__":
    main()
