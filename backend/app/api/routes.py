import asyncio
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from app.engine.red_team import RedTeam
from app.engine.judge import Judge, RUBRIC_VERSION
from app.core.exceptions import RateLimitError
from app.core.config import settings
from app.core.logger import log_audit_event

router = APIRouter()

class AuditRequest(BaseModel):
    # User can provide EITHER a target_url OR a system_prompt
    target_url: Optional[str] = None
    system_prompt: Optional[str] = None
    mode: str = "chatbot" # chatbot or rag
    suites: List[str] = Field(default_factory=lambda: ["default"]) # default, gdpr, hipaa, eu_ai_act
    api_key: Optional[str] = None

class AuditResponse(BaseModel):
    audit_id: str
    status: str
    results: List[dict] = Field(default_factory=list)
    rate_limited: bool = False
    rate_limit_message: Optional[str] = None
    error_message: Optional[str] = None

@router.post("/audit", response_model=AuditResponse)
async def trigger_audit(request: AuditRequest):
    if not request.target_url and not request.system_prompt:
        raise HTTPException(status_code=400, detail="Must provide either target_url or system_prompt")

    request_id = str(uuid.uuid4())
    log_audit_event(request_id, "Audit Request Received", {"mode": request.mode, "suites": request.suites})

    # 1. Initialize RedTeam with target config
    red_team = RedTeam(mode=request.mode)
    
    # 2. Initialize Judge
    judge = Judge()
    
    # 3. Generate Attacks (Standard, Security, Hallucination)
    attacks = red_team.generate_attacks(suites=request.suites)
    
    results = []
    total_attacks = len(attacks)
    had_judge_errors = False
    log_audit_event(request_id, "Audit Start", {"total_attacks": total_attacks})
    
    for i, attack_data in enumerate(attacks):
        if settings.THROTTLE_DELAY > 0:
            await asyncio.sleep(settings.THROTTLE_DELAY)
            
        attack = attack_data["prompt"]
        category = attack_data["category"]
        
        log_audit_event(
            request_id,
            "Attack Start",
            {"index": i + 1, "total": total_attacks, "category": category, "attack_preview": attack[:50]},
        )
        # Step A & B: Send Attack
        if request.target_url:
            response_text = await red_team.send_request_to_url(request.target_url, attack)
        else:
            response_text = await red_team.run_ephemeral_agent(request.system_prompt, attack)
            
        # Step C: Judge Response
        log_audit_event(request_id, "Judge Start", {"index": i + 1, "total": total_attacks, "category": category})
        
        # Check for connectivity errors before judging
        if response_text.startswith("Error connecting to agent:"):
            log_audit_event(request_id, "Audit Failed", {"error": response_text})
            return {
                "audit_id": request_id,
                "status": "failed",
                "results": results,
                "rate_limited": False,
                "error_message": response_text,
            }

        try:
            score_data = await judge.evaluate(
                attack, response_text, attack_metadata=attack_data, tier=settings.TIER, request_id=request_id
            )
            results.append({
                "attack": attack,
                "category": category,
                "response": response_text,
                "metrics": score_data
            })
        except RateLimitError as e:
            log_audit_event(request_id, "Rate Limit Hit", {"error": str(e)})
            return {
                "audit_id": request_id,
                "status": "partial_completed",
                "results": results,
                "rate_limited": True,
                "rate_limit_message": str(e)
            }
        except Exception as e:
            log_audit_event(request_id, "Audit Failed", {"error": str(e)})
            had_judge_errors = True
            results.append({
                "attack": attack,
                "category": category,
                "response": response_text,
                "metrics": {
                    "verdict": "FAIL",
                    "safety_score": 0,
                    "hallucination_score": -1,
                    "tone_score": 0,
                    "violations": [],
                    "evidence": [],
                    "reason": f"Judge error: {str(e)}",
                    "is_consensus": False,
                    "rubric_version": RUBRIC_VERSION,
                },
            })
    
    log_audit_event(request_id, "Audit Completed", {"total_attacks": total_attacks})
        
    return {
        "audit_id": request_id,
        "status": "completed_with_errors" if had_judge_errors else "completed",
        "results": results
    }

# @router.get("/report/{audit_id}")
# async def get_report(audit_id: str):
#     return {"audit_id": audit_id, "status": "completed", "score": 98.5}
