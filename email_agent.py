import os
import re
import html
import datetime
from typing import Dict, Optional
from urllib.parse import urlparse, urlunparse, parse_qsl

import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To, Bcc, Personalization, TrackingSettings, ClickTracking
from agents import Agent, function_tool, ModelSettings

BRAND = {
    "wordmark": "B. Colby Hood MBA",
    "accent": "#f97316",
    "text":   "#111827",
    "muted":  "#6b7280",
    "bg":     "#ffffff",
    "card":   "#f9fafb",
    "button_text": "#ffffff",
    "link":   "#0ea5e9",
    "site_url": "https://bryanthood-wph.github.io/index.html",
    "linkedin_url": "https://www.linkedin.com/in/colby-hood-mba-336156150/",
    "github_url": "https://github.com/bryanthood-wph",
}

EMAIL_TEMPLATE = """<!doctype html>
<html lang="en"><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="x-ua-compatible" content="ie=edge">
<title>{subject}</title>
</head>
<body style="margin:0;padding:0;background:{bg};color:{text};font-family:-apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;-webkit-font-smoothing:antialiased;-ms-text-size-adjust:100%;-webkit-text-size-adjust:100%;">
  <!-- hidden preheader -->
  <div style="display:none!important;visibility:hidden;overflow:hidden;opacity:0;color:transparent;height:0;width:0;line-height:1px;max-height:0;max-width:0;">
    {preheader}
  </div>

  <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
    <tr>
      <td align="center" style="padding:24px;">
        <table role="presentation" width="640" cellpadding="0" cellspacing="0" style="width:640px;max-width:640px;">
          
          <!-- Brand header -->
          <tr>
            <td style="padding:12px 8px 8px;">
              <div style="font-weight:700;font-size:18px;line-height:1.25;color:{text};font-family: 'Times New Roman', Georgia, serif;">{wordmark}</div>
              <div style="font-size:12px;line-height:1.4;color:{muted};">AI automation • Finance ops • Analytics engineering</div>
            </td>
          </tr>

          <!-- Hero card -->
          <tr>
            <td style="padding:12px 0 0;">
              <table role="presentation" width="100%" style="background:#0f172a;border:1px solid #0b1220;border-radius:12px;">
                <tr>
                  <td style="padding:20px 24px;">
                    <div style="font-size:20px;font-weight:700;line-height:1.3;margin:0 0 6px;color:#ffffff;">{hero_title}</div>
                    <div style="font-size:14px;line-height:1.5;color:#cbd5e1;">{hero_sub}</div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Action Board -->
          <tr>
            <td style="padding:24px 0 8px;">
              <table role="presentation" width="100%">
                <tr>
                  <!-- visual spine -->
                  <td width="6" style="border-left:2px solid {accent};padding-left:12px;"></td>
                  <td>
                    <div style="font-size:16px;font-weight:700;margin:0 0 8px;color:{text};">Action Board</div>
                    <ul style="list-style:none;margin:0;padding:0;">
                      {actions_html}
                    </ul>

                    <!-- CTA (bulletproof-ish for Outlook) -->
                    {cta_html}
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Executive Summary -->
          <tr>
            <td style="padding:16px 0 0;">
              <h2 style="font-size:18px;line-height:1.3;margin:0 0 8px;color:{text};">Executive Summary</h2>
              {exec_summary_html}
            </td>
          </tr>

          <!-- Main Findings -->
          <tr>
            <td style="padding:16px 0 0;">
              <h2 style="font-size:18px;line-height:1.3;margin:0 0 8px;color:{text};">Main Findings</h2>
              {findings_html}
            </td>
          </tr>

          <!-- Dogs Not Barking -->
          <tr>
            <td style="padding:16px 0 0;">
              <h2 style="font-size:18px;line-height:1.3;margin:0 0 8px;color:{text};">Dogs Not Barking</h2>
              <p style="margin:0 0 8px;color:#6b7280;font-size:14px;">Market gaps and unmet opportunities in this area:</p>
              <ul style="margin:0;padding-left:18px;">
                {gaps_html}
              </ul>
            </td>
          </tr>

          <!-- Sources -->
          <tr>
            <td style="padding:16px 0 8px;">
              <h2 style="font-size:18px;line-height:1.3;margin:0 0 8px;color:{text};">Sources</h2>
              <ul style="margin:0;padding-left:18px;">
                {sources_html}
              </ul>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:20px 0;border-top:1px solid #e5e7eb;">
              <table role="presentation" width="100%">
                <tr>
                  <td style="font-size:12px;line-height:1.4;color:{muted};">
                    © {year} {wordmark} —
                    <a href="{linkedin_url}" target="_blank" rel="noopener" style="color:{link};text-decoration:underline;padding:0 2px;">LinkedIn</a> •
                    <a href="{github_url}" target="_blank" rel="noopener" style="color:{link};text-decoration:underline;padding:0 2px;">GitHub</a> •
                    <a href="{site_url}" target="_blank" rel="noopener" style="color:{link};text-decoration:underline;padding:0 2px;">Website</a>
                  </td>
                  <td align="right">
                    <a href="{site_url}" target="_blank" rel="noopener" style="font-size:12px;color:{link};text-decoration:underline;padding:0 2px;">View site</a>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body></html>"""

H2 = re.compile(r"^\s{0,3}##\s+(.*)$", re.M)
MD_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
PLAIN_URL = re.compile(r"(https?://[\w\-._~:/?#\[\]@!$&'()*+,;=%]+)")

def _get_action_category(raw: str) -> str:
    """Determine emoji category based on action content."""
    lower = raw.lower()
    if any(word in lower for word in ["audit", "baseline", "setup", "configure", "install"]):
        return "🔧"
    elif any(word in lower for word in ["increase", "grow", "boost", "improve", "enhance"]):
        return "📈"
    elif any(word in lower for word in ["tool", "software", "platform", "system"]):
        return "🧰"
    elif any(word in lower for word in ["launch", "start", "create", "build", "develop"]):
        return "🚀"
    else:
        return "✅"

def _fmt_action_head(raw: str, is_first: bool = False, is_quick_win: bool = False) -> str:
    """Format action title with emoji category and optional 'Start here' and 'Quick win' badges."""
    t = raw.strip().lstrip("-•* ")
    owner = ""
    m = re.match(r'^\[?Owner:\s*([^\]\|]+)\]?', t, flags=re.I)
    if m: owner = m.group(1).strip()
    m2 = re.search(r'Action:\s*([^|—]+)', t, flags=re.I)
    action = m2.group(1).strip() if m2 else t.split("—", 1)[0].split("|", 1)[0].split("KPI:", 1)[0].strip()
    head = f"{html.escape(owner + ': ' if owner else '')}{html.escape(action)}"
    
    # Add emoji category
    emoji = _get_action_category(raw)
    head_html = f"{emoji} <strong style='font-size:18px;font-weight:700;'>{head}</strong>"
    
    badges = []
    
    # Add "Start here" badge for first action (no time shown)
    if is_first:
        badges.append(f"<span style='background:{BRAND['accent']};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;margin-left:8px;'>Start here</span>")
    
    # Add "Quick win" badge for low-effort actions or if flagged
    if is_quick_win:
        badges.append(f"<span style='background:#10b981;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;margin-left:8px;'>Quick win</span>")
    
    if badges:
        head_html += " " + " ".join(badges)
    
    return head_html

def _grab(raw: str, pat: str):
    m = re.search(pat + r'\s*:\s*([^;|\]\)]+)', raw, flags=re.I)
    return m.group(1).strip() if m else None

def _fmt_action_meta(raw: str) -> str:
    """Format metrics with plain language labels."""
    kpi    = _grab(raw, r'KPI')
    target = _grab(raw, r'Target')
    base   = _grab(raw, r'(?:Baseline|B)')
    src    = _grab(raw, r'(?:Source|Src)')
    effort = _grab(raw, r'Effort')
    impact = _grab(raw, r'Impact')
    season = None
    m = re.search(r'\[Season(?:ality)?:\s*([^\]]+)\]', raw, flags=re.I)
    if m: season = m.group(1).strip()
    
    # Plain language labels
    result_parts = []
    tracking_parts = []
    
    if kpi:    result_parts.append(f"Goal: {html.escape(kpi)}")
    if target: result_parts.append(f"Aim for: {html.escape(target)}")
    if base:   result_parts.append(f"Currently: {html.escape(base)}")
    if src:    tracking_parts.append(f"Track with: {html.escape(src)}")
    
    # Build result & tracking line
    result_line = " | ".join(result_parts) if result_parts else ""
    if tracking_parts:
        result_line = (result_line + " | " + " | ".join(tracking_parts)) if result_line else " | ".join(tracking_parts)
    
    # Effort/Impact on separate line
    effort_impact = []
    if effort: effort_impact.append(f"Effort: {html.escape(effort)}")
    if impact: effort_impact.append(f"Impact: {html.escape(impact)}")
    
    html_parts = []
    if result_line:
        html_parts.append(f"<div style='margin:8px 0 4px 0;color:#6b7280;font-size:13px;line-height:1.4;'>{result_line}</div>")
    if effort_impact:
        html_parts.append(f"<div style='margin:4px 0 0 0;color:#6b7280;font-size:13px;'>{' • '.join(effort_impact)}</div>")
    
    return "".join(html_parts)

def _fmt_action_how_and_tool(raw: str) -> str:
    """Format HOW steps and Tool into separate, clearly labeled blocks."""
    parts = re.split(r'\|\s*TOOL\s*:\s*', raw, flags=re.I)
    left  = parts[0]
    tool  = parts[1].strip() if len(parts) > 1 else None
    m = re.search(r'(?:→\s*)?HOW\s*:\s*(.+)$', left, flags=re.I)
    how   = m.group(1).strip() if m else ""
    steps = [s.strip() for s in re.split(r'(?:(?:^|\s)\d+\)\s*|;|\s\|\s)', how) if s.strip()]
    
    html_parts = []
    
    # What to do block
    if steps:
        items = "".join(f"<li style='margin:0 0 6px 0;line-height:1.5;'>{html.escape(s)}</li>" for s in steps[:6])
        html_parts.append(
            f"<div style='margin:12px 0 8px 0;'>"
            f"<div style='font-weight:600;color:#111827;font-size:14px;margin-bottom:4px;'>What to do:</div>"
            f"<ol style='margin:0 0 0 20px;padding:0;color:#111827;font-size:14px;line-height:1.5;'>{items}</ol>"
            f"</div>"
        )
    
    # Why it matters block
    why_text = _get_why_it_matters(raw)
    html_parts.append(
        f"<div style='margin:8px 0;'>"
        f"<span style='font-weight:600;color:#111827;font-size:14px;'>Why it matters:</span> "
        f"<span style='color:#374151;font-size:14px;line-height:1.5;'>{html.escape(why_text)}</span>"
        f"</div>"
    )
    
    # Tool block
    if tool:
        html_parts.append(
            f"<div style='margin:8px 0 0 0;'>"
            f"<span style='font-weight:600;color:#111827;font-size:14px;'>Tool:</span> "
            f"<span style='color:{BRAND['accent']};font-weight:600;font-size:14px;'>{html.escape(tool)}</span>"
            f"</div>"
        )
    
    return "".join(html_parts)

def _strip_utm(url: str) -> str:
    try:
        p = urlparse(url)
        kept = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
        q = "&".join(f"{k}={v}" for k, v in kept)
        return urlunparse((p.scheme, p.netloc, p.path, p.params, q, p.fragment))
    except Exception:
        return url

def _root(u: str) -> str:
    d = (urlparse(u).netloc or u).lower() if "://" in u else u.lower()
    return d[4:] if d.startswith("www.") else d

def _format_sources_markdown(md: str) -> str:
    if not md or not md.strip():
        return "<p style='color:#6b7280'>No data.</p>"
    urls = []
    for line in md.splitlines():
        m = re.search(r'(https?://\S+)|\b[\w.-]+\.(?:com|org|net|gov|io|ai)\b', line, flags=re.I)
        if m: urls.append(m.group(0))
    seen = set(); lis = []
    for u in urls:
        clean = _strip_utm(u)
        root = _root(clean)
        if root in seen: continue
        seen.add(root)
        href = clean if "://" in clean else "https://" + clean
        lis.append(f"<li style='margin:0 0 8px 0;'><a href='{html.escape(href)}' target='_blank' rel='noopener' style='color:{BRAND['link']};text-decoration:underline;'>{html.escape(root)}</a></li>")
    return "".join(lis) if lis else "<p style='color:#6b7280'>No data.</p>"

def _section(md: str, title: str) -> str:
    """Capture content under heading with flexible matching."""
    # Try multiple variations and header levels
    variations = [title]
    
    # Add common variations
    if title == "Action Board":
        variations.extend(["Actions", "Action Items", "Top Actions", "Action Plan"])
    elif title == "Executive Summary":
        variations.extend(["Executive summary", "Summary", "Overview"])
    elif title == "Main Findings":
        variations.extend(["Findings", "Key Findings", "Main findings"])
    elif title == "Sources":
        variations.extend(["References", "Links", "Source Links"])
    
    # Try each variation with multiple header levels
    for variant in variations:
        for hashes in ["###", "##", "#"]:
            # Case-insensitive, flexible whitespace
            pat = re.compile(
                rf"^\s{{0,3}}{re.escape(hashes)}\s+{re.escape(variant)}\s*$([\s\S]*?)(^\s{{0,3}}#{{{len(hashes)},}}\s+|\Z)",
                re.M | re.I
            )
            m = pat.search(md + "\n## END\n")
            if m and m.group(1).strip():
                return m.group(1).strip()
    
    return ""

def _actions(md: str) -> list[str]:
    """Extract action lines from Action Board section."""
    block = _section(md, "Action Board")
    
    # If we found a section, extract lines
    if block:
        lines = [ln.strip("-• ").strip() for ln in block.splitlines() if ln.strip()]
        # Prefer lines with KPI/Target, fallback to any list items
        action_lines = [ln for ln in lines if "KPI:" in ln and "Target:" in ln]
        if action_lines:
            return action_lines[:5]
        # Fallback: any non-empty lines that look like actions
        return [ln for ln in lines if len(ln) > 10][:5]
    
    # Fallback: scan entire document for action-like patterns
    lines = [ln.strip("-• ").strip() for ln in md.splitlines() if ln.strip()]
    action_lines = [ln for ln in lines if "KPI:" in ln and "Target:" in ln]
    return action_lines[:5] if action_lines else []

def _md_to_html_list(md_block: str) -> str:
    """Convert simple bullets to <ul><li>."""
    if not md_block: return "<p style='color:#6b7280'>No data.</p>"
    items = []
    for ln in md_block.splitlines():
        t = ln.strip()
        if not t: continue
        t = t.lstrip("-• ").strip()
        items.append(f"<li style='margin:0 0 8px 0;'>{_linkify_text(t)}</li>")
    return "".join(items) if items else f"<p>{html.escape(md_block)}</p>"

def _md_to_html_paras(md_block: str) -> str:
    """Very light conversion: split by lines, wrap paras and keep bullets as plain text."""
    if not md_block: return "<p style='color:#6b7280'>No data.</p>"
    parts = [p.strip() for p in re.split(r"\n\s*\n", md_block.strip()) if p.strip()]
    out = []
    for p in parts:
        if p.startswith("-") or p.startswith("•"):
            out.append(f"<ul style='padding-left:18px;margin:0;'>{_md_to_html_list(p)}</ul>")
        else:
            out.append(f"<p style='margin:0 0 8px 0;'>{_linkify_text(p)}</p>")
    return "".join(out)

def _linkify_text(text: str) -> str:
    """Escape text and convert markdown/plain URLs to anchors."""
    if not text:
        return ""

    result = []
    idx = 0
    for match in MD_LINK.finditer(text):
        prefix = text[idx:match.start()]
        result.append(_linkify_plain(prefix))
        label = html.escape(match.group(1).strip())
        url = html.escape(match.group(2).strip())
        result.append(
            f"<a href=\"{url}\" target=\"_blank\" rel=\"noopener\" style='color:{BRAND['link']};text-decoration:underline;'>{label}</a>"
        )
        idx = match.end()
    result.append(_linkify_plain(text[idx:]))
    return "".join(result)

def _linkify_plain(text: str) -> str:
    if not text:
        return ""
    result = []
    last = 0
    for match in PLAIN_URL.finditer(text):
        prefix = text[last:match.start()]
        result.append(html.escape(prefix))
        url = match.group(0)
        url_escaped = html.escape(url)
        result.append(
            f"<a href=\"{url_escaped}\" target=\"_blank\" rel=\"noopener\" style='color:{BRAND['link']};text-decoration:underline;'>{url_escaped}</a>"
        )
        last = match.end()
    result.append(html.escape(text[last:]))
    return "".join(result)

def _first_line_text(md: str) -> str:
    """Preheader seed from first action or first exec bullet."""
    # Try actions first
    acts = _actions(md)
    if acts and acts[0]:
        return acts[0][:120]
    
    # Try executive summary
    es = _section(md, "Executive Summary")
    if es:
        lines = [x.strip() for x in es.splitlines() if x.strip()]
        if lines:
            return lines[0].lstrip("-• ").strip()[:120]
    
    # Fallback: first substantial line from anywhere
    lines = [ln.strip() for ln in md.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    for ln in lines:
        cleaned = ln.lstrip("-• ").strip()
        if len(cleaned) > 20:  # Meaningful content
            return cleaned[:120]
    
    return "Brief ready."

def _get_why_it_matters(action_text: str) -> str:
    """Generate simple 'Why it matters' explanation for an action."""
    action_lower = action_text.lower()
    
    # Common term dictionary with plain language explanations
    explanations = {
        "seo": "SEO (Search Engine Optimization) helps your website show up when people search for your services online.",
        "google business profile": "Your Google Business Profile helps local customers find and contact you.",
        "gbp": "Your Google Business Profile helps local customers find and contact you.",
        "ppc": "PPC (Pay-Per-Click) advertising puts your business at the top of search results.",
        "adwords": "Google Ads puts your business at the top of search results when people search.",
        "crm": "A CRM (Customer Relationship Management) system helps you track clients and follow up effectively.",
        "email marketing": "Email marketing keeps you in touch with past clients and brings them back.",
        "social media": "Social media helps you stay visible and build relationships with potential clients.",
        "website": "Your website is often the first impression potential clients have of your business.",
        "content": "Educational content shows your expertise and builds trust before clients even call you.",
        "blog": "Blogging demonstrates your expertise and helps people find you through search engines.",
        "reviews": "Online reviews are the first thing people check when choosing who to hire.",
        "online booking": "Online booking makes it easier for clients to schedule with you, even after hours.",
        "consultation": "Free consultations lower the barrier for potential clients to reach out.",
        "pricing": "Clear pricing helps clients understand what to expect and builds trust.",
        "video": "Video content is more engaging and helps potential clients feel like they know you.",
        "analytics": "Analytics show what's working and what's not, so you spend time and money wisely.",
    }
    
    # Check for matching terms
    for term, explanation in explanations.items():
        if term in action_lower:
            return explanation
    
    # Generic default explanation
    return "This action helps you compete more effectively and attract clients in your market."

def _fallback_exec_summary(md: str, subject: str = "") -> str:
    """Generate Executive Summary with geography, industry, and market context."""
    # Extract location and business from subject (robust parsing)
    location = ""
    business = ""
    if subject:
        # Try pattern: "Brief: Business – Location" or variations with em-dash
        if ':' in subject:
            after_colon = subject.split(':', 1)[-1].strip()
            # Handle both em-dash (–) and regular dash (-) or comma
            for separator in ['–', '—', '-', ',']:
                if separator in after_colon:
                    parts = after_colon.split(separator, 1)
                    business = parts[0].strip()
                    location = parts[1].strip() if len(parts) > 1 else ""
                    break
        # Fallback: extract location-like patterns (City, ST)
        if not location:
            location_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})\b', subject)
            if location_match:
                location = location_match.group(1)
    
    # Extract Main Findings to pull market trends and competitor context
    findings_section = _section(md, "Main Findings")
    if not findings_section:
        # Direct extraction without fallback to avoid circular dependency
        all_bullets = [ln.strip() for ln in md.splitlines() if ln.strip().startswith(('-', '•'))]
        findings_section = "\n".join(all_bullets[:10])
    
    # Extract concrete data points (competitor names, prices, numbers)
    concrete_facts = []
    market_trends = []
    
    if findings_section:
        trend_indicators = ["market trend", "industry trend", "market pattern", "market gap", "local firms lack", "% of", "of local", "unmet", "gap"]
        for line in findings_section.splitlines():
            line_clean = line.replace("**", "").replace("*", "").strip().strip("-•* ").strip()
            line_lower = line_clean.lower()
            
            # Skip empty lines
            if not line_clean:
                continue
            
            # Look for Market Trend bullets (flexible detection)
            if any(ind in line_lower for ind in trend_indicators):
                market_trends.append(line_clean)
            # Look for concrete facts (firm names, prices, numbers, ratings)
            elif any(word in line for word in ["$", "%"]) or any(word in line_lower for word in ["charges", "rated", "reviews", "offers", "specializes", "provides", "features"]):
                concrete_facts.append(line_clean)
    
    # Build narrative summary (paragraph format, not bullets)
    parts = []
    
    # Geography and industry context - FIX GRAMMAR ISSUE
    if location:
        if business:
            # Fix "the The" issue - check if business name starts with "The"
            business_starts_with_the = business.lower().startswith("the ")
            
            # Try to infer industry from business name
            if any(word in business.lower() for word in ["law", "legal", "attorney", "lawyer"]):
                parts.append(f"In {location}, the legal services market shows distinct competitive patterns.")
            elif any(word in business.lower() for word in ["consulting", "consultant"]):
                parts.append(f"In {location}, the consulting services market presents specific opportunities.")
            else:
                # Use business name without "the" if it already has it
                if business_starts_with_the:
                    parts.append(f"In {location}, {business}'s market shows distinct competitive patterns.")
                else:
                    parts.append(f"In {location}, the {business} market shows distinct competitive patterns.")
        else:
            parts.append(f"The local market in {location} presents specific opportunities and challenges.")
    
    # Add 2-3 concrete facts from findings
    if concrete_facts:
        for fact in concrete_facts[:3]:
            parts.append(fact)
    
    # Market trends (move from Main Findings)
    if market_trends:
        for trend in market_trends[:2]:  # Top 2 market trends
            # Clean up the trend text
            trend_clean = trend.replace("**Market Trend:**", "").replace("**Market Trend**", "").replace("Market Trend:", "").strip()
            if trend_clean:
                parts.append(trend_clean)
    
    # Convert to paragraph format (not bullets)
    if parts:
        return " ".join(parts)
    
    # Final fallback if nothing extracted
    if location:
        return f"Market analysis for {location} reveals competitive positioning opportunities based on local competitor strategies and market gaps."
    return "This brief analyzes the local competitive landscape to identify strategic actions for market positioning."

def _fallback_findings(md: str) -> str:
    """If Main Findings section missing, derive from bullets in document."""
    lines = []
    capture = False
    for raw in md.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("##"):
            lower = stripped.lower()
            if "executive" in lower:
                capture = True
                continue
            if capture:
                break
            continue
        if capture and stripped.startswith(('-', '•')):
            lines.append(stripped)
    if lines:
        return "\n".join(lines)

    # Fallback: take first bullet-rich segment anywhere
    alt_lines = [ln.strip() for ln in md.splitlines() if ln.strip().startswith(('-', '•'))]
    return "\n".join(alt_lines[:6])

def _is_gap_line(text: str) -> bool:
    """Detect if a line describes a market gap (used across sections).

    Heuristics:
    - Positive match on gap patterns (lack, missing, few, unmet, gap in, etc.)
    - Exclude explicit firm fact lines (contain URL in parentheses or Firm-like token followed by a colon)
    - Require meaningful length
    """
    if not text:
        return False

    line_clean = text.replace("**", "").replace("*", "").strip().strip("-•* ").strip()
    line_lower = line_clean.lower()

    # Exclude explicit firm fact lines
    if re.search(r"\(https?://[^)]+\)", line_clean):
        return False
    if re.search(r"[A-Z][A-Za-z&.'-]+(?:\s+[A-Z][A-Za-z&.'-]+){1,}\s*:\s", line_clean):
        return False

    gap_patterns = [
        r"\black\b",
        r"\bdon't\s+(?:offer|provide|have)",
        r"doesn't\s+(?:offer|provide|have)",
        r"\bmissing\b",
        r"\bno\s+(?:firm|competitor|business)\b",
        r"\bfew\s+(?:firms|competitors|businesses)\b",
        r"only\s+\d+\s+(?:of|out of)",
        r"\d+%\s+(?:don't|lack|missing)",
        r"\bunmet\b",
        r"gap\s+in",
    ]

    is_gap = any(re.search(pattern, line_lower) for pattern in gap_patterns)
    return bool(is_gap and len(line_clean) > 20)

def _extract_market_gaps(md: str, location: str = "") -> list[str]:
    """Extract 3 market gaps (Dogs Not Barking) from findings."""
    findings_section = _section(md, "Main Findings")
    if not findings_section:
        all_bullets = [ln.strip() for ln in md.splitlines() if ln.strip().startswith(('-', '•'))]
        findings_section = "\n".join(all_bullets[:15])
    
    gaps = []

    if findings_section:
        for line in findings_section.splitlines():
            line_clean = line.replace("**", "").replace("*", "").strip().strip("-•* ").strip()
            if _is_gap_line(line_clean):
                gaps.append(line_clean)
    
    # Take top 3 gaps
    gaps = gaps[:3]
    
    # Fallback gaps if we don't have 3
    fallback_gaps = [
        "Most local firms lack weekend or evening availability, leaving potential clients underserved",
        "Few competitors offer instant online booking or live chat, creating a convenience gap",
        "Limited use of educational content (blogs, videos, guides) to build trust and expertise"
    ]
    
    # Fill in with fallbacks if needed
    while len(gaps) < 3:
        gaps.append(fallback_gaps[len(gaps)])
    
    return gaps[:3]  # Always return exactly 3

def render_branded_email_html(report_md: str, subject: str, cta_url: Optional[str] = None, cta_label: str = "View Full Report") -> str:
    """Wrap the parsed markdown sections into the branded HTML template."""
    actions = _actions(report_md)
    
    # Check if any action has low effort - if not, mark first as quick win
    has_low_effort = any(_grab(a, r'Effort') and _grab(a, r'Effort').lower() in ['l', 'low'] for a in actions)
    
    actions_html = "".join(
        f"<li style='margin:0 0 16px 0;padding-top:12px;{'border-top:1px solid #e5e7eb;' if idx > 0 else ''}'>"
        f"{_fmt_action_head(a, is_first=(idx == 0), is_quick_win=(not has_low_effort and idx == 0) or (_grab(a, r'Effort') and _grab(a, r'Effort').lower() in ['l', 'low']))}"
        f"<div style='margin-top:8px;'>"
        f"{_fmt_action_how_and_tool(a)}"
        f"{_fmt_action_meta(a)}"
        f"</div>"
        f"</li>"
        for idx, a in enumerate(actions)
    ) or "<li style='color:#6b7280'>No actions provided.</li>"
    
    cta_html = (
        f"<div style='padding-top:16px;'>"
        f"<a href='{html.escape(cta_url)}' target='_blank' rel='noopener' "
        f"style='display:inline-block;background:{BRAND['accent']};color:{BRAND['button_text']};"
        f"text-decoration:none;font-weight:700;font-size:14px;padding:12px 16px;border-radius:8px;"
        f"box-shadow:0 1px 0 rgba(0,0,0,0.08);'>"
        f"{html.escape(cta_label)}</a></div>"
    ) if cta_url else ""
    
    # Executive Summary with guaranteed fallback
    exec_summary_raw = _section(report_md, "Executive Summary")
    if not exec_summary_raw or exec_summary_raw.strip() == "":
        exec_summary_raw = _fallback_exec_summary(report_md, subject)
    exec_summary_html = _md_to_html_paras(exec_summary_raw)
    
    # Main Findings - filter out Market Trend bullets (moved to Executive Summary)
    findings_section  = _section(report_md, "Main Findings")
    if not findings_section:
        findings_section = _fallback_findings(report_md)
    # Remove Market Trend bullets from Main Findings (but keep at least 3 bullets)
    if findings_section:
        all_lines = findings_section.splitlines()
        filtered_lines = []
        trend_indicators = ["market trend", "industry trend", "market pattern", "market gap"]
        for line in all_lines:
            line_clean = line.replace("**", "").replace("*", "").strip()
            line_lower = line_clean.lower()
            # Skip market trend bullets (flexible detection)
            is_trend = any(ind in line_lower for ind in trend_indicators) or ("%" in line_clean and ("of local" in line_lower or "unmet" in line_lower or "gap" in line_lower))
            # Skip gap bullets (centralized detection)
            is_gap = _is_gap_line(line_clean)
            if not (is_trend or is_gap):
                filtered_lines.append(line)
        # Keep at least 3 bullets to avoid empty Main Findings
        if len(filtered_lines) < 3 and len(all_lines) >= 3:
            filtered_lines = all_lines[:5]  # Keep original if filtering would leave too few
        findings_section = "\n".join(filtered_lines) if filtered_lines else findings_section
    findings_html     = _md_to_html_paras(findings_section)
    sources_html      = _format_sources_markdown(_section(report_md, "Sources"))
    
    # Extract location from subject for gap analysis
    location = ""
    if subject:
        location_match = re.search(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})\b', subject)
        if location_match:
            location = location_match.group(1)
    
    # Dogs Not Barking - market gaps
    gaps = _extract_market_gaps(report_md, location)
    gaps_html = "".join(
        f"<li style='margin:0 0 10px 0;color:#374151;font-size:14px;line-height:1.6;'>{html.escape(gap)}</li>"
        for gap in gaps
    )

    hero_title = subject or "SMB Decision Brief"
    hero_sub   = "Action-first summary with clear next steps."
    preheader  = _first_line_text(report_md)
    year       = str(datetime.date.today().year)

    html_out = EMAIL_TEMPLATE.format(
        subject=html.escape(subject or "Brief"),
        preheader=html.escape(preheader),
        hero_title=html.escape(hero_title),
        hero_sub=html.escape(hero_sub),
        actions_html=actions_html,
        cta_html=cta_html,
        exec_summary_html=exec_summary_html,
        findings_html=findings_html,
        gaps_html=gaps_html,
        sources_html=sources_html,
        year=year,
        **BRAND
    )
    return html_out

def mask_email(email: str) -> str:
    """Mask email for privacy: a****@domain.com"""
    try:
        local, domain = email.split('@')
        if len(local) <= 1:
            masked_local = local[0] + "****"
        else:
            masked_local = local[0] + "****"
        return f"{masked_local}@{domain}"
    except Exception:
        return "****@****.***"


def send_email_direct(subject: str, html_body: str, to_email: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body (direct call version)"""
    try:
        # html_body comes as Markdown from the orchestrator (report.markdown_report)
        # Convert to branded HTML using our template
        html_content = render_branded_email_html(
            report_md=html_body,
            subject=subject
        )
        
        # Strip CRLF from subject for safety
        subject = subject.replace('\r', '').replace('\n', '')
        
        # Initialize SendGrid client
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
        
        # Build and send email with BCC using SendGrid's Personalization API
        mail = Mail()
        mail.from_email = Email("colby@colbyhoodconsulting.com")
        mail.subject = subject
        
        # Disable click tracking to prevent SendGrid from wrapping footer links
        try:
            mail.tracking_settings = TrackingSettings(click_tracking=ClickTracking(enable=False))
        except Exception as e:
            # Fallback: continue if tracking settings fail
            print(f"Warning: Could not disable click tracking: {e}")
        
        # Set up personalization with TO and BCC
        personalization = Personalization()
        personalization.add_to(Email(to_email))
        # Avoid duplicate between TO and BCC (SendGrid 400 if same)
        bcc_addr = "brnthood@gmail.com"
        if to_email.strip().lower() != bcc_addr:
            personalization.add_bcc(Email(bcc_addr))
        mail.add_personalization(personalization)
        
        # Add HTML content
        mail.add_content(Content("text/html", html_content))
        
        # Send with proper client and surface error details on 4xx/5xx
        response = sg.send(mail)
        if getattr(response, "status_code", 500) >= 400:
            try:
                body = response.body.decode() if hasattr(response.body, "decode") else str(response.body)
            except Exception:
                body = str(response.body)
            raise Exception(f"SendGrid  {response.status_code}: {body}")
        
        # Log success
        masked = mask_email(to_email)
        print(f"✅ Email sent to {masked}, status: {response.status_code}")
        return {"status": "sent", "to": masked}
        
    except Exception as e:
        # Log detailed error for debugging
        err_detail = getattr(e, "body", None)
        if err_detail is None:
            err_detail = getattr(e, "message", "")
        try:
            err_detail = err_detail.decode() if hasattr(err_detail, "decode") else str(err_detail)
        except Exception:
            err_detail = str(err_detail)
        print(f"❌ EMAIL SEND FAILED: {type(e).__name__}: {str(e)}\n{err_detail}")
        import traceback
        traceback.print_exc()
        # Re-raise with clear message
        raise Exception(f"Email send failed: {str(e)} {err_detail}") from e


@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """Send an email with the given subject and HTML body"""
    return send_email_direct(subject, html_body)


INSTRUCTIONS = """Produce ONE HTML email from a provided report.

Order:
- Subject (clear)
- "Action Board" first as an HTML list (each line uses the standard action format).
- Then the rest of the report as semantic HTML (h1–h3, p, ul/ol, a). No commentary.

Tooling: call the send_email tool exactly once with subject, html_body.

No chain-of-thought. US English.

Example <li>:
<li>Sales Call lapsed quotes — KPI: closes Target: +4 by 2025-11-18 (B:0, Src:CRM; Effort:M; Impact:H) [Season:year-end budgets, Lead:14d]</li>"""

email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
    model_settings=ModelSettings(max_output_tokens=200, temperature=0.2),
)
