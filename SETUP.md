# AgentAudit Setup Guide

## Prerequisites

AgentAudit requires API keys for the providers used by your tier.

## 1. Configure API Keys

Create a file named `backend/.env.secret` (or modify the existing template) and add your keys.

Lite tier (default) uses Groq + Google + DeepSeek:
```env
GROQ_API_KEY=your_groq_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

Pro tier uses OpenAI + Anthropic + Google:
```env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

Optional if you override `LLM_PROVIDER` elsewhere:

```env
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

## 2. Start AgentAudit

### Backend
```bash
cd backend
# Run the server
uvicorn app.main:app --port 8000 --reload
```

### Frontend (Streamlit)
```bash
# From the project root
streamlit run frontend/streamlit_app.py
```

## 3. Run Your First Audit

1. Open the Streamlit app (usually `http://localhost:8501`)
2. Enter a test API endpoint (e.g., `http://localhost:5001/chat`)
3. Select compliance suites
4. Click "Initiate Audit Sequence"

---

## Troubleshooting

### "Invalid API Key"
- Ensure API Keys are correctly set in `backend/.env.secret`.
- Ensure the backend service has been restarted after changing keys.

### Port conflicts
- Backend: `8000`
- Frontend: `3000`
- Demo Chatbot: `5001`
