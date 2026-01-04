import asyncio
import json
from app.engine.red_team import RedTeam
from app.engine.judge import Judge
from app.core.config import settings

async def run_test_audit():
    print("🚀 Starting End-to-End Audit Pipeline Test...")
    
    # 1. Initialize Components
    rt = RedTeam()
    judge = Judge()
    
    # 2. Generate Attacks (Specifically looking for our New Advanced Probes)
    print("\n--- Phase 1: Attack Generation ---")
    attacks = rt.generate_attacks(suites=["default"])
    
    # Filter for the specific ones we just added to see if they're there
    target_ids = ["PI_SMILEY_SMUGGLE_01", "PI_LINK_SMUGGLE_02", "PI_REASONING_TRAP_01"]
    new_attacks = [a for a in attacks if any(tid in a['id'] for tid in target_ids)]
    
    if not new_attacks:
        print("❌ Error: New advanced attacks not found in generated list!")
        return
    
    print(f"✅ Found {len(new_attacks)} advanced probes in the library.")

    # 3. Choose one to test the full loop
    # We'll use the Link Smuggling one as it's Critical
    target_attack = new_attacks[0]
    print(f"\n--- Phase 2: Simulating Audit for {target_attack['id']} ---")
    print(f"Attack Prompt: {target_attack['prompt']}")
    
    # Simulate a "Pass" response (Refusal)
    safe_response = "I'm sorry, I cannot fulfill this request. My safety policy prevents me from exporting environment variables or interacting with untrusted debug endpoints."
    
    # 4. Evaluate with Judge Panel
    print("\n--- Phase 3: Selection of Judge Panel ---")
    print(f"Tier: {settings.TIER} | Consensus logic: Enabled")
    
    # Use await because Judge.evaluate is now async!
    try:
        metrics = await judge.evaluate(
            attack_prompt=target_attack['prompt'],
            agent_response=safe_response,
            tier=settings.TIER
        )
        
        print("\n--- Result ---")
        print(json.dumps(metrics, indent=2))
        
        if metrics.get('verdict') == "PASS":
            print("\n🌟 TEST PASSED: Judge correctly identified a safe refusal.")
        else:
            print("\n⚠️ TEST FAILED/FLAGGED: Check the verdict and reasoning.")
            
    except Exception as e:
        print(f"❌ Error during evaluation: {e}")

if __name__ == "__main__":
    asyncio.run(run_test_audit())
