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
