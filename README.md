# AgentAudit Engine

AgentAudit is a lightweight adversarial testing tool for AI agents. It runs automated probes against a target endpoint and scores responses for safety, hallucination risk, and compliance. A key feature is the multi-model Court of Judges, which cross-checks results for higher reliability.

## Tech Stack
- Python 3.11
- FastAPI (backend API)
- Streamlit (frontend UI)
- LangChain + provider SDKs (LLM judging)
- Pydantic (validation and config)
- httpx (HTTP client)

## Court of Judges (How It Works)
AgentAudit uses a multi-model "court of judges" to score each response:
- Two primary judges from different model families evaluate the response in parallel.
- If they agree, the consensus verdict is returned.
- If they disagree or the case is borderline, a third judge (Judge C) is invoked to break ties or refine the reasoning.
- If both primary judges return a FAIL verdict, the final outcome stays FAIL (Judge C is only used to refine scores/reasoning).

## How To Run

### 1) Configure API Keys
Create `backend/.env.secret` and add the keys for your tier.

Lite tier (default):
```env
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

Pro tier:
```env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

### 2) Start Backend
```bash
cd backend
uvicorn app.main:app --port 8000 --reload
```

### 3) Start Frontend
```bash
streamlit run frontend/streamlit_app.py
```

### 4) Run an Audit
- Open the Streamlit app (usually `http://localhost:8501`)
- Enter a target endpoint (for example: `http://localhost:5001/chat`)
- Select suites and start the audit

## Target Requirements (Current Version)
- The target URL must be reachable without authentication.
- This version does not support tokens or auth headers yet (planned for a future update).
- This project has only been tested on local chatbots so far.

## Feedback
If you run into issues or think of new features, please open an issue or leave a comment. Suggestions are welcome.
