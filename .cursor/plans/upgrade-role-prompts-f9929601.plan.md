<!-- f9929601-b252-4f0f-94bb-a7d96797eabc c48cf0c2-2466-40c6-9ae8-2b2fac789e3e -->
# Fix Duplicate Gap Bullets + Restore Progress Indicator (Red Teamed)

## Problem 1: Duplicate Gap Bullets

**Issue**: Gap bullets appear in both Main Findings and Dogs Not Barking.

**Risk with prior approach**: Naively filtering for words like "few" or "limited" may hide legitimate competitor facts (e.g., "Few firms offer Chapter 7 flat-fee pricing").

**Robust Solution**:

- Centralize gap detection in a single helper used by BOTH sections to ensure consistency:
- Add `_is_gap_line(text: str) -> bool` next to `_extract_market_gaps()` that reuses the same regexes and excludes lines with explicit firm names (contains parentheses URL or a capitalized firm-like token followed by a colon), to avoid removing competitor facts.
- In `render_branded_email_html()`, when building `Main Findings`, filter out lines where `_is_gap_line(line_lower)` is True (in addition to the existing trend filter), and keep the "keep at least 3 bullets" safeguard.
- Dogs Not Barking continues to use `_extract_market_gaps()` which relies on `_is_gap_line()`.

**Change scope**: ~10 lines. Zero behavioral ambiguity because a single source of truth governs both sections.

## Problem 2: Missing Progress Indicator

**Goal**: Bring back live progress updates with the smallest, safest change.

**Risk with prior approach**: A custom sync wrapper around an async generator is brittle and can conflict with Gradio's internal event loop.

**Robust Solution (simpler)**:

- Gradio supports async generator functions directly. Remove the sync wrapper entirely.
- Convert `smb_briefs.generate_brief()` to an async generator that yields status strings at key steps.
- Convert `app_smb.run_brief()` to an async generator that validates email, then `async for`wards those messages to the UI.
- Wire `go.click(fn=run_brief, ...)` directly (no wrapper). Gradio will stream updates to the `status` Markdown.

**Change scope**: ~20 lines across two files. No custom loops, minimal surface area, works across Gradio versions that support async.

## Files to Modify

1. `email_agent.py`

- Add `_is_gap_line()`; use it inside both `_extract_market_gaps()` and the Main Findings filter.

2. `smb_briefs.py`

- Change `generate_brief()` to async generator yielding: "Planning…", "Searching…", "Writing…", "Sending…", "Done".

3. `app_smb.py`

- Change `run_brief()` to async generator; remove `_sync_run`; wire button to `run_brief`.

## Testing

- Run a brief and confirm streamed messages appear in order.
- Verify Main Findings no longer shows gap bullets; Dogs Not Barking always shows exactly 3.
- Sanity check: competitor bullets with URLs/firms stay in Main Findings.
- Quick compile/lint on the 3 changed files.

### To-dos

- [ ] Update INSTRUCTIONS in email_agent.py with compatibility-fixed prompt
- [ ] Update INSTRUCTIONS in planner_agent.py with JSON structure guidance
- [ ] Update INSTRUCTIONS in search_agent.py with new format
- [ ] Update INSTRUCTIONS in writer_agent.py with JSON structure guidance
- [ ] Update writer_instructions() and TEMPLATES in brief_templates.py
- [ ] Run grep checks to verify old prompts removed and new prompts present
- [ ] Run py_compile on all modified files to ensure syntax is valid
- [ ] Redesign action item rendering to show title, HOW steps, Tool, and metrics with better visual hierarchy
- [ ] Replace corporate abbreviations (KPI, B:, Src:, Target) with plain language (Goal, Currently, Track with, Aim for)
- [ ] Debug and fix Executive Summary parsing so it displays content instead of 'No data'
- [ ] Increase spacing between action items and adjust typography for better scannability
- [ ] Generate test brief and validate all improvements are working