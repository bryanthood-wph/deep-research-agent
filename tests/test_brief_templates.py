from brief_templates import TEMPLATES, writer_instructions

def test_writer_instructions_contains_sections():
    assert "Competitor Snapshot" in TEMPLATES
    s = writer_instructions("Competitor Snapshot", "Acme Plumbing", "Austin, TX")
    assert "Executive summary" in s and "Top actions" in s and "Sources" in s
