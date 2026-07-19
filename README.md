# 🤖 AI Recruitment Copilot | LangGraph • LangChain • FastAPI • RAG • FAISS • Streamlit

An **Agentic AI-powered Recruitment Assistant** that automates resume screening using **LangGraph**, **LangChain**, **FastAPI**, **FAISS**, **RAG**, and **Streamlit**.

The application analyzes resumes against job descriptions, calculates candidate-job compatibility, identifies skill gaps, generates candidate summaries, and creates personalized interview questions.

---

## 🚀 Features

### ✅ Resume Analysis
- Upload Resume PDF
- Extract candidate information
- Identify skills
- Extract education details
- Calculate years of experience
- Detect projects

### ✅ Job Description Analysis
- Upload Job Description PDF
- Extract required skills
- Extract preferred skills
- Identify responsibilities
- Extract minimum experience

### ✅ AI Matching Engine
- Match resume against job description
- Calculate compatibility score
- Identify matched skills
- Detect missing skills
- Verify experience requirements
- Generate hiring recommendation

### ✅ Interview Question Generator
- Generates role-specific interview questions
- Questions are based on:
  - Resume
  - Job Description
  - Missing Skills
  - Candidate Experience

### ✅ RAG Pipeline
- PDF Processing
- Text Chunking
- Vector Embeddings
- FAISS Vector Database
- Semantic Retrieval

---

# 🏗️ Project Architecture

```
                   Resume PDF
                        │
                        ▼
               Resume Extraction Agent
                        │
                        ▼
               Structured Resume Data
                        │
                        │
Job Description PDF ────┘
        │
        ▼
 Job Description Agent
        │
        ▼
 Structured JD Data
        │
        ▼
 Matching Agent
        │
        ▼
 Candidate Summary
 Match Score
 Skill Gap Analysis
 Recommendation
        │
        ▼
 Interview Agent
        │
        ▼
 Interview Questions
```

---

# 🧠 Agentic Workflow

```
User Uploads Resume + JD
            │
            ▼
Resume Agent
            │
            ▼
JD Agent
            │
            ▼
Matching Agent
            │
            ▼
Interview Agent
            │
            ▼
Results displayed in Streamlit
```

---

# 📂 Project Structure

```
AIRecruitmentCopilot/
│
├── agents/
│   ├── resume_agent.py
│   ├── jd_agent.py
│   ├── matching_agent.py
│   └── interview_agent.py
│
├── backend/
│   ├── main.py
│   ├── workflow.py
│   └── llm.py
│
├── frontend/
│   └── app.py
│
├── rag/
│   ├── vector_store.py
│   └── retriever.py
│
├── utils/
│   └── pdf_loader.py
│
├── models/
│   └── schemas.py
│
├── data/
│
├── .env
├── requirements.txt
└── README.md
```

---

# ⚙️ Tech Stack

- Python
- FastAPI
- Streamlit
- LangChain
- LangGraph
- FAISS
- Retrieval-Augmented Generation (RAG)
- Sentence Transformers
- Groq Llama 3.3 70B (LLM)
- PyMuPDF
- Pydantic

---

# 🔄 RAG Pipeline

```
PDF
 │
 ▼
Text Extraction
 │
 ▼
Chunking
 │
 ▼
Embeddings
 │
 ▼
FAISS Vector Store
 │
 ▼
Similarity Search
 │
 ▼
Relevant Context
 │
 ▼
LLM Response
```

---

# 🧠 LangGraph Workflow

The application uses LangGraph to orchestrate multiple AI agents.

### Resume Agent
Extracts:
- Candidate Name
- Skills
- Education
- Experience
- Projects

### JD Agent
Extracts:
- Required Skills
- Preferred Skills
- Responsibilities
- Minimum Experience

### Matching Agent
Calculates:
- Match Score
- Matched Skills
- Missing Skills
- Experience Match
- Candidate Recommendation

### Interview Agent
Generates technical interview questions tailored to the candidate profile.

---

# ▶️ Installation

Clone the repository

```bash
git clone https://github.com/yourusername/AIRecruitmentCopilot.git

cd AIRecruitmentCopilot
```

Install dependencies

```bash
uv sync
```

or

```bash
pip install -r requirements.txt
```

Create a `.env` file

```env
GROQ_API_KEY=your_api_key
GOOGLE_API_KEY=your_google_api_key
```

---

# ▶️ Run FastAPI

```bash
uv run uvicorn backend.main:app --reload
```

---

# ▶️ Run Streamlit

```bash
streamlit run frontend/app.py
```

---

# 📸 Demo

### Upload

- Resume PDF
- Job Description PDF

### AI Generates

- Resume Summary
- Job Description Analysis
- Match Score
- Skill Gap Analysis
- Hiring Recommendation
- Interview Questions

---

# 💡 Future Enhancements

- Multi-candidate ranking
- ATS Resume Parsing
- Resume Recommendation Engine
- Knowledge Graph Integration
- HR Dashboard
- Authentication
- PostgreSQL Integration
- Docker Deployment
- Cloud Deployment (AWS/Azure)

---

# 👩‍💻 Author

**Sakshi Maurya**

B.Tech – Artificial Intelligence & Data Science

Interested in:
- Agentic AI
- Large Language Models
- Retrieval-Augmented Generation
- AI Automation
- Backend Engineering

---
