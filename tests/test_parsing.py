"""
Tests for robust JSON parsing and repair.
"""

import pytest
from parsing.json_capture import robust_json_load, repair_fill, extract_and_parse_json
from schemas import Report


def test_robust_json_load_trailing_comma():
    """Test JSON with trailing comma is fixed."""
    text = '{"short_summary": "test", "actions": [],}'
    result = robust_json_load(text)
    assert result is not None
    assert result["short_summary"] == "test"


def test_robust_json_load_single_quotes():
    """Test JSON with single quotes is converted."""
    text = "{'short_summary': 'test', 'actions': []}"
    result = robust_json_load(text)
    assert result is not None
    assert result["short_summary"] == "test"


def test_robust_json_load_code_block():
    """Test JSON extraction from code block."""
    text = "Some text\n```json\n{\"short_summary\": \"test\"}\n```\nMore text"
    result = robust_json_load(text)
    assert result is not None
    assert result["short_summary"] == "test"


def test_repair_fill_minimums():
    """Test repair_fill ensures minimum required fields."""
    minimal = {"short_summary": "test"}
    repaired = repair_fill(minimal)
    
    assert len(repaired["actions"]) == 5
    assert len(repaired["exec_summary"]) >= 4
    assert len(repaired["findings"]) >= 6
    assert len(repaired["gaps"]) >= 3
    assert len(repaired["sources"]) >= 2


def test_repair_fill_dedupe():
    """Test repair_fill removes duplicate bullets."""
    input_dict = {
        "short_summary": "test summary that is long enough",
        "exec_summary": ["duplicate", "duplicate", "unique", "another"],
        "actions": [],
        "findings": [],
        "gaps": [],
        "sources": []
    }
    repaired = repair_fill(input_dict)
    # Should have deduped
    assert len(repaired["exec_summary"]) >= 4
    assert "duplicate" in repaired["exec_summary"]  # First occurrence kept


def test_extract_and_parse_valid_json():
    """Test full extraction and validation pipeline."""
    import json
    
    # Build complete valid structure
    base_action = {
        "title": "Test action one",
        "kpi": "test metric",
        "target_percent": "+15%",
        "target_days": 30,
        "how_steps": ["step 1", "step 2", "step 3"],
        "tools": ["Test tool 1", "Test tool 2", "Test tool 3"],
        "effort": "M",
        "impact": "H"
    }
    
    data = {
        "schema_version": "1.0",
        "short_summary": "This is a test summary that is long enough to pass validation requirements",
        "actions": [base_action.copy() for _ in range(5)],
        "exec_summary": ["bullet 1", "bullet 2", "bullet 3", "bullet 4"],
        "findings": ["finding 1", "finding 2", "finding 3", "finding 4", "finding 5", "finding 6"],
        "gaps": ["gap 1", "gap 2", "gap 3"],
        "sources": [
            {"url": "https://example.com", "citation": "example.com"},
            {"url": None, "citation": "(local research)"}
        ]
    }
    
    # Update action titles to be unique
    for i, action in enumerate(data["actions"]):
        action["title"] = f"Test action {i+1}"
    
    parsed = extract_and_parse_json(json.dumps(data))
    assert parsed is not None
    assert len(parsed["actions"]) == 5
    assert parsed["schema_version"] == "1.0"


def test_report_schema_validation():
    """Test Report schema validates correctly."""
    from schemas import ActionItem, Source
    
    report = Report(
        schema_version="1.0",
        short_summary="This is a test summary that is long enough to pass validation requirements",
        actions=[
            ActionItem(
                title="Test action",
                kpi="test metric",
                target_percent="+15%",
                target_days=30,
                how_steps=["step 1", "step 2", "step 3"],
                tools=["Test tool 1", "Test tool 2", "Test tool 3"],
                effort="M",
                impact="H"
            ) for _ in range(5)
        ],
        exec_summary=["bullet 1", "bullet 2", "bullet 3", "bullet 4"],
        findings=["finding 1", "finding 2", "finding 3", "finding 4", "finding 5", "finding 6"],
        gaps=["gap 1", "gap 2", "gap 3"],
        sources=[
            Source(url="https://example.com", citation="example.com"),
            Source(url=None, citation="(local research)")
        ]
    )
    
    assert report.schema_version == "1.0"
    assert len(report.actions) == 5
    assert len(report.exec_summary) >= 4
    assert len(report.findings) >= 6

