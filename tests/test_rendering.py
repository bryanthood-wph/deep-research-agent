"""
Tests for markdown rendering and email HTML generation.
"""

import pytest
from schemas import Report, ActionItem, Source
from renderers.markdown_renderer import render_report_to_markdown


def test_markdown_renderer_deterministic():
    """Test that same Report produces same markdown."""
    report = _create_test_report()
    
    markdown1 = render_report_to_markdown(report)
    markdown2 = render_report_to_markdown(report)
    
    assert markdown1 == markdown2
    assert "## Action Board" in markdown1
    assert "## Executive Summary" in markdown1
    assert "## Main Findings" in markdown1
    assert "## Dogs Not Barking" in markdown1
    assert "## Sources" in markdown1


def test_markdown_renderer_action_format():
    """Test action items render with correct format."""
    report = _create_test_report()
    markdown = render_report_to_markdown(report)
    
    # Check action format includes KPI, target, how steps, tool
    assert "KPI:" in markdown
    assert "HOW:" in markdown
    assert "TOOL:" in markdown
    assert "Effort:" in markdown
    assert "Impact:" in markdown


def test_markdown_renderer_all_sections():
    """Test all sections are present in output."""
    report = _create_test_report()
    markdown = render_report_to_markdown(report)
    
    sections = [
        "Action Board",
        "Executive Summary",
        "Main Findings",
        "Dogs Not Barking",
        "Sources"
    ]
    
    for section in sections:
        assert f"## {section}" in markdown


def test_markdown_renderer_html_escaped():
    """Test that HTML is properly escaped."""
    report = Report(
        schema_version="1.0",
        short_summary="Test summary with <script>alert('xss')</script> tags",
        actions=[
            ActionItem(
                title="Action with <tag>",
                kpi="metric",
                target_percent="+15%",
                target_days=30,
                how_steps=["step 1", "step 2", "step 3"],
                tools=["Tool 1", "Tool 2", "Tool 3"],
                effort="M",
                impact="H"
            ) for _ in range(5)
        ],
        exec_summary=["Bullet with <script> tag"] * 4,  # Need at least 4
        findings=["Finding with <tag>"] * 6,
        gaps=["Gap with <tag>"] * 3,
        sources=[
            Source(url=None, citation="(local research)")
        ] * 2
    )
    
    markdown = render_report_to_markdown(report)
    # HTML should be escaped (schemas.py handles this)
    assert "<script>" not in markdown  # Should be escaped to &lt;script&gt;
    # Check that tags are escaped (schemas sanitize on input)
    assert "&lt;tag&gt;" in markdown or "<tag>" not in markdown


def _create_test_report() -> Report:
    """Helper to create a test report."""
    return Report(
        schema_version="1.0",
        short_summary="This is a test summary that is long enough to pass validation requirements",
        actions=[
            ActionItem(
                title=f"Test action {i+1}",
                kpi="test metric",
                target_percent="+15%",
                target_days=30,
                how_steps=["step 1", "step 2", "step 3"],
                tools=["Test tool 1", "Test tool 2", "Test tool 3"],
                effort="M",
                impact="H"
            ) for i in range(5)
        ],
        exec_summary=["bullet 1", "bullet 2", "bullet 3", "bullet 4"],
        findings=[f"finding {i}" for i in range(1, 7)],
        gaps=["gap 1", "gap 2", "gap 3"],
        sources=[
            Source(url="https://example.com", citation="example.com"),
            Source(url=None, citation="(local research)")
        ]
    )

