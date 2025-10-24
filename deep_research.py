# Import UI framework for web interface, environment loader for API keys, orchestrator for research logic
import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

# Load environment variables first - critical for all agents needing API keys (OpenAI, SendGrid)
# override=True ensures .env values take precedence over existing environment variables
load_dotenv(override=True)

# Wrapper function adapting ResearchManager's async generator to Gradio's streaming interface
# Yields status updates and final report progressively for real-time UI feedback
async def run(query: str):
    async for chunk in ResearchManager().run(query):
        yield chunk


# Define UI layout using Blocks - must construct all components before launch
# Order of component definitions determines visual layout in interface
with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Report")

    # Wire up event handlers - button click and textbox submit both trigger same run function
    # Both output to report component which updates progressively as run() yields chunks
    run_button.click(fn=run, inputs=query_textbox, outputs=report)
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)

# Launch UI server - must be last statement after all components and handlers defined
# inbrowser=True automatically opens browser tab for user convenience
ui.launch(inbrowser=True)
