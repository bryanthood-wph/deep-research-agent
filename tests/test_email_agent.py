"""
Tests for email_agent Markdown to HTML conversion.
"""
import pytest
from unittest.mock import patch, MagicMock
from email_agent import send_email_direct


def test_markdown_to_html_conversion():
    """Ensure send_email_direct converts Markdown to proper HTML"""
    
    # Mock SendGrid to avoid actual API calls
    with patch('email_agent.sendgrid.SendGridAPIClient') as mock_sg:
        # Setup mock response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_client.client.mail.send.post.return_value = mock_response
        mock_sg.return_value = mock_client
        
        # Test input with Markdown syntax
        markdown_input = """# Executive Summary

This is a **bold** statement with a [link](https://example.com).

## Key Findings

- Item 1
- Item 2"""
        
        # Call function
        result = send_email_direct("Test Subject", markdown_input)
        
        # Verify function succeeded
        assert result["status"] == "success"
        
        # Verify SendGrid was called
        assert mock_client.client.mail.send.post.called
        
        # Extract the mail object that was sent
        call_args = mock_client.client.mail.send.post.call_args
        mail_payload = call_args[1]['request_body']
        
        # Verify HTML content was generated (not raw Markdown)
        # The content should have HTML tags, not Markdown syntax
        assert '<h1>' in str(mail_payload) or 'Executive Summary' in str(mail_payload)
        assert '<strong>' in str(mail_payload) or '<b>' in str(mail_payload)
        assert '<a href=' in str(mail_payload) or 'https://example.com' in str(mail_payload)
        
        # Verify no literal Markdown syntax remains
        assert '# Executive' not in str(mail_payload)  # No literal # heading
        assert '**bold**' not in str(mail_payload)     # No literal **bold**
        assert '[link]' not in str(mail_payload)        # No literal [link](url)


def test_markdown_newlines_preserved():
    """Ensure newlines are converted to HTML properly"""
    
    with patch('email_agent.sendgrid.SendGridAPIClient') as mock_sg:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_client.client.mail.send.post.return_value = mock_response
        mock_sg.return_value = mock_client
        
        # Test multi-line content
        markdown_input = "Line 1\nLine 2\n\nParagraph 2"
        
        result = send_email_direct("Test", markdown_input)
        
        assert result["status"] == "success"
        
        # The 'nl2br' extension should convert newlines to <br>
        call_args = mock_client.client.mail.send.post.call_args
        mail_payload = str(call_args[1]['request_body'])
        
        # Should have paragraph tags or br tags
        assert '<p>' in mail_payload or '<br' in mail_payload

