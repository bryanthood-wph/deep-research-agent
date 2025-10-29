"""
Gradio UI for SMB Decision Briefs (MVP).
"""

from dotenv import load_dotenv
load_dotenv()

import gradio as gr
import asyncio
from smb_briefs import generate_brief
from brief_templates import TEMPLATES

async def run_brief(query, template, biz, location, email):
    report = await generate_brief(query, template, biz, location, email)
    return report.markdown_report

def _sync_run(q, t, b, l, e):
    try:
        return asyncio.run(run_brief(q, t, b, l, e))
    except Exception as ex:
        return f"### ⚠️ Could not generate brief\n```\n{ex}\n```\nCheck API key / quota and try again."

def main():
    with gr.Blocks(title="SMB Decision Brief Generator") as demo:
        gr.Markdown("# 🧠 SMB Decision Briefs\nGenerate concise research-based reports for small businesses.")
        with gr.Row():
            template = gr.Dropdown(list(TEMPLATES.keys()), label="Brief Type", value="Competitor Snapshot")
            biz = gr.Textbox(label="Business Name", placeholder="Acme Plumbing")
            location = gr.Textbox(label="Location", placeholder="Austin, TX")
        query = gr.Textbox(label="Research Query", placeholder="Market trends for local plumbers", lines=2)
        email = gr.Checkbox(label="Email report when done", value=False)
        go = gr.Button("Generate Brief 🚀", variant="primary")
        output = gr.Markdown(label="Generated Brief")

        go.click(fn=_sync_run, inputs=[query, template, biz, location, email], outputs=output)

    # Auto-find available port; use 0.0.0.0 for HF Spaces compatibility
    # Gradio auto-detects HF environment and adjusts accordingly
    demo.launch(server_name="0.0.0.0", server_port=None)

if __name__ == "__main__":
    main()
