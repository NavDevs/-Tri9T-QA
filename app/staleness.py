from sqlalchemy.orm import Session
from app.models import DocumentVersion, Node
from app.versioning import generate_diff

def check_staleness(db: Session, generation_record: dict) -> dict:
    """
    Given a generation record, checks if the underlying source nodes
    have changed in the LATEST document version.
    
    Limitation Note (TRD 7): This relies entirely on text-hash diffing. 
    It cannot distinguish a cosmetic wording fix from a critical changed 
    clinical threshold (e.g., "150 mmHg" -> "160 mmHg"). Both trip the same flag.
    """
    latest_version = db.query(DocumentVersion).order_by(DocumentVersion.version_number.desc()).first()
    if not latest_version:
        return {"is_stale": False, "details": []}
        
    is_stale = False
    details = []
    
    source_hashes = generation_record.get("source_node_hashes", [])
    for src in source_hashes:
        logical_id = src["logical_node_id"]
        old_hash = src["content_hash"]
        
        old_node = db.query(Node).filter(Node.id == src.get("node_id")).first()
        old_body = old_node.body_text if old_node else ""
        
        latest_node = db.query(Node).filter(
            Node.document_version_id == latest_version.id,
            Node.logical_node_id == logical_id
        ).first()
        
        node_stale = False
        diff = ""
        
        if not latest_node:
            node_stale = True
            diff = generate_diff(old_body, "")
        elif latest_node.content_hash != old_hash:
            node_stale = True
            diff = generate_diff(old_body, latest_node.body_text)
            
        if node_stale:
            is_stale = True
            
        details.append({
            "logical_node_id": logical_id,
            "stale": node_stale,
            "diff": diff
        })
        
    return {
        "is_stale": is_stale,
        "details": details
    }
