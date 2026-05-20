# GreenPack EPR AI Service

AI-powered backend service for plastic EPR declaration management, ERP reconciliation, and compliance Q&A using Retrieval-Augmented Generation (RAG).

---

# Features

## 1. Submit Monthly EPR Declarations
- Producers can submit plastic declaration data
- Validation prevents negative quantities
- Unique record IDs are generated automatically

## 2. ERP Reconciliation Engine
- Compares submitted declaration quantities against ERP procurement records
- Detects mismatches above 5%
- Generates AI-powered reconciliation summaries

## 3. RAG-based Compliance Assistant
- Semantic document retrieval using FAISS
- Sentence-transformer embeddings
- Grounded answers using retrieved context
- Hallucination prevention support
- Source citation support

---

# Tech Stack

- FastAPI
- Python
- Groq API (Llama 3.1)
- Sentence Transformers
- FAISS Vector Search
- Pandas
- NumPy


---

# Project Structure

```text
greenpack-epr-ai/
│
├── main.py                  # Main FastAPI backend application
├── cache_manager.py         # Local cache and hallucination logging
├── cache_logs.json          # Stored RAG interaction logs
│
├── requirements.txt         # Python dependencies
├── README.md                # Project documentation
├── sample_curl.txt          # API testing commands
├── .env                     # Environment variables
│
├── data/
│   ├── erp_feed.csv         # ERP procurement dataset
│   │
│   └── rag_docs/
│       ├── doc1.txt         # EPR information
│       ├── doc2.txt         # Monthly declaration information
│       └── doc3.txt         # ERP reconciliation information

```

---

# Cache and Observability

The system stores all RAG interactions locally for observability and audit tracking.

Each interaction logs:
- user question
- generated answer
- retrieved source
- hallucination status
- timestamp

Logs are stored in:

```text
cache_logs.json

{
    "question": "What is Extended Producer Responsibility?",
    "answer": "Extended Producer Responsibility requires plastic producers to manage plastic waste generated from their products.",
    "source": "doc1.txt",
    "hallucination": false,
    "timestamp": "2026-05-20 15:45:12"
}

Hallucination attempts are also tracked:

{
    "question": "Who is the CEO of GreenPack?",
    "answer": "I do not know based on the provided documents.",
    "source": null,
    "hallucination": true,
    "timestamp": "2026-05-20 15:48:33"
}
