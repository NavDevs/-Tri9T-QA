import pytest
from app.versioning import generate_diff, match_versions

def test_generate_diff():
    v1 = "Hello world.\nThis is V1."
    v2 = "Hello world.\nThis is V2."
    diff = generate_diff(v1, v2)
    assert "-This is V1." in diff
    assert "+This is V2." in diff

def test_match_versions():
    v1_tree = [
        {
            "logical_node_id": "1::intro",
            "heading": "1. Intro",
            "body_text": "V1 Body",
            "content_hash": "hash1",
            "children": [
                {
                    "logical_node_id": "1.1::sub",
                    "heading": "1.1 Sub",
                    "body_text": "Sub V1",
                    "content_hash": "hashsub1",
                    "children": []
                }
            ]
        }
    ]
    
    v2_tree = [
        {
            "logical_node_id": "1::intro",
            "heading": "1. Intro",
            "body_text": "V1 Body", # unchanged
            "content_hash": "hash1",
            "children": [
                {
                    # Primary mismatch, but high fuzzy similarity
                    "logical_node_id": "1.1::sub-edited",
                    "heading": "1.1 Sub Edited",
                    "body_text": "Sub V2",
                    "content_hash": "hashsub2",
                    "children": []
                },
                {
                    # Added node
                    "logical_node_id": "1.2::new",
                    "heading": "1.2 New",
                    "body_text": "New",
                    "content_hash": "hashnew",
                    "children": []
                }
            ]
        }
    ]
    
    results = match_versions(v1_tree, v2_tree, threshold=60.0)
    
    # 1. Intro should be unchanged
    intro_res = next(r for r in results if r["v2_node"]["heading"] == "1. Intro")
    assert intro_res["status"] == "unchanged"
    assert intro_res["match_confidence"] == "high"
    
    # 1.1 Sub Edited should match 1.1 Sub as 'changed' with low confidence
    sub_res = next(r for r in results if r["v2_node"]["heading"] == "1.1 Sub Edited")
    assert sub_res["status"] == "changed"
    assert sub_res["match_confidence"] == "low"
    assert sub_res["v2_node"]["logical_node_id"] == "1.1::sub" # adopted v1 logical id
    assert "-Sub V1" in sub_res["diff"]
    
    # 1.2 New should be added
    new_res = next(r for r in results if r["v2_node"]["heading"] == "1.2 New")
    assert new_res["status"] == "added"
    assert new_res["v1_node"] is None
