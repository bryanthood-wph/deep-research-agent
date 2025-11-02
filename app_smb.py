"""
Gradio UI for SMB Decision Briefs (MVP).
"""

from dotenv import load_dotenv
load_dotenv()

import gradio as gr
import asyncio
import re
import os
from smb_briefs import generate_brief
from brief_templates import TEMPLATES
from email_agent import mask_email

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

async def run_brief(query, template, biz, location, to_email):
    # Check for required environment variables
    if not os.environ.get("OPENAI_API_KEY"):
        return "⚠️ **Configuration Error:** OPENAI_API_KEY not set. Please configure this in your Render dashboard."
    
    if not os.environ.get("SENDGRID_API_KEY"):
        return "⚠️ **Configuration Error:** SENDGRID_API_KEY not set. Please configure this in your Render dashboard."
    
    # Validate inputs
    if not query or not query.strip():
        return "⚠️ Please enter a query describing what you want in the brief."
    
    if not biz or not biz.strip():
        return "⚠️ Please enter a business name."
    
    if not location or not location.strip():
        return "⚠️ Please enter a location."
    
    # Validate email
    if not to_email or not EMAIL_RE.match(to_email.strip()):
        return "⚠️ Enter a valid email to receive the brief."
    
    # Generate report and send via email
    try:
        report = await generate_brief(query, template, biz, location, to_email.strip())
        return f"✅ Email sent to **{mask_email(to_email.strip())}**"
    except Exception as ex:
        error_msg = str(ex)
        if "API key" in error_msg.lower() or "authentication" in error_msg.lower():
            return f"⚠️ **Authentication Error:** Check your API keys in the Render dashboard. Error: {error_msg[:200]}"
        elif "rate limit" in error_msg.lower():
            return f"⚠️ **Rate Limit:** API rate limit exceeded. Please try again in a moment."
        else:
            return f"⚠️ **Error generating brief:** {error_msg[:300]}"

def _sync_run(q, t, b, l, e):
    try:
        return asyncio.run(run_brief(q, t, b, l, e))
    except Exception as ex:
        error_msg = str(ex)
        if "API key" in error_msg.lower():
            return f"⚠️ **Configuration Error:** API key issue. Check Render dashboard environment variables."
        return f"⚠️ **Error:** {error_msg[:300]}"

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
