# Technical Requirements Document — CT-200 Manual QA Test Case Generator

## 1. Stack
- **FastAPI + Pydantic** — API layer, request/response validation
- **SQLAlchemy + SQLite** — relational store for document tree, versions, selections
- **TinyDB** (local JSON-backed) — NoSQL store for LLM-generated test cases.
  Justification: the assignment allows a "well-justified JSON store" in place of
  MongoDB; TinyDB lets a reviewer run the project with zero external services
  or Atlas credentials.
- **LLM provider**: Gemini API (key via `GEMINI_API_KEY` env var); design the
  LLM call behind a thin interface so swapping providers is a one-file change.
- **PDF parsing**: PyMuPDF (`fitz`) for text + font metadata, `pdfplumber` for
  table extraction (input files are PDF, per `IMPORTANT_ASSIGNMENT_UPDATE.txt`
  — confirmed present alongside `ct200_manual`/`ct200_manual_v2`).
- **pytest** for unit + API tests.

## 2. Data Model

### SQL (SQLite)

**DocumentVersion**
`id, version_number, ingested_at, source_filename`

**Node**
`id, document_version_id (FK), parent_id (self FK, nullable), heading, level,
body_text, content_hash (sha256), order_index, logical_node_id`

`logical_node_id` is the stable identifier used for cross-version matching
(see §4) — distinct from `id`, which is per-version-row.

**Selection**
`id, name, created_at`

**SelectionNode** (join table — this is what makes selections version-pinned)
`selection_id (FK), node_id (FK)` — `node_id` points at the specific version's
`Node` row, so a selection always resolves to the exact text it was created
against, even after re-ingestion.

### NoSQL (TinyDB / JSON)

**Generation**
```
{
  id, selection_id, generated_at,
  source_node_hashes: [{node_id, logical_node_id, content_hash}],
  raw_llm_response, parsed_test_cases: [...],
  generation_status: "ok" | "malformed" | "retried" | "failed"
}
```

## 3. Parsing Strategy (PDF)
- Extract text spans with font size/weight (PyMuPDF) to infer heading level;
  cross-check against a numbered-heading regex (`^\d+(\.\d+)*\s`) since font
  size alone is unreliable across PDF export tools.
- Extract tables (e.g. General Specifications, Error Codes) via `pdfplumber`
  and attach them as structured content on their parent heading node — never
  drop them.
- **Irregularities to catalog once the actual PDF is inspected** (fill this in
  for real, don't leave it generic): duplicate/repeated heading text at
  different levels, inconsistent numbering, tables spanning a page break,
  footnotes or callout boxes not part of the heading hierarchy, bold non-heading
  text that could be misdetected as a heading.
- Parser must fail loudly (raise with node context, or log a clearly-flagged
  warning attached to the node) rather than silently mis-parenting when a
  pattern doesn't match.

## 4. Version Matching Strategy
- **Primary**: match by `logical_node_id` = normalized heading text + hierarchy
  path (e.g. `3.2.1::cuff-pressure-limits`). Survives body-text edits and minor
  reordering.
- **Fallback**: fuzzy string match (e.g. `rapidfuzz`) against the previous
  version's headings within the same parent, above a similarity threshold —
  flagged as `"match_confidence": "low"` for review rather than silently
  auto-accepted.
- A node is "changed" if `content_hash` differs between versions for the same
  `logical_node_id`.
- **Known failure modes** (state these plainly in the approach doc): a heading
  rename below the fuzzy threshold is misclassified as a brand-new node; a
  section moved to a different parent breaks the hierarchy-path match even if
  its heading text is untouched; two sections swapping headings would be
  cross-matched incorrectly.

## 5. LLM Prompt Design & Structured Output
- Prompt instructs the model to return **only** a JSON array of 3–5 objects:
  `{title, steps: [string], expected_result}`.
- Validate the response against a Pydantic schema on receipt.
- On validation failure: retry once with an explicit corrective follow-up
  ("your last response was not valid JSON matching schema X — return only
  valid JSON, no prose").
- If the retry also fails: set `generation_status = "failed"`, store the raw
  response for debugging, and surface the failure through the retrieval API —
  never fabricate placeholder test cases to paper over a bad LLM response.

## 6. Duplicate Selection Submission Policy
**Chosen policy**: every `POST /generate` creates a new `Generation` record;
generation is *not* idempotent by selection ID. Re-running against unchanged
text is a legitimate action (user wants different phrasing/coverage), and
silent deduplication would hide that choice from the user. All prior
generations for a selection stay retrievable.
*(Alternative considered: idempotent-by-content-hash caching, which trades
away that flexibility for lower LLM cost — worth naming as the rejected
option in the approach doc.)*

## 7. Staleness / Impact Detection
- At retrieval time, recompute the current `content_hash` for every
  `logical_node_id` referenced in a `Generation`'s `source_node_hashes`, and
  compare to the hash stored at generation time.
- Any mismatch → `stale: true`, plus a lightweight diff (e.g. `difflib`
  unified diff) of the affected node's old vs. new body text.
- **Explicit limitation**: this is a text-hash diff — it cannot distinguish a
  cosmetic wording fix from a changed clinical threshold (e.g. "150 mmHg" →
  "160 mmHg"). Both trip the same flag. State this as a deliberate, known
  simplification in the approach doc, not something you claim to have solved.

## 8. API Surface
| Method | Path | Purpose |
|---|---|---|
| POST | `/ingest` | Upload manual PDF, create new `DocumentVersion` |
| GET | `/nodes?version=` | List top-level sections |
| GET | `/nodes/{id}` | Node detail, children, content hash |
| GET | `/search?q=` | Search headings/body text |
| GET | `/nodes/{id}/diff` | Cross-version diff, if changed |
| POST | `/selections` | Create version-pinned selection |
| GET | `/selections/{id}` | Get selection detail |
| POST | `/generate` | Generate test cases for a selection |
| GET | `/test-cases?selection_id=` or `?node_id=` | Retrieve test cases, incl. staleness flag |

## 9. Decision Log (draft — tighten once implementation surfaces real specifics)
1. **Most likely silent-wrong-result risk**: the fuzzy-match fallback in
   version matching — a low-confidence match could silently link two unrelated
   sections. Caught by logging every fallback match's similarity score and
   surfacing low-confidence matches through the diff API instead of
   auto-resolving them.
2. **Simplicity over correctness**: content-hash-based staleness instead of
   semantic diffing — cheap and time-boxed, but in production it would
   false-flag on trivial typo fixes as often as it catches real spec changes,
   causing alert fatigue.
3. **Unhandled input**: a PDF table spanning a page break — the parser treats
   it as two separate fragments attached to two (possibly wrong) nodes rather
   than merging them. This is a documented known gap, not silently papered
   over.
