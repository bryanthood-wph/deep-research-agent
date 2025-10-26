import pytest
import asyncio
from smb_briefs import writer_instructions

@pytest.mark.asyncio
async def test_writer_instructions_builds_prompt():
    text = writer_instructions("Competitor Snapshot", "Acme Plumbing", "Austin, TX")
    assert "SMB Decision Brief" in text
