import pytest
from app.parser import fix_ligatures, parse_pdf

def test_fix_ligatures():
    assert fix_ligatures("Speciﬁcations") == "Specifications"
    assert fix_ligatures("cuﬀ") == "cuff"

def test_parser_irregularities():
    # We will test against the real PDF to ensure the irregularities are handled
    nodes = parse_pdf("data/ct200_manual.pdf")
    
    # Irregularity 1: Ligatures and multi-font spans (hyphens)
    # Section 1.1 should have "CT-200" not "CT - 200" or similar
    # Find node 1.1
    node_1_1 = None
    for n in nodes[0]["children"]:
        if n["heading"].startswith("1.1"):
            node_1_1 = n
            break
            
    assert node_1_1 is not None
    assert "CT-200" in node_1_1["body_text"]
    assert "cuff" in nodes[0]["children"][1]["body_text"].lower() or "cuﬀ" not in nodes[0]["children"][1]["body_text"]

    # Irregularity 2: Out of order numbering (3.4 before 3.3)
    # The parser should still nest them correctly under 3.
    node_3 = next(n for n in nodes if n["heading"].startswith("3."))
    headings = [c["heading"] for c in node_3["children"]]
    assert any(h.startswith("3.4") for h in headings)
    assert any(h.startswith("3.3") for h in headings)
    
    # Irregularity 3: Inconsistent font sizing (2.1.1.1 is size 11.0 but bold)
    node_2 = next(n for n in nodes if n["heading"].startswith("2."))
    node_2_1 = next(c for c in node_2["children"] if c["heading"].startswith("2.1"))
    node_2_1_1_1 = next(c for c in node_2_1["children"] if c["heading"].startswith("2.1.1.1"))
    assert node_2_1_1_1 is not None
    assert node_2_1_1_1["level"] == 4
    
    # Irregularity 4: Cross page content (3.1 spans pages 2 and 3)
    node_3_1 = next(c for c in node_3["children"] if c["heading"].startswith("3.1"))
    assert "Press and hold the power button" in node_3_1["body_text"]
    assert "Use the profile button to select User 1" in node_3_1["body_text"]
