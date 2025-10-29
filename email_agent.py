import os
from typing import Dict

import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool, ModelSettings
import markdown


def send_email_direct(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body (direct call version)"""
    # Convert Markdown to HTML before sending
    # Note: html_body comes as Markdown from the orchestrator (report.markdown_report)
    # We need to convert # headings, [links](url), **bold**, etc. to proper HTML
    html_content = markdown.markdown(
        html_body,
        extensions=['extra', 'nl2br']  # 'extra' handles tables/fenced code, 'nl2br' converts newlines
    )
    
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email("colby@colbyhoodconsulting.com")  # put your verified sender here
    to_email = To("brnthood@gmail.com")  # put your recipient here
    content = Content("text/html", html_content)  # Now it's real HTML, not Markdown
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print("Email response", response.status_code)
    return {"status": "success"}


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body"""
    return send_email_direct(subject, html_body)


INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
    model_settings=ModelSettings(max_output_tokens=200, temperature=0.2),
)
