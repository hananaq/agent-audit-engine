import random
import asyncio
from typing import List, Dict, Optional
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm_factory import LLMFactory
from app.engine.probes.models import AttackSpec
from app.engine.probes.library import PROBE_LIBRARY
from app.engine.probes.mutator import ProbeMutator

class RedTeam:
    def __init__(self, mode: str = "chatbot"):
        self.mode = mode
        # Use factory to get the configured LLM
        self.llm = LLMFactory.create_llm(temperature=0.7)

    def generate_attacks(self, suites: List[str] = ["default"]) -> List[dict]:
        all_attacks: List[AttackSpec] = []

        # ---- 1. Select Categories ----
        selected_categories = []
        if "default" in suites or "quick" in suites or "adversarial_extended" in suites:
            selected_categories += [
                "Prompt Injection & Jailbreaks",
                "Security & Hygiene",
                "Hallucination & Factual Grounding",
                "Tone, Toxicity & Bias",
                "Logic & Consistency",
            ]

        if "dos" in suites: selected_categories.append("Model DoS & Cost Attacks")
        if "agent_security" in suites: selected_categories.append("Tool & Action Hijacking")
        if "gdpr" in suites: selected_categories.append("GDPR Compliance")
        if "hipaa" in suites: selected_categories.append("HIPAA Compliance")
        if "eu_ai_act" in suites: selected_categories.append("EU AI Act")
        if self.mode == "rag": selected_categories.append("RAG Security")

        # ---- 2. Expand Variants & Filter ----
        VARIANT_CATS = {"Prompt Injection & Jailbreaks", "RAG Security"}

        for cat in selected_categories:
            for spec in PROBE_LIBRARY.get(cat, []):
                if cat in VARIANT_CATS:
                    # Use the restored ProbeMutator
                    variants = ProbeMutator.with_jailbreak_variants(spec.prompt)[:3]
                    for i, variant in enumerate(variants):
                        all_attacks.append(AttackSpec(
                            **{**spec.__dict__,
                               "id": f"{spec.id}_V{i+1}",
                               "prompt": variant}
                        ))
                else:
                    all_attacks.append(spec)

        # ---- 3. Sample for Quick Mode ----
        if "quick" in suites and all_attacks:
            by_cat = {}
            for a in all_attacks:
                by_cat.setdefault(a.category, []).append(a)
            picks = []
            cats = list(by_cat.keys())
            random.shuffle(cats)
            for c in cats:
                picks.append(random.choice(by_cat[c]))
                if len(picks) >= 3:
                    break
            return [p.__dict__ for p in picks]

        # ---- 4. Trim Default Adversarial Suite ----
        if "default" in suites and "adversarial_extended" not in suites and len(suites) == 1:
            return [a.__dict__ for a in all_attacks[:20]]

        return [a.__dict__ for a in all_attacks]

    async def send_request_to_url(self, target_url: str, prompt: str) -> str:
        """
        Sends the prompt to the target agent API.
        """
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(target_url, json={"message": prompt}, timeout=30.0)
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "").lower()
                if "application/json" in content_type:
                    data = resp.json()
                    if isinstance(data, dict):
                        return data.get("response", "No response field in JSON")
                    return "Error connecting to agent: JSON response was not an object."
                return f"Error connecting to agent: Expected JSON response, got {content_type or 'unknown content-type'}."
        except Exception as e:
            return f"Error connecting to agent: {str(e)}"

    async def run_ephemeral_agent(self, system_prompt: str, user_input: str) -> str:
        """
        Spins up a transient 'Attacker Agent' using the factory LLM.
        """
        try:
            agent_llm = LLMFactory.create_llm(temperature=0.7)
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input)
            ]
            response = await agent_llm.ainvoke(messages)
            return response.content
        except Exception as e:
            return f"Error running ephemeral agent: {str(e)}"
