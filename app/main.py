from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
import os
import uuid
import datetime

from app.database import engine, Base, get_db
from app.models import DocumentVersion, Node, Selection, selection_node
from app.schemas import NodeResponse, SelectionRequest, SelectionResponse, DiffResponse
from app.parser import parse_pdf
from app.versioning import match_versions, generate_diff
from app.llm import generate_test_cases
from app.nosql import insert_generation, get_generations_by_selection, get_generations_by_node, get_generation_by_id
from app.staleness import check_staleness

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CT-200 QA Generator")

def build_tree_from_db(db_nodes):
    node_dict = {n.id: {
        "logical_node_id": n.logical_node_id, 
        "heading": n.heading, 
        "body_text": n.body_text, 
        "content_hash": n.content_hash, 
        "level": n.level,
        "children": []
    } for n in db_nodes}
    
    tree = []
    for n in db_nodes:
        if n.parent_id:
            node_dict[n.parent_id]["children"].append(node_dict[n.id])
        else:
            tree.append(node_dict[n.id])
    return tree

def insert_tree_to_db(db: Session, doc_version_id: int, tree: list, parent_id: int = None, order_start: int = 0):
    idx = order_start
    for node_dict in tree:
        new_node = Node(
            document_version_id=doc_version_id,
            parent_id=parent_id,
            heading=node_dict["heading"],
            level=node_dict["level"],
            body_text=node_dict["body_text"],
            content_hash=node_dict["content_hash"],
            order_index=idx,
            logical_node_id=node_dict.get("logical_node_id")
        )
        db.add(new_node)
        db.flush()
        insert_tree_to_db(db, doc_version_id, node_dict.get("children", []), new_node.id, 0)
        idx += 1

@app.post("/ingest")
async def ingest(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = f"data/temp_{uuid.uuid4()}.pdf"
    os.makedirs("data", exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(await file.read())
        
    try:
        new_tree = parse_pdf(file_path)
    finally:
        os.remove(file_path)
        
    latest_version = db.query(DocumentVersion).order_by(DocumentVersion.version_number.desc()).first()
    new_version_num = (latest_version.version_number + 1) if latest_version else 1
    
    if latest_version:
        v1_nodes = db.query(Node).filter(Node.document_version_id == latest_version.id).order_by(Node.order_index).all()
        v1_tree = build_tree_from_db(v1_nodes)
        # Apply versioning matching to ensure logical_node_ids match
        # match_versions modifies v2_tree nodes' logical_node_id in-place if there's a fallback match
        match_versions(v1_tree, new_tree)
        
    doc_ver = DocumentVersion(version_number=new_version_num, source_filename=file.filename)
    db.add(doc_ver)
    db.flush()
    
    insert_tree_to_db(db, doc_ver.id, new_tree)
    db.commit()
    
    return {"message": "Ingested successfully", "version": new_version_num}

@app.get("/nodes", response_model=list[NodeResponse])
def get_nodes(version: int = None, db: Session = Depends(get_db)):
    if not version:
        latest = db.query(DocumentVersion).order_by(DocumentVersion.version_number.desc()).first()
        if not latest:
            return []
        version = latest.version_number
        
    doc_ver = db.query(DocumentVersion).filter(DocumentVersion.version_number == version).first()
    if not doc_ver:
        raise HTTPException(status_code=404, detail="Version not found")
        
    top_nodes = db.query(Node).filter(
        Node.document_version_id == doc_ver.id,
        Node.parent_id == None
    ).order_by(Node.order_index).all()
    
    return top_nodes

@app.get("/nodes/{id}", response_model=NodeResponse)
def get_node(id: int, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.id == id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node

@app.get("/search", response_model=list[NodeResponse])
def search_nodes(q: str, db: Session = Depends(get_db)):
    latest = db.query(DocumentVersion).order_by(DocumentVersion.version_number.desc()).first()
    if not latest:
        return []
        
    results = db.query(Node).filter(
        Node.document_version_id == latest.id,
        or_(Node.heading.ilike(f"%{q}%"), Node.body_text.ilike(f"%{q}%"))
    ).all()
    
    return results

@app.get("/nodes/{id}/diff", response_model=DiffResponse)
def get_node_diff(id: int, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.id == id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
        
    # Get the previous version of this node
    doc_ver = db.query(DocumentVersion).filter(DocumentVersion.id == node.document_version_id).first()
    prev_ver = db.query(DocumentVersion).filter(DocumentVersion.version_number == doc_ver.version_number - 1).first()
    
    if not prev_ver:
        return DiffResponse(status="added", diff="", match_confidence="high")
        
    prev_node = db.query(Node).filter(
        Node.document_version_id == prev_ver.id,
        Node.logical_node_id == node.logical_node_id
    ).first()
    
    if not prev_node:
        return DiffResponse(status="added", diff="", match_confidence="high")
        
    if prev_node.content_hash == node.content_hash:
        return DiffResponse(status="unchanged", diff="", match_confidence="high")
        
    diff = generate_diff(prev_node.body_text, node.body_text)
    return DiffResponse(status="changed", diff=diff, match_confidence="high") # In a real implementation we'd track low confidence here if fuzzy matched

@app.post("/selections", response_model=SelectionResponse)
def create_selection(req: SelectionRequest, db: Session = Depends(get_db)):
    nodes = db.query(Node).filter(Node.id.in_(req.node_ids)).all()
    if len(nodes) != len(req.node_ids):
        raise HTTPException(status_code=400, detail="Some nodes not found")
        
    sel = Selection(name=req.name)
    db.add(sel)
    db.flush() # get id
    
    sel.nodes = nodes
    db.commit()
    db.refresh(sel)
    return sel

@app.get("/selections/{id}", response_model=SelectionResponse)
def get_selection(id: int, db: Session = Depends(get_db)):
    sel = db.query(Selection).filter(Selection.id == id).first()
    if not sel:
        raise HTTPException(status_code=404, detail="Selection not found")
    return sel

@app.post("/generate")
def generate_tests(selection_id: int, db: Session = Depends(get_db)):
    sel = db.query(Selection).filter(Selection.id == selection_id).first()
    if not sel:
        raise HTTPException(status_code=404, detail="Selection not found")
        
    combined_text = "\n\n".join([n.heading + "\n" + n.body_text for n in sel.nodes])
    
    llm_res = generate_test_cases(combined_text)
    
    source_hashes = [{"node_id": n.id, "logical_node_id": n.logical_node_id, "content_hash": n.content_hash} for n in sel.nodes]
    
    gen_data = {
        "selection_id": sel.id,
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "source_node_hashes": source_hashes,
        "raw_llm_response": llm_res["raw_response"],
        "parsed_test_cases": llm_res["parsed"],
        "generation_status": llm_res["status"]
    }
    
    gen_id = insert_generation(gen_data)
    gen_data["id"] = gen_id
    
    return gen_data

@app.get("/test-cases")
def get_test_cases(selection_id: int = None, node_id: int = None, db: Session = Depends(get_db)):
    if selection_id:
        gens = get_generations_by_selection(selection_id)
    elif node_id:
        gens = get_generations_by_node(node_id)
    else:
        raise HTTPException(status_code=400, detail="Must provide selection_id or node_id")
        
    results = []
    for g in gens:
        # Check staleness
        staleness_info = check_staleness(db, g)
        
        # We inject the staleness info into the response
        res = dict(g)
        res["staleness"] = staleness_info
        results.append(res)
        
    return results
