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

async def run_brief(query, template, biz, location, to_email, progress=None):
    """
    Generate brief with progress updates and error handling.
    Returns status message for UI display.
    """
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
        if progress:
            progress(0.1, desc="Planning searches...")
        
        report, error = await generate_brief(query, template, biz, location, to_email.strip())
        
        if progress:
            progress(0.7, desc="Searching web...")
        
        if progress:
            progress(0.8, desc="Writing report...")
        
        if error:
            # Partial success: report generated but email failed
            if "email failed" in error.lower():
                if progress:
                    progress(1.0, desc="⚠️ Email failed")
                return f"⚠️ **Report generated but email failed:** {error}\n\nReport summary: {report.short_summary[:200]}"
            # Full failure
            if progress:
                progress(1.0, desc="⚠️ Error")
            return f"⚠️ **Error:** {error}"
        
        # Success
        if progress:
            progress(1.0, desc="✅ Email sent")
        return f"✅ Email sent to **{mask_email(to_email.strip())}**"
        
    except asyncio.TimeoutError:
        if progress:
            progress(1.0, desc="⚠️ Timeout")
        return "⚠️ **Timeout:** Request took too long - try a simpler query"
    except Exception as ex:
        error_msg = str(ex)
        if progress:
            progress(1.0, desc="⚠️ Error")
        if "API key" in error_msg.lower() or "authentication" in error_msg.lower():
            return f"⚠️ **Authentication Error:** Check your API keys in the Render dashboard. Error: {error_msg[:200]}"
        elif "rate limit" in error_msg.lower():
            return f"⚠️ **Rate Limit:** API rate limit exceeded. Please try again in a moment."
        else:
            return f"⚠️ **Error generating brief:** {error_msg[:300]}"


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
            placeholder='Example: "Top 5 bankruptcy law competitors in Johnson City; pricing, offers, differentiators; 14-day actions. The Pope Firm specializes in bankruptcy and debt relief services. Key concerns: client intake efficiency and local SEO visibility."',
            lines=4,
            info="💡 **Important:** Include (1) what your business does (e.g., 'bankruptcy law', 'EV charger installation', 'family law'), (2) any specific concerns or focus areas, and (3) what you want in the brief. This ensures accurate, industry-specific recommendations."
        )
        to_email = gr.Textbox(
            label="Where should we email it?",
            placeholder="you@company.com",
            lines=1
        )
        
        gr.Markdown("**Delivery:** Email")
        
        # Button
        go = gr.Button("Generate Brief 🚀", variant="primary")
        
        # Status display
        status = gr.Markdown(label="Status", value="Ready to generate brief")
        
        def run_with_progress_sync(q, t, b, l, e, progress=None):
            """Run brief generation with progress updates (sync wrapper for Gradio)."""
            import traceback
            try:
                # Create new event loop for this thread
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Run async function in event loop
                # Progress is passed directly - Gradio injects it automatically
                if loop.is_running():
                    # If loop is already running, we need nest_asyncio
                    try:
                        import nest_asyncio
                        nest_asyncio.apply()
                        result = loop.run_until_complete(run_brief(q, t, b, l, e, progress))
                    except ImportError:
                        return "⚠️ **System Error:** Please install nest-asyncio: pip install nest-asyncio"
                else:
                    result = loop.run_until_complete(run_brief(q, t, b, l, e, progress))
                
                if progress:
                    progress(1.0, desc="✅ Complete")
                return result
            except Exception as ex:
                error_str = str(ex)
                error_type = type(ex).__name__
                # Log full traceback for debugging
                print(f"\n{'='*60}")
                print(f"ERROR in run_with_progress_sync: {error_type}: {error_str}")
                print(traceback.format_exc())
                print(f"{'='*60}\n")
                # Map common errors to friendly messages
                if "event loop" in error_str.lower() or "asyncio.run" in error_str.lower():
                    return "⚠️ **System Error:** Async operation conflict. Please restart the app."
                # Map validation errors
                if "enter" in error_str.lower():
                    return f"⚠️ **Validation Error:** {error_str}"
                return f"⚠️ **Error:** {error_type}: {error_str[:200]}"
        
        # Wire button click with button locking and status updates
        def update_status_and_disable():
            """Update status and disable button on click."""
            return "🔄 Planning searches...", gr.update(interactive=False)
        
        def process_and_enable(q, t, b, l, e, progress=None):
            """Process request and re-enable button (sync)."""
            result = run_with_progress_sync(q, t, b, l, e, progress)
            return result, gr.update(interactive=True)
        
        # Chain button click: disable → update status → process → re-enable
        # Note: Progress is automatically injected by Gradio when using .then()
        go.click(
            fn=update_status_and_disable,
            outputs=[status, go]
        ).then(
            fn=process_and_enable,
            inputs=[query, template, biz, location, to_email],
            outputs=[status, go]
        )

    return demo

# Create demo at module level for Gradio CLI compatibility
demo = create_demo()

def main():
    """Launch the demo (for direct execution)."""
    # Read port from environment (Render sets $PORT)
    port = int(os.environ.get("PORT", 7860))
    # Use 0.0.0.0 for Render/HF Spaces compatibility
    # Share port if already in use (for development)
    try:
        demo.launch(server_name="0.0.0.0", server_port=port, share=False)
    except OSError:
        # Port in use, try next available
        demo.launch(server_name="0.0.0.0", server_port=None, share=False)

if __name__ == "__main__":
    main()
