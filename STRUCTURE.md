# STRUCTURE.md — Project File Graph

Regenerate this file every time the folder structure actually changes (new,
renamed, or deleted file). This must always reflect what's on disk, not the
plan. Read this before creating or moving any file.

## Planned structure

```
tri9t-ct200/
├── README.md
├── PRD.md
├── TRD.md
├── STRUCTURE.md
├── CONTEXT.md
├── PROGRESS_LOG.md
├── requirements.txt
├── .env.example
├── data/
│   ├── ct200_manual.pdf
│   ├── ct200_manual_v2.pdf
│   └── IMPORTANT_ASSIGNMENT_UPDATE.txt
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app, route registration
│   ├── database.py        # SQLAlchemy engine/session (SQLite)
│   ├── nosql.py            # TinyDB setup for generations
│   ├── models.py           # SQLAlchemy ORM models
│   ├── schemas.py          # Pydantic request/response schemas
│   ├── parser.py           # PDF -> tree (PyMuPDF + pdfplumber)
│   ├── versioning.py       # cross-version node matching + diffing
│   ├── llm.py               # prompt construction, LLM call, validation/retry
│   └── staleness.py        # staleness computation used by retrieval API
├── tests/
│   ├── test_parser.py       # irregularity-targeted unit tests
│   ├── test_versioning.py
│   ├── test_staleness.py
│   └── test_api.py          # end-to-end API tests
└── scripts/
    └── demo_flow.sh          # curl script: ingest v1 -> select -> generate -> ingest v2 -> retrieve -> staleness
```

## Dependency graph (high level)

```
main.py
 ├── database.py ── models.py
 ├── nosql.py
 ├── schemas.py
 ├── parser.py ───────────────┐
 ├── versioning.py ── models.py
 ├── llm.py ── schemas.py     │
 └── staleness.py ── models.py, nosql.py

parser.py produces Node rows consumed by versioning.py and (indirectly)
llm.py / staleness.py, which never re-parse the PDF themselves.
```

## Status legend for CONTEXT.md entries
- `NOT STARTED` — planned, not yet created
- `IN PROGRESS` — created, incomplete or untested
- `DONE` — implemented, tests passing, CONTEXT.md entry matches actual code
