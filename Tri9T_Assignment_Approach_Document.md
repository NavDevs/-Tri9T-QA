# Tri9T AI Internship - Assignment Approach Document
**Applicant:** Naveen S
**Role:** AI Intern

## 1. Architectural Overview
For this assignment, I engineered a full-stack, AI-powered Quality Assurance (QA) Engine designed to process medical device manuals and dynamically generate audit-ready test cases. 

The architecture is split into a robust Python backend and a custom-styled, zero-dependency frontend, ensuring maximum performance and maintainability.

* **Backend Framework:** FastAPI (Python)
* **Frontend:** Vanilla HTML, CSS, JavaScript (No heavy frameworks, highly optimized)
* **Database/Storage:** TinyDB (Local JSON-based document store)
* **AI/LLM Provider:** Groq API (Utilizing Llama 3 / Mixtral for ultra-low latency inference)
* **PDF Processing:** PyMuPDF (`fitz`), pdfplumber

## 2. Ingestion & Parsing Strategy
The assignment specified parsing a complex hierarchical document (the CT-200 manual). Instead of basic chunking, I implemented a semantic ingestion pipeline:
* **Text Extraction:** Utilized PyMuPDF to extract raw text, preserving crucial font size and stylistic data.
* **Structural Chunking:** Built a custom parser that reads font sizes (e.g., Size 16.5 for `##` top-level headings, Size 12.9 for `###` sub-headings) to accurately reconstruct the exact hierarchical structure of the document (8 main sections) rather than indiscriminately cutting paragraphs in half.
* **Storage:** The parsed, structured chunks are stored locally in a TinyDB instance (`tri9t.db`), tagging each chunk with its parent section context.

## 3. Search and Retrieval (RAG Pipeline)
To ensure the LLM generates accurate test cases without hallucinating, I implemented a Retrieval-Augmented Generation (RAG) pipeline:
* **Querying:** When a user searches for a feature (e.g., "Overpressure"), the backend utilizes fuzzy matching (via `rapidfuzz`) and keyword tokenization against the TinyDB records.
* **Context Initialization:** The system retrieves the most relevant chunks, including their hierarchical context (ensuring the LLM knows *where* in the manual the information came from).
* **Future Improvement:** While the current lightweight string-matching is highly effective for this specific manual, a production deployment would replace this with dense vector embeddings (e.g., ChromaDB) for deep semantic search.

## 4. LLM Execution & Prompt Engineering
* **Inference:** I utilized the Groq API due to its exceptionally fast inference speeds, which is critical for real-time frontend user experiences.
* **Prompt Strategy:** The prompt strictly binds the LLM to the provided context. The LLM acts as an expert Medical Device QA Engineer, instructed to output structured test cases containing:
  - Test Case ID & Title
  - Preconditions
  - Step-by-step Execution
  - Expected Results (tied directly to the safety/operational parameters in the manual)
  
## 5. UI/UX Design System
Instead of using a generic template, I designed a bespoke **Minimalist Monochrome** frontend aesthetic. 
* **Design Philosophy:** Pure black, pure white, and editorial serif typography. It utilizes 0ms instant-inversion hover states to provide a premium, highly tactile "software terminal" feel.
* **UX Flow:** The dashboard directly mirrors the backend pipeline (Ingest -> Query -> Initialize -> Execute), giving the user visual confirmation at every stage of the RAG process.
