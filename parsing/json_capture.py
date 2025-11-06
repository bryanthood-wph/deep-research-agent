"""
Robust JSON extraction and repair with comprehensive error handling.
Handles malformed JSON, missing fields, and edge cases.
"""

import json
import re
from typing import Optional, Dict, Any
from schemas import Report, ActionItem, Source


def robust_json_load(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON with tolerance for common formatting issues.
    Returns None if completely unparseable.
    """
    if not text or not text.strip():
        return None
    
    original_text = text.strip()
    text = original_text
    
    # Try to extract JSON block first
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    elif text.startswith('{'):
        # Already looks like JSON, try to extract complete object
        # Find matching closing brace
        brace_count = 0
        end_pos = -1
        for i, char in enumerate(text):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i + 1
                    break
        if end_pos > 0:
            text = text[:end_pos]
        # If no complete match, try full text anyway
    else:
        # Try to extract outermost {...}
        brace_match = re.search(r'\{.*\}', text, re.DOTALL)
        if brace_match:
            text = brace_match.group(0)
    
    # Try direct JSON parse first (most common case)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass  # Continue with fixing steps
    
    # Fix common JSON issues
    # Remove trailing commas before } or ]
    text = re.sub(r',\s*([}\]])', r'\1', text)
    
    # Remove comments (simple // and /* */) - but be careful not to break strings
    # Only remove comments outside of strings
    lines = text.split('\n')
    fixed_lines = []
    in_string = False
    for line in lines:
        # Simple heuristic: track string state
        if '//' in line and not in_string:
            line = re.sub(r'//.*$', '', line)
        fixed_lines.append(line)
        # Update in_string state (simplified)
        in_string = (line.count('"') - line.count('\\"')) % 2 == 1
    text = '\n'.join(fixed_lines)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    
    # Convert single quotes to double (ONLY if not already valid JSON)
    # Be very careful - only do this if we detected single quotes
    if "'" in text and '"' not in text[:100]:  # Heuristic: likely Python dict
        text = re.sub(r"'([^']*)':", r'"\1":', text)
        text = re.sub(r":\s*'([^']*)'", r': "\1"', text)
    
    # Ensure closing braces
    open_braces = text.count('{')
    close_braces = text.count('}')
    if open_braces > close_braces:
        text += '}' * (open_braces - close_braces)
    
    # Strip HTML tags (but preserve JSON structure)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Limit string lengths (prevent DoS)
    if len(text) > 50000:
        return None
    
    # Try parsing again after fixes
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Last resort: try minimal fixes
        try:
            # Only fix if it's clearly not valid JSON
            if not text.startswith('{'):
                return None
            # Don't do aggressive fixes on valid-looking JSON
            return None
        except Exception:
            return None


def validate_target_percent(percent_str: str) -> str:
    """Validate and normalize target_percent: +X% or 'complete'."""
    if not percent_str:
        return "+10%"
    percent_str = percent_str.strip()
    if percent_str.lower() == 'complete':
        return 'complete'
    # Must match +X% or -X% format
    if re.match(r'^[+\-]?\d+%$', percent_str):
        return percent_str
    return "+10%"  # Default

def validate_target_days(days: Any) -> int:
    """Validate target_days: must be 14, 30, 60, or 90."""
    if isinstance(days, int):
        if days in [14, 30, 60, 90]:
            return days
        return 30  # Default
    if isinstance(days, str):
        try:
            days_int = int(days.strip())
            if days_int in [14, 30, 60, 90]:
                return days_int
        except ValueError:
            pass
    return 30  # Default


def repair_fill(report_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Repair and fill missing/invalid fields in report dictionary.
    Ensures all required fields are present with safe defaults.
    """
    # Ensure schema_version
    report_dict['schema_version'] = report_dict.get('schema_version', '1.0')
    
    # Repair short_summary
    summary = report_dict.get('short_summary', '')
    if not summary or len(summary) < 20:
        report_dict['short_summary'] = 'Insufficient data - expand search scope to generate comprehensive summary.'
    else:
        report_dict['short_summary'] = summary[:300]
    
    # Repair actions (must be exactly 5)
    actions = report_dict.get('actions', [])
    if not isinstance(actions, list):
        actions = []
    
    # Ensure exactly 5 actions
    while len(actions) < 5:
        actions.append({
            'title': 'Additional action pending - expand research scope',
            'kpi': 'completion',
            'target_percent': '+10%',
            'target_days': 30,
            'how_steps': ['Gather additional data', 'Analyze findings', 'Implement recommendations'],
            'tool': 'Research tools',
            'effort': 'M',
            'impact': 'M'
        })
    
    # Limit to 5 if more
    actions = actions[:5]
    
    # Repair each action
    for i, action in enumerate(actions):
        if not isinstance(action, dict):
            actions[i] = {
                'title': f'Action {i+1} - data incomplete',
                'kpi': 'completion',
                'target_percent': '+10%',
                'target_days': 30,
                'how_steps': ['Review data', 'Plan approach', 'Execute'],
                'tools': ['Tool TBD', 'Tool TBD', 'Tool TBD'],
                'effort': 'M',
                'impact': 'M'
            }
            continue
        
        # Repair target_percent and target_days (migrate from old target_by if present)
        if 'target_by' in action:
            # Migrate old date format to relative days
            action['target_percent'] = '+10%'
            action['target_days'] = 30
            del action['target_by']
        
        # Validate and repair target_percent
        if 'target_percent' not in action:
            action['target_percent'] = '+10%'
        else:
            action['target_percent'] = validate_target_percent(str(action['target_percent']))
        
        # Validate and repair target_days
        if 'target_days' not in action:
            action['target_days'] = 30
        else:
            action['target_days'] = validate_target_days(action['target_days'])
        
        # Ensure how_steps is list of 3
        how_steps = action.get('how_steps', [])
        if not isinstance(how_steps, list):
            how_steps = []
        while len(how_steps) < 3:
            how_steps.append('See documentation')
        action['how_steps'] = how_steps[:3]
        
        # Migrate tool → tools (backward compatibility)
        if 'tool' in action and 'tools' not in action:
            # Convert single tool to list of 3
            single_tool = str(action['tool']).strip()
            action['tools'] = [single_tool, single_tool, single_tool]
            del action['tool']
        
        # Validate and repair tools list
        if 'tools' not in action:
            action['tools'] = ['Tool TBD', 'Tool TBD', 'Tool TBD']
        else:
            tools = action.get('tools', [])
            if not isinstance(tools, list):
                tools = [str(tools)]
            # Ensure exactly 3 tools
            while len(tools) < 3:
                tools.append('Tool TBD')
            action['tools'] = [str(t).strip()[:100] for t in tools[:3]]
        
        # Fill defaults
        action['title'] = action.get('title', f'Action {i+1}')[:120]
        action['kpi'] = action.get('kpi', 'metric')[:60]
        action['effort'] = action.get('effort', 'M')
        action['impact'] = action.get('impact', 'M')
    
    report_dict['actions'] = actions
    
    # Repair exec_summary (4-6 items)
    exec_summary = report_dict.get('exec_summary', [])
    if not isinstance(exec_summary, list):
        exec_summary = []
    
    # Dedupe (simple exact match for now)
    seen = set()
    unique = []
    for item in exec_summary:
        item_str = str(item).strip()[:240]
        if item_str and item_str not in seen:
            seen.add(item_str)
            unique.append(item_str)
    
    while len(unique) < 4:
        unique.append('Insufficient data - expand search scope')
    report_dict['exec_summary'] = unique[:6]
    
    # Repair findings (6-10 items)
    findings = report_dict.get('findings', [])
    if not isinstance(findings, list):
        findings = []
    
    # Dedupe
    seen = set()
    unique = []
    for item in findings:
        item_str = str(item).strip()[:240]
        if item_str and item_str not in seen:
            seen.add(item_str)
            unique.append(item_str)
    
    while len(unique) < 6:
        unique.append('Limited public data available for this query (consider refining search terms)')
    report_dict['findings'] = unique[:10]
    
    # Repair gaps (3-8 items)
    gaps = report_dict.get('gaps', [])
    if not isinstance(gaps, list):
        gaps = []
    
    seen = set()
    unique = []
    for item in gaps:
        item_str = str(item).strip()[:200]
        if item_str and item_str not in seen:
            seen.add(item_str)
            unique.append(item_str)
    
    while len(unique) < 3:
        unique.append('Market research incomplete - expand search scope')
    report_dict['gaps'] = unique[:8]
    
    # Repair sources (2-10 items)
    sources = report_dict.get('sources', [])
    if not isinstance(sources, list):
        sources = []
    
    # Convert string sources to Source objects
    repaired_sources = []
    for source in sources:
        if isinstance(source, str):
            # Try to parse as URL
            if source.startswith(('http://', 'https://')):
                repaired_sources.append({'url': source, 'citation': source})
            else:
                repaired_sources.append({'url': None, 'citation': source[:200]})
        elif isinstance(source, dict):
            repaired_sources.append({
                'url': source.get('url'),
                'citation': source.get('citation', 'Unknown source')[:200]
            })
        else:
            repaired_sources.append({'url': None, 'citation': 'Unknown source'})
    
    while len(repaired_sources) < 2:
        repaired_sources.append({'url': None, 'citation': 'Additional research needed'})
    
    report_dict['sources'] = repaired_sources[:10]
    
    return report_dict


def extract_and_parse_json(text: str, retry_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from text and parse it robustly.
    Returns parsed dictionary or None if completely unparseable.
    """
    # Try robust parsing
    parsed = robust_json_load(text)
    if parsed:
        # Try to repair and fill
        try:
            repaired = repair_fill(parsed)
            return repaired
        except Exception as e:
            # Log but don't fail completely
            import logging
            logging.getLogger(__name__).warning(f"repair_fill failed: {e}")
            # Return original if repair fails
            return parsed
    
    return None

