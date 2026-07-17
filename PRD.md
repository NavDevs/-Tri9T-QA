# Product Requirements Document — CT-200 Manual QA Test Case Generator

## 1. Overview
A backend system that ingests versioned copies of the CardioTrack CT-200 Home
Blood Pressure Monitor manual (PDF), converts each into a browsable hierarchical
tree, tracks what changed between versions, lets a user select sections and
generate LLM-powered QA test-case ideas from them, and flags previously
generated test cases as stale when the underlying document text changes.

## 2. Problem Statement
Manual QA test-case authoring is slow, and traceability between a test case and
the exact spec text it came from is easily lost when the spec gets revised — a
serious risk in regulated medical device software, where a missed or outdated
test case can mean patient harm. This system automates test-case ideation while
preserving auditable, version-pinned traceability.

## 3. Target User
A QA engineer working against a versioned device manual. For this assignment
specifically: the internship reviewer, evaluating correctness of the
versioning, traceability, and staleness-detection logic above all else.

## 4. Core Capabilities (Functional Requirements)

**FR1 — Ingestion & Structuring**
- Parse the CT-200 manual PDF into a hierarchical tree.
- Persist heading, level, body text, parent/child relationships, and a content
  hash per node.
- Correctly handle every structural irregularity actually present in the PDF
  (see TRD §3) — no silent drops, mis-parenting, or merges.

**FR2 — Document Versioning**
- Re-ingest a modified manual as a new version without destroying the prior
  version.
- Recognize semantically-unchanged nodes across versions as the same logical
  node (not duplicated); flag nodes whose body text changed.

**FR3 — Browse API**
- List top-level sections (version param, defaults to latest).
- Get a node by ID with children, full text, and content hash.
- Search/filter across headings or body text.
- Given a node ID, report whether it changed across versions, with a
  lightweight diff summary.

**FR4 — Selection API**
- Create a named, version-pinned selection (a set of node+version pairs).
- Old selections must resolve to the exact original text even after the
  document is re-ingested.

**FR5 — LLM Generation API**
- Given a selection, reconstruct the relevant text, prompt an LLM, and generate
  3–5 QA test-case ideas.
- Validate LLM output against a defined schema; have an explicit, defensible
  policy for malformed/incomplete responses.
- Store generated output linked to the selection and the exact node content it
  came from, surviving later re-versioning.
- Have an explicit, defensible policy for duplicate submission of the same
  selection.

**FR6 — Staleness / Impact Detection**
- At retrieval time, tell the user whether a previously generated test case
  still reflects the current document.
- Be explicit about the approach's limits (e.g., a wording tweak vs. a changed
  safety threshold currently trip the same flag).

**FR7 — Retrieval API**
- Fetch previously generated test cases by selection ID or node ID.
- The staleness flag from FR6 must be visible in this response, not just
  computed internally.

## 5. Non-Goals (Explicitly Out of Scope)
- Auth / user accounts
- A generic parser for arbitrary PDFs or Markdown documents
- Auto-regeneration of stale test cases
- A UI (curl/Postman/script demo is sufficient)

## 6. Success Criteria
- End-to-end flow is demoable: ingest v1 → create selection → generate test
  cases → ingest v2 → retrieve → see staleness flag and diff.
- At least 3 unit tests target specific irregularities found in the *actual*
  manual PDF (not hypothetical ones).
- The approach doc's decision log answers reflect real reasoning about this
  specific system, not generic best practices.
