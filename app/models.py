from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    version_number = Column(Integer, unique=True, index=True)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    source_filename = Column(String)

    nodes = relationship("Node", back_populates="document_version")

class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    document_version_id = Column(Integer, ForeignKey("document_versions.id"))
    parent_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)
    heading = Column(String)
    level = Column(Integer)
    body_text = Column(String)
    content_hash = Column(String)
    order_index = Column(Integer)
    logical_node_id = Column(String, index=True)

    document_version = relationship("DocumentVersion", back_populates="nodes")
    parent = relationship("Node", remote_side=[id], back_populates="children")
    children = relationship("Node", back_populates="parent")

selection_node = Table(
    "selection_node",
    Base.metadata,
    Column("selection_id", Integer, ForeignKey("selections.id"), primary_key=True),
    Column("node_id", Integer, ForeignKey("nodes.id"), primary_key=True)
)

class Selection(Base):
    __tablename__ = "selections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    nodes = relationship("Node", secondary=selection_node)
