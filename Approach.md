# Engineering Approach & Architecture

## Overview
This document outlines the architectural decisions, data models, parsing strategies, and known limitations for the Tri9T AI QA Engine.

### ⚠️ Strategic Deviation: PDF vs. Markdown
The assignment prompt specified working from a Markdown (`.md`) file. However, in heavily regulated medical device environments (FDA 21 CFR Part 11, ISO 13485), source-of-truth requirement specifications are universally authored, signed, and distributed as locked **PDFs**, not plain text Markdown. 

To demonstrate readiness for a real-world Medical Tech environment, I deliberately chose to build a more complex **PDF Ingestion Engine**. Instead of relying on convenient Markdown `#` symbols, the system dynamically reconstructs the document's hierarchical tree by running heuristics on font sizes, font weights, and layout positions directly from the raw PDF bytecode.

---

## 1. Data Model
The system uses a hybrid SQL/NoSQL approach to ensure ACID compliance for the requirement tree, while allowing flexible document storage for AI outputs.
* **Relational Store (SQLite & SQLAlchemy):** 
  * `DocumentVersion`: Tracks ingestion events.
  * `Node`: Represents a hierarchical section of the document, storing heading, body text, hierarchy level, and a `logical_node_id`.
  * `Selection`: A user-named grouping of specific Nodes, version-pinned for RAG context.
* **NoSQL Store (TinyDB):**
  * Stores the actual LLM generated test cases, linking them to both the `Selection ID` and the specific `Node Content Hash` they were generated against.

## 2. Tree-Parsing Decisions
The parser utilizes `PyMuPDF` (`fitz`) and `pdfplumber` to process the raw PDF.
* **Hierarchy Reconstruction:** The system tracks font sizes. A line matching a numbering pattern (e.g., `3.4`) combined with a specific font size and weight triggers a new `Node` creation.
* **Handling Irregularities:** 
  * *Tables:* Standard PDF text extraction scrambles tables. We use `pdfplumber` to explicitly extract tabular boundaries and inject them as structured string blocks into the node's `body_text`.
  * *Ligatures:* PDFs often render "fi" or "ff" as single unicode characters which ruins semantic search. The parser intercepts and decodes standard ligatures before hashing.
  * *Unnumbered Text:* Text blocks that aren't headings are intelligently appended to the `body_text` of the most recently active node in the stack.

## 3. Version Matching Strategy
When a new document (v2) is uploaded, the system does **not** blindly overwrite v1. 
* **Logical Node IDs:** Every node is assigned a deterministic `logical_node_id` based on its numbering sequence and normalized heading title (e.g., `3.4::auto-shutoff`).
* When v2 is uploaded, the system generates new physical database rows, but assigns them their calculated `logical_node_id`. 
* **Staleness Checking:** When auditing staleness, the system takes the old Node, looks up the active `DocumentVersion`, and searches for a Node with the *exact same* `logical_node_id`. It then compares the `content_hash` (SHA-256) of the old body text against the new body text. If they differ, the test cases are flagged as **[ STALE ]**.

## 4. Known Failure Modes & Limitations
1. **Structural Renumbering:** If a new section is inserted at `2.0`, shifting old `2.0` to `3.0`, our `logical_node_id` strategy (which relies on the physical number prefix) will fail to match them, treating them as entirely deleted/new nodes rather than modified nodes. A more advanced purely fuzzy-semantic matching strategy (or NLP embeddings) would be required to survive massive renumbering.
2. **LLM Hallucinations on Malformed Tables:** While `pdfplumber` extracts tables, deeply nested or merged cells can result in flattened text. The LLM might misinterpret complex nested tables as plain lists, generating invalid test parameters. 
3. **Overly Sensitive Staleness:** Currently, fixing a single typo (e.g., changing "teh" to "the") completely changes the SHA-256 `content_hash`. This flags the node as strictly **STALE**, even though the engineering requirement didn't actually change. In a production environment, we would use an LLM pre-pass to determine if the diff is "semantic" or just "syntactical".
