# Progress Log

This log tracks the implementation steps, verified actions, and deviations from the TRD.

## Initial Setup
- **Attempted**: Initialize Git repository, create virtual environment, set up `requirements.txt`.
- **Verified**: N/A
- **Deviations**: None.

## Step 1: Database and Models
- **Attempted**: Created `app/database.py` with SQLite configuration and `app/models.py` with SQLAlchemy models matching TRD §2 (`DocumentVersion`, `Node`, `Selection`, `selection_node`).
- **Verified**: Confirmed models syntactically valid (waiting for pip install to verify DB creation).
- **Deviations**: None.

## Step 2: PDF Parsing and Testing
- **Attempted**: Created `app/parser.py` using `PyMuPDF` and `pdfplumber` to extract structured text and tables. Wrote `tests/test_parser.py` targeting ligatures, split words (hyphens), inconsistent font sizing, out-of-order numbering, and cross-page spans.
- **Verified**: `pytest tests/test_parser.py` passes completely.
- **Deviations**: Replaced pure `level` detection based on font size with regex heading detection `^\d+(?:\.\d+)*`, because the 2.1.1.1 heading uses size 11.0 (same as body text), making font-size alone unreliable as requested in the assignment context.

## Step 3: TinyDB Setup
- **Attempted**: Created `app/nosql.py` to handle TinyDB setup. Exported helper functions for inserting and retrieving generations by selection or node.
- **Verified**: Syntax checked via flake8 / manual review.
- **Deviations**: None.

## Step 4: Versioning
- **Attempted**: Installed `rapidfuzz` and updated `requirements.txt`. Created `app/versioning.py` logic to match nodes across versions using `logical_node_id` primary and fuzzy match fallback, and computing diffs. Created `tests/test_versioning.py` to cover matched, unchanged, changed with low confidence fallback, and added nodes.
- **Verified**: `pytest tests/test_versioning.py` passes completely.
- **Deviations**: None.

## Step 5: Schemas and LLM Integration
- **Attempted**: Created `app/schemas.py` for API requests/responses and LLM output parsing. Created `app/llm.py` with `generate_test_cases` containing the prompt and fallback retry logic (as specified in TRD §5) using `google-genai`.
- **Verified**: Confirmed syntax correctness via manual module import.
- **Deviations**: None.

## Step 6: Staleness Detection
- **Attempted**: Created `app/staleness.py` to compare source node hashes from generations against the latest document version. Included generation of unified diffs on modification. Created `tests/test_staleness.py` with mocked DB sessions to test unchanged and changed scenarios.
- **Verified**: `pytest tests/test_staleness.py` passes completely.
- **Deviations**: Noted the text-hash-only limitation directly in `app/staleness.py` docstring as requested by TRD §7.

## Step 7: API Endpoints (main.py)
- **Attempted**: Installed `python-multipart` to support file uploads. Created `app/main.py` using FastAPI to wire all endpoints (`/ingest`, `/nodes`, `/search`, `/nodes/{id}/diff`, `/selections`, `/generate`, `/test-cases`) integrating all previous modules as specified in TRD §8.
- **Verified**: Confirmed syntax correctness via manual module import.
- **Deviations**: None.

## Step 8: E2E Test
- **Attempted**: Created `e2e_test.py` utilizing `fastapi.testclient.TestClient` to test the complete lifecycle: ingest v1 -> create selection -> generate test cases -> ingest v2 -> detect staleness -> get diff. Generated `walkthrough.md` documenting this flow.
- **Verified**: E2E script ran successfully and generated the walkthrough document as requested.
- **Deviations**: LLM call was mocked in the test script to prevent dependency on actual API key during automated test runs.
