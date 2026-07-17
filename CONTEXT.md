# CONTEXT.md — Living Per-File Reference

**Rule**: update this file's relevant entry in the SAME commit as any change to
the file it describes. Before writing code that touches an existing file, read
that file's entry here first — don't work from memory of what you intended it
to contain.

Each entry format:
```
### <path>
**Status**: NOT STARTED | IN PROGRESS | DONE
**Purpose**: one paragraph — what this file does and why it exists
**Public interface**: real function/class/endpoint signatures currently in the file
**Depends on**: files/modules it imports or calls
**Depended on by**: files/modules that import or call it
**Known gaps**: anything intentionally incomplete or simplified
```

---

### app/main.py
**Status**: NOT STARTED
**Purpose**: FastAPI app instance and route registration for all API endpoints
in TRD §8.
**Public interface**: TBD
**Depends on**: database.py, nosql.py, schemas.py, parser.py, versioning.py, llm.py, staleness.py
**Depended on by**: —
**Known gaps**: —

### app/database.py
**Status**: DONE
**Purpose**: SQLAlchemy engine + session setup for the SQLite store.
**Public interface**: `engine`, `SessionLocal`, `Base`, `get_db()`
**Depends on**: —
**Depended on by**: models.py, main.py
**Known gaps**: —

### app/nosql.py
**Status**: NOT STARTED
**Purpose**: TinyDB setup/access for storing LLM-generated test cases.
**Public interface**: TBD
**Depends on**: —
**Depended on by**: llm.py, staleness.py, main.py
**Known gaps**: —

### app/models.py
**Status**: DONE
**Purpose**: SQLAlchemy ORM models — DocumentVersion, Node, Selection,
SelectionNode (see TRD §2).
**Public interface**: `DocumentVersion`, `Node`, `Selection`, `selection_node`
**Depends on**: database.py
**Depended on by**: parser.py, versioning.py, staleness.py, main.py
**Known gaps**: —

### app/schemas.py
**Status**: NOT STARTED
**Purpose**: Pydantic request/response models for the API, plus the LLM
structured-output schema.
**Public interface**: TBD
**Depends on**: —
**Depended on by**: main.py, llm.py
**Known gaps**: —

### app/parser.py
**Status**: IN PROGRESS
**Purpose**: Parses the CT-200 manual PDF into a Node tree (see TRD §3).
**Public interface**: TBD
**Depends on**: models.py
**Depended on by**: main.py
**Known gaps**: Must handle multi-font span breaks (hyphens), out-of-order headings (3.4 before 3.3), size-11 bold headings (2.1.1.1), and cross-page paragraphs.

### app/versioning.py
**Status**: NOT STARTED
**Purpose**: Cross-version node matching (logical_node_id + fuzzy fallback)
and diff generation (see TRD §4).
**Public interface**: TBD
**Depends on**: models.py
**Depended on by**: main.py, staleness.py
**Known gaps**: known failure modes from TRD §4 apply here directly.

### app/llm.py
**Status**: NOT STARTED
**Purpose**: Builds the prompt from a selection's reconstructed text, calls the
LLM, validates/retries on malformed output (see TRD §5).
**Public interface**: TBD
**Depends on**: schemas.py, nosql.py
**Depended on by**: main.py
**Known gaps**: —

### app/staleness.py
**Status**: NOT STARTED
**Purpose**: Recomputes current content hashes for a generation's source
nodes and flags staleness + diff at retrieval time (see TRD §7).
**Public interface**: TBD
**Depends on**: models.py, nosql.py
**Depended on by**: main.py
**Known gaps**: text-hash-only limitation from TRD §7 applies.

### tests/test_parser.py
**Status**: IN PROGRESS
**Purpose**: Unit tests targeting the ≥3 real irregularities found in the
manual PDF.
**Public interface**: —
**Depends on**: app/parser.py
**Depended on by**: —
**Known gaps**: —

### tests/test_versioning.py
**Status**: NOT STARTED
**Purpose**: Tests for node matching across v1/v2, including a known
failure-mode case.
**Depends on**: app/versioning.py

### tests/test_staleness.py
**Status**: NOT STARTED
**Purpose**: Tests that a changed node correctly flags its generations stale
and an unchanged node does not.
**Depends on**: app/staleness.py

### tests/test_api.py
**Status**: NOT STARTED
**Purpose**: End-to-end test of ingest → select → generate → re-ingest →
retrieve → staleness flag.
**Depends on**: app/main.py

### scripts/demo_flow.sh
**Status**: NOT STARTED
**Purpose**: curl script demonstrating the full versioning + staleness flow
end-to-end, per assignment's "must demonstrate, not just happy-path CRUD."
**Depends on**: running app/main.py
