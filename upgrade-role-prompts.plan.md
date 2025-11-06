<!-- f9929601-b252-4f0f-94bb-a7d96797eabc 51655cd9-c2cb-488c-8d6b-40294ffbd240 -->
# Code Audit and Cleanup Plan

## Issues Found

### 1. **Time Estimate Functionality - REMOVE**
- `_get_time_estimate()` function (lines 141-148) - user requested removal
- Call to `_get_time_estimate()` in `_fmt_action_head()` (line 182)
- Badge text should change from "Start here (X hours)" to just "Start here"

### 2. **Broken Function - send_email()**
- Line 618-620: `send_email()` calls `send_email_direct()` but missing `to_email` parameter
- This function is used by `email_agent` Agent but won't work correctly
- Need to check if `send_email` tool is actually used or if it's dead code

### 3. **Unused Regex - H2**
- Line 137: `H2 = re.compile(...)` is defined but never used
- `_section()` uses its own inline regex patterns
- Safe to remove

### 4. **Potentially Unused Import - To**
- Line 9: `To` imported from sendgrid.helpers.mail but may not be used
- Need to verify - we use `Email()` and `Personalization()` now

### 5. **Unused Function Check**
- `send_email()` - used by `email_agent` Agent, but Agent may not be used
- Check if `email_agent` Agent object is actually imported/used anywhere

### 6. **Footer Links Not Working - CRITICAL**
- Footer links (LinkedIn, GitHub, Website, View site) appear but don't work
- Need to verify HTML structure and href attributes in EMAIL_TEMPLATE
- Check BRAND dictionary URLs are correct and properly escaped in template
- Issue: URLs in template use `{linkedin_url}` but template.format() may not be escaping correctly

### 7. **Sources Section Too Light**
- User reports sources section seems incomplete
- Verify `_format_sources_markdown()` is extracting all URLs from markdown
- Check if Sources section parsing is working correctly
- May need to scan entire document for URLs, not just Sources section

### 8. **Hero Card Background Color**
- Change hero card background from light grey (#f9fafb) to navy (brand-aligned)
- Update EMAIL_TEMPLATE card background color (line 54)
- Ensure text contrast is readable on navy background (may need white text)
- Use navy like #1e3a8a or #1e40af (brand-aligned)

### 9. **Executive Summary Duplicates Action Board - CRITICAL**
- Current fallback just rehashes action titles with generic "why it matters"
- Should be flowy narrative about:
  - Industry context in the specific market/location
  - Market dynamics and competitive landscape
  - WHY the recommended actions matter (strategic reasoning)
  - Market trends and gaps observed
  - NOT just a list of what to do
- Need to rewrite `_fallback_exec_summary()` to generate contextual narrative
- Should extract market insights from Main Findings section
- Convert competitor data, pricing, services into narrative context
- Explain strategic rationale for actions

## Implementation Steps

### Step 1: Remove Time Estimate
1. Delete `_get_time_estimate()` function (lines 141-148)
2. Update `_fmt_action_head()` to remove time_str calculation and badge formatting
3. Change badge from `"Start here ({time_str})"` to `"Start here"`

### Step 2: Fix or Remove send_email()
1. Check if `email_agent` Agent is used in codebase
2. If unused: Remove `send_email()` function and `email_agent` Agent object
3. If used: Fix `send_email()` signature to match expected usage pattern

### Step 3: Remove Dead Code
1. Remove `H2` regex constant (line 137)
2. Verify `To` import - remove if unused
3. Remove any other unused constants/imports

### Step 4: Fix Footer Links
1. Inspect EMAIL_TEMPLATE footer section (lines 112-129)
2. Verify `{linkedin_url}`, `{github_url}`, `{site_url}` placeholders are in template
3. Check BRAND dictionary URLs are correct
4. Issue: Template.format() with `**BRAND` should work, but verify URLs aren't being double-escaped
5. Test that links render as clickable `<a>` tags with proper href
6. Check if issue is in template formatting or actual URL values

### Step 5: Enhance Sources Section
1. Review `_format_sources_markdown()` function
2. Verify it extracts all URLs from Sources section markdown
3. Check if `_section(report_md, "Sources")` is finding the section correctly
4. Consider scanning entire document for URLs if Sources section is sparse
5. Ensure sources are being parsed from all formats (markdown links, plain URLs, domain mentions)

### Step 6: Change Hero Card to Navy
1. Update EMAIL_TEMPLATE hero card background (line 54)
2. Change `background:{card}` to navy color `#1e3a8a` or `#1e40af`
3. Update text colors: title and subtitle should be white or very light (#ffffff or #f3f4f6)
4. Test readability and contrast
5. Keep border if needed for definition

### Step 7: Rewrite Executive Summary
1. Rewrite `_fallback_exec_summary()` function completely
2. Extract market insights from Main Findings section:
   - Competitor pricing, services, ratings
   - Market gaps and opportunities
   - Industry trends
3. Extract location/business context from subject or report
4. Generate flowy narrative (not bullet points) that includes:
   - Industry/market context specific to location
   - Competitive landscape insights ("X firms charge Y, while Z offers...")
   - Market dynamics and trends ("Most local firms lack...", "The market shows...")
   - WHY the actions matter (strategic reasoning, not just "improves position")
   - Connect findings to actionable opportunities
5. Format as paragraphs, not bullets
6. If real Executive Summary exists but is action-focused, enhance it too
7. Use Main Findings data to build rich context

### Step 8: Verification
1. Run `python -m py_compile email_agent.py`
2. Check all imports are still valid
3. Verify no broken references to removed functions
4. Test that `send_email_direct()` still works correctly
5. Manually inspect HTML output to verify:
   - Footer links are clickable and work
   - Sources show all URLs
   - Hero card is navy with readable white text
   - Executive Summary is narrative flow, not action list

## Files to Modify
- `email_agent.py` (primary file)
- No other files should need changes (only exports are `send_email_direct`, `mask_email`, `email_agent`)

## Risk Assessment
- **Low Risk**: Removing time estimate - straightforward deletion
- **Medium Risk**: `send_email()` function - need to verify usage before removing
- **Low Risk**: Removing unused regex/imports - safe cleanup
- **High Risk**: Executive Summary rewrite - must not break existing functionality
- **Medium Risk**: Footer links - may require template restructuring
- **Low Risk**: Hero card color change - straightforward styling

### To-dos
- [ ] Remove time estimate functionality
- [ ] Fix or remove send_email() function
- [ ] Remove unused H2 regex and verify To import
- [ ] Fix footer links (verify URLs are clickable)
- [ ] Enhance sources section extraction
- [ ] Change hero card to navy background with white text
- [ ] Rewrite Executive Summary as flowy narrative with market context

