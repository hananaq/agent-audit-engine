from typing import List, Literal
from dataclasses import dataclass

Severity = Literal["low", "med", "high", "critical"]
Expected = Literal["REFUSE", "SANITIZE", "ASK_CLARIFY", "CITE_CONTEXT_ONLY", "ALLOW"]

@dataclass
class AttackSpec:
    id: str
    category: str
    suite: str
    severity: Severity
    expected: Expected
    prompt: str
    tags: List[str]
