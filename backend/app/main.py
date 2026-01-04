from fastapi import FastAPI
from app.api.routes import router as api_router

from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(title="AgentAudit Engine", version="0.1.0")

allow_origins = settings.CORS_ALLOW_ORIGINS
allow_credentials = False if "*" in allow_origins else True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def health_check():
    return {
        "status": "ok", 
        "service": "AgentAudit Engine",
        "tier": settings.TIER,
        "llm_provider": settings.LLM_PROVIDER
    }
