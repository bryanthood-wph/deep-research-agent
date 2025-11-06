"""
Deterministic markdown renderer for Report schema.
Converts structured Report to markdown format for email rendering.
"""

from schemas import Report, ActionItem


def render_action_item(action: ActionItem) -> str:
    """Render a single action item to markdown."""
    # Format: Action — KPI: <metric> Target: +X% in <14/30/60/90> days (Effort:L/M/H; Impact:L/M/H) | HOW: 1) <step> 2) <step> 3) <step> | TOOLS: 1) <tool> 2) <tool> 3) <tool>
    
    how_steps = ' | '.join([f"{i+1}) {step}" for i, step in enumerate(action.how_steps)])
    tools_list = ' '.join([f"{i+1}) {tool}" for i, tool in enumerate(action.tools)])
    
    action_line = (
        f"{action.title} — KPI: {action.kpi} Target: {action.target_percent} in {action.target_days} days "
        f"(Effort:{action.effort}; Impact:{action.impact}) | "
        f"HOW: {how_steps} | TOOLS: {tools_list}"
    )
    
    return action_line


def render_report_to_markdown(report: Report) -> str:
    """
    Render a Report schema to markdown format.
    Deterministic: same Report → same markdown every time.
    """
    lines = []
    
    # Action Board
    lines.append("## Action Board")
    lines.append("")
    for action in report.actions:
        lines.append(f"- {render_action_item(action)}")
    lines.append("")
    
    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    for item in report.exec_summary:
        lines.append(f"- {item}")
    lines.append("")
    
    # Main Findings
    lines.append("## Main Findings")
    lines.append("")
    for finding in report.findings:
        lines.append(f"- {finding}")
    lines.append("")
    
    # Dogs Not Barking
    lines.append("## Dogs Not Barking")
    lines.append("")
    lines.append("Market gaps and unmet opportunities in this area:")
    lines.append("")
    for gap in report.gaps:
        lines.append(f"- {gap}")
    lines.append("")
    
    # Sources
    lines.append("## Sources")
    lines.append("")
    for source in report.sources:
        if source.url:
            lines.append(f"- {source.url}")
        else:
            lines.append(f"- {source.citation}")
    lines.append("")
    
    return "\n".join(lines)

