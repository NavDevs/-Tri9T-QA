from rapidfuzz import fuzz
import difflib

def generate_diff(old_text: str, new_text: str) -> str:
    diff = difflib.unified_diff(
        old_text.splitlines(),
        new_text.splitlines(),
        fromfile='v1',
        tofile='v2',
        lineterm=''
    )
    return '\n'.join(diff)

def flatten_tree(nodes, parent_logical_id=None):
    flat = []
    for n in nodes:
        flat.append({
            "node": n,
            "parent_logical_id": parent_logical_id
        })
        flat.extend(flatten_tree(n["children"], n["logical_node_id"]))
    return flat

def match_versions(v1_tree, v2_tree, threshold=80.0):
    v1_flat = flatten_tree(v1_tree)
    v2_flat = flatten_tree(v2_tree)
    
    v1_by_logical_id = {item["node"]["logical_node_id"]: item for item in v1_flat}
    v1_by_parent = {}
    for item in v1_flat:
        pid = item["parent_logical_id"]
        if pid not in v1_by_parent:
            v1_by_parent[pid] = []
        v1_by_parent[pid].append(item)
        
    results = []
    
    for item in v2_flat:
        v2_node = item["node"]
        v2_parent = item["parent_logical_id"]
        v2_logical = v2_node["logical_node_id"]
        
        match = None
        confidence = "high"
        
        # Primary: logical_node_id match
        if v2_logical in v1_by_logical_id:
            match = v1_by_logical_id[v2_logical]["node"]
        else:
            # Fallback: fuzzy match on heading text among v1 siblings
            siblings = v1_by_parent.get(v2_parent, [])
            best_score = 0
            best_sibling = None
            for sib in siblings:
                score = fuzz.ratio(v2_node["heading"], sib["node"]["heading"])
                if score > best_score:
                    best_score = score
                    best_sibling = sib["node"]
            
            if best_score >= threshold:
                match = best_sibling
                confidence = "low"
                # Important: Adopt the v1 logical_node_id so it's treated as the same node
                v2_node["logical_node_id"] = match["logical_node_id"]
                
        if match:
            if match["content_hash"] == v2_node["content_hash"]:
                status = "unchanged"
                diff = ""
            else:
                status = "changed"
                diff = generate_diff(match["body_text"], v2_node["body_text"])
        else:
            status = "added"
            diff = ""
            
        results.append({
            "v2_node": v2_node,
            "v1_node": match,
            "status": status,
            "match_confidence": confidence,
            "diff": diff
        })
        
    return results
