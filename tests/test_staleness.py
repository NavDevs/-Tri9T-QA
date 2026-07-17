import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, DocumentVersion, Node
from app.staleness import check_staleness

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_staleness_unchanged(db_session):
    v1 = DocumentVersion(version_number=1, source_filename="v1.pdf")
    db_session.add(v1)
    db_session.commit()
    
    node = Node(
        document_version_id=v1.id,
        logical_node_id="1::test",
        body_text="Test Body",
        content_hash="hash1"
    )
    db_session.add(node)
    db_session.commit()
    
    generation = {
        "source_node_hashes": [
            {"node_id": node.id, "logical_node_id": "1::test", "content_hash": "hash1"}
        ]
    }
    
    result = check_staleness(db_session, generation)
    assert not result["is_stale"]
    assert not result["details"][0]["stale"]

def test_staleness_changed(db_session):
    v1 = DocumentVersion(version_number=1, source_filename="v1.pdf")
    db_session.add(v1)
    db_session.commit()
    
    node1 = Node(
        document_version_id=v1.id,
        logical_node_id="1::test",
        body_text="Test Body",
        content_hash="hash1"
    )
    db_session.add(node1)
    db_session.commit()
    
    # New version where body text changed
    v2 = DocumentVersion(version_number=2, source_filename="v2.pdf")
    db_session.add(v2)
    db_session.commit()
    
    node2 = Node(
        document_version_id=v2.id,
        logical_node_id="1::test",
        body_text="Test Body Updated",
        content_hash="hash2" # different hash
    )
    db_session.add(node2)
    db_session.commit()
    
    generation = {
        "source_node_hashes": [
            {"node_id": node1.id, "logical_node_id": "1::test", "content_hash": "hash1"}
        ]
    }
    
    result = check_staleness(db_session, generation)
    assert result["is_stale"]
    assert result["details"][0]["stale"]
    assert "+Test Body Updated" in result["details"][0]["diff"]
    assert "-Test Body" in result["details"][0]["diff"]
