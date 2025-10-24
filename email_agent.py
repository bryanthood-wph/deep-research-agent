# Import environment variable access for API key, Dict for type hints, sendgrid for email delivery
import os
from typing import Dict

# Import sendgrid components - must import all helpers before use in send_email function
import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool

# Define email sending function as tool - @function_tool decorator enables agent to call this function
# Requires sendgrid imports above to access email construction and sending capabilities
@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body"""
    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
    from_email = Email(
        "support@colbyhoodconsulting.com"
    )  # put your verified sender here
    to_email = To("brnthood@gmail.com")  # put your recipient here
    content = Content("text/html", html_body)
    mail = Mail(from_email, to_email, subject, content).get()
    response = sg.client.mail.send.post(request_body=mail)
    print("Email response", response.status_code)
    return {"status": "success"}


# Define agent behavior for email composition - emphasizes HTML formatting and subject line generation
# Expects markdown report as input, must convert to HTML before calling send_email tool
INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""

# Instantiate email agent - requires both send_email function and INSTRUCTIONS defined above
# tools=[send_email] gives agent ability to actually send emails, not just generate content
email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
