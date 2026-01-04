import asyncio
from unittest.mock import AsyncMock, patch
from app.engine.judge import Judge, AuditMetrics, EvidenceSpan

async def test_judge_consensus():
    judge = Judge()
    
    # Mock return values for res_a and res_b
    def create_metrics(verdict="PASS", safety=90, hallu=-1, violations=None):
        return AuditMetrics(
            verdict=verdict,
            safety_score=safety,
            hallucination_score=hallu,
            tone_score=95,
            violations=violations or [],
            evidence=[EvidenceSpan(source="response", quote="test")],
            reason="test reason"
        )

    # 1. Test Perfect Consensus
    print("Test 1: Perfect Consensus...")
    res_a = create_metrics()
    res_b = create_metrics()
    
    with patch.object(Judge, '_run_single_judge', side_effect=[res_a, res_b]):
        result = await judge.evaluate("attack", "response")
        assert result["is_consensus"] is True
        print("✅ Passed")

    # 2. Test Safety Delta Failure
    print("Test 2: Safety Delta Failure...")
    res_a = create_metrics(safety=100)
    res_b = create_metrics(safety=80) # Delta 20 > 15
    
    with patch.object(Judge, '_run_single_judge', side_effect=[res_a, res_b, create_metrics()]):
        result = await judge.evaluate("attack", "response")
        assert result["is_consensus"] is False
        assert "safety delta too high" in result["reason"]
        print("✅ Passed")

    # 3. Test Critical Violation Mismatch
    print("Test 3: Critical Violation Mismatch...")
    res_a = create_metrics(verdict="FAIL", violations=["PII_LEAK"])
    res_b = create_metrics(verdict="FAIL", violations=["MEDICAL"]) # MEDICAL isn't in critical set, but PII_LEAK is
    
    with patch.object(Judge, '_run_single_judge', side_effect=[res_a, res_b, create_metrics()]):
        result = await judge.evaluate("attack", "response")
        assert result["is_consensus"] is False
        assert "critical violation mismatch" in result["reason"]
        print("✅ Passed")

    # 4. Test Hallucination Aggregation Fix
    print("Test 4: Hallucination Aggregation Fix...")
    res_a = create_metrics(hallu=80)
    res_b = create_metrics(hallu=-1) # One is N/A
    
    with patch.object(Judge, '_run_single_judge', side_effect=[res_a, res_b]):
        result = await judge.evaluate("attack", "response")
        assert result["is_consensus"] is True
        assert result["hallucination_score"] == 80 # Should take the real score
        print("✅ Passed")

    # 5. Test Jaccard Similarity Failure
    print("Test 5: Jaccard Similarity Failure...")
    res_a = create_metrics(violations=["MEDICAL", "LEGAL"])
    res_b = create_metrics(violations=["FINANCIAL"]) # No overlap
    
    with patch.object(Judge, '_run_single_judge', side_effect=[res_a, res_b, create_metrics()]):
        result = await judge.evaluate("attack", "response")
        assert result["is_consensus"] is False
        assert "violation overlap too low" in result["reason"]
        print("✅ Passed")

    print("\nAll Consensus Logic Tests Passed!")

if __name__ == "__main__":
    asyncio.run(test_judge_consensus())
