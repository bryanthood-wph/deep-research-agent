"""
Strict Pydantic schemas for report generation with HTML sanitization.
All model outputs are validated and sanitized to prevent XSS.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
import html
import re


class Source(BaseModel):
    """Flexible source: URL or citation string (e.g., 'local research')"""
    url: Optional[str] = None  # AnyUrl fails on "(local research)" - validate manually
    citation: str = Field(min_length=3, max_length=200)
    
    @field_validator('citation')
    @classmethod
    def sanitize_citation(cls, v: str) -> str:
        """Sanitize citation text."""
        return html.escape(v.strip())
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate URL format if provided."""
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        # Basic URL validation
        if not re.match(r'^https?://', v, re.IGNORECASE):
            return None
        return html.escape(v)


class ActionItem(BaseModel):
    """Single action item with KPI, target, steps, and tools."""
    title: str = Field(min_length=8, max_length=120)
    kpi: str = Field(min_length=3, max_length=60)
    target_percent: str = Field(description="Percentage improvement like '+15%' or 'complete'")
    target_days: int = Field(description="Relative days: 14, 30, 60, or 90")
    how_steps: list[str] = Field(min_length=3, max_length=3)
    tools: list[str] = Field(min_length=3, max_length=3, description="Exactly 3 tools ordered by market share")
    effort: Literal['L', 'M', 'H']
    impact: Literal['L', 'M', 'H']
    
    @field_validator('title', 'kpi')
    @classmethod
    def sanitize_string(cls, v: str) -> str:
        """Sanitize string fields."""
        return html.escape(v.strip())
    
    @field_validator('target_percent')
    @classmethod
    def validate_target_percent(cls, v: str) -> str:
        """Validate target_percent format: +X% or 'complete'."""
        v = v.strip()
        if v.lower() == 'complete':
            return v
        if not re.match(r'^[+\-]?\d+%$', v):
            raise ValueError(f"target_percent must be like '+15%' or 'complete', got '{v}'")
        return v
    
    @field_validator('target_days')
    @classmethod
    def validate_target_days(cls, v: int) -> int:
        """Validate target_days: must be 14, 30, 60, or 90."""
        if v not in [14, 30, 60, 90]:
            raise ValueError(f"target_days must be 14, 30, 60, or 90, got {v}")
        return v
    
    @field_validator('how_steps')
    @classmethod
    def sanitize_steps(cls, v: list[str]) -> list[str]:
        """Sanitize list of steps."""
        return [html.escape(s.strip()) for s in v if s.strip()]
    
    @field_validator('tools')
    @classmethod
    def validate_tools(cls, v: list) -> list[str]:
        """Validate tools: must be exactly 3 items."""
        if not isinstance(v, list):
            raise ValueError(f"tools must be a list, got {type(v)}")
        if len(v) != 3:
            raise ValueError(f"tools must have exactly 3 items, got {len(v)}")
        # Sanitize each tool name
        sanitized = [html.escape(str(t).strip()) for t in v if str(t).strip()]
        if len(sanitized) != 3:
            raise ValueError(f"tools must have exactly 3 non-empty items after sanitization")
        return sanitized


class Report(BaseModel):
    """Complete report structure with all sections."""
    schema_version: Literal["1.0"] = "1.0"
    short_summary: str = Field(min_length=20, max_length=300)
    actions: list[ActionItem] = Field(min_length=5, max_length=5)
    exec_summary: list[str] = Field(min_length=4, max_length=6)
    findings: list[str] = Field(min_length=6, max_length=10)
    gaps: list[str] = Field(min_length=3, max_length=8)
    sources: list[Source] = Field(min_length=2, max_length=10)
    
    @field_validator('short_summary')
    @classmethod
    def sanitize_summary(cls, v: str) -> str:
        """Sanitize and truncate summary."""
        return html.escape(v.strip()[:300])
    
    @field_validator('exec_summary', 'findings', 'gaps')
    @classmethod
    def sanitize_list(cls, v: list[str]) -> list[str]:
        """Sanitize and truncate list items."""
        return [html.escape(s.strip()[:240]) for s in v if s.strip()]
    
    @field_validator('actions')
    @classmethod
    def validate_actions(cls, v: list) -> list:
        """Ensure exactly 5 actions."""
        if len(v) != 5:
            raise ValueError(f"Must have exactly 5 actions, got {len(v)}")
        return v

