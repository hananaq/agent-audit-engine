import httpx
from typing import Optional, Dict, Any

class AgentAuditClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "http://localhost:8000/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url)

    def trigger_audit(self, target_url: str, mode: str = "chatbot") -> Dict[str, Any]:
        """
        Triggers an audit for the given target URL.
        """
        response = self.client.post("/audit", json={
            "target_url": target_url, 
            "mode": mode,
            "api_key": self.api_key
        })
        response.raise_for_status()
        return response.json()

    def get_report(self, audit_id: str) -> Dict[str, Any]:
        """
        Retrieves the report for a specific audit.
        """
        response = self.client.get(f"/report/{audit_id}")
        response.raise_for_status()
        return response.json()
