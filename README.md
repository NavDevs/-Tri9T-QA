# Tri9T AI QA Engine

**Live Demo:** [https://tri9t-qa.onrender.com/](https://tri9t-qa.onrender.com/)

An AI-powered Quality Assurance (QA) Engine designed to process complex medical device manuals and dynamically generate audit-ready test cases. Built for the AffineSurge Internship Assignment.

## 🚀 Overview
The Tri9T QA Engine automates the software testing lifecycle for strict regulatory environments. It parses hierarchical requirement specifications (PDFs), vectorizes them for semantic search, and dynamically generates comprehensive test cases using Retrieval-Augmented Generation (RAG).

## 🛠️ Tech Stack
* **Backend:** FastAPI (Python)
* **Frontend:** Vanilla HTML, CSS, JavaScript (Zero dependencies, custom "Minimalist Monochrome" design system)
* **AI / LLM:** Groq API (Llama 3 / Mixtral) for ultra-low latency inference
* **Storage:** TinyDB (Local JSON document store) & RapidFuzz for fuzzy search
* **PDF Parsing:** PyMuPDF (`fitz`), pdfplumber

## ✨ Core Features
1. **Intelligent Ingestion:** Parses complex PDFs not by indiscriminately cutting text, but by reading font sizes and styles to reconstruct the exact structural hierarchy of the manual.
2. **Contextual Search (RAG):** Users can query the local database to isolate specific nodes (e.g., "Overpressure Alarms") and lock them in as context.
3. **Dynamic Test Generation:** Executes a strictly bound LLM prompt against the Groq API to output structured, audit-ready QA Test Cases (Preconditions, Steps, Expected Results).
4. **Staleness Auditing:** Detects if the underlying PDF manual has been altered since the test cases were generated, instantly flagging outdated tests.

## 💻 Local Installation

**1. Clone the repository**
```bash
git clone https://github.com/NavDevs/-Tri9T-QA.git
cd -Tri9T-QA
```

**2. Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set Environment Variables**
Create a `.env` file in the root directory and add your Groq API key:
```env
GROQ_API_KEY=your_api_key_here
```

**5. Run the Application**
```bash
uvicorn app.main:app --reload
```
The application will be available at `http://127.0.0.1:8000/`.

## ☁️ Deployment
This application is fully configured for seamless 1-click deployment on [Render](https://render.com/) using the included `render.yaml` infrastructure-as-code file.