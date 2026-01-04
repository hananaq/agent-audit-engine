import streamlit as st
import httpx
import pandas as pd
import time
import concurrent.futures
import os
import sys

from pathlib import Path

# Add backend to path for config
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))
try:
    from app.core.config import settings
    from app.engine.probes.library import PROBE_LIBRARY
    from app.engine.probes.mutator import ProbeMutator
except ImportError:
    # Fallback if backend structure isn't exactly as expected
    settings = None
    PROBE_LIBRARY = {}
    ProbeMutator = None

def _count_attacks_for_suites(mode: str, suites: list[str]) -> int:
    selected_categories = []
    if "default" in suites or "quick" in suites or "adversarial_extended" in suites:
        selected_categories += [
            "Prompt Injection & Jailbreaks",
            "Security & Hygiene",
            "Hallucination & Factual Grounding",
            "Tone, Toxicity & Bias",
            "Logic & Consistency",
        ]

    if "dos" in suites:
        selected_categories.append("Model DoS & Cost Attacks")
    if "agent_security" in suites:
        selected_categories.append("Tool & Action Hijacking")
    if "gdpr" in suites:
        selected_categories.append("GDPR Compliance")
    if "hipaa" in suites:
        selected_categories.append("HIPAA Compliance")
    if "eu_ai_act" in suites:
        selected_categories.append("EU AI Act")
    if mode == "rag":
        selected_categories.append("RAG Security")

    variant_cats = {"Prompt Injection & Jailbreaks", "RAG Security"}
    variants_per_spec = 3 if ProbeMutator else 1
    total = 0
    for cat in selected_categories:
        specs = PROBE_LIBRARY.get(cat, [])
        if cat in variant_cats:
            total += len(specs) * variants_per_spec
        else:
            total += len(specs)

    if "quick" in suites:
        categories_with_attacks = [cat for cat in selected_categories if PROBE_LIBRARY.get(cat)]
        return min(3, len(categories_with_attacks))

    if "default" in suites and "adversarial_extended" not in suites and len(suites) == 1:
        return min(20, total)

    return total

# Custom CSS for premium look
st.set_page_config(
    page_title="AgentAudit | AI Security Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.html("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .main {
        background-color: #020617;
        color: #f8fafc;
    }
    
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #2563eb, #4f46e5);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 0.75rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4);
        background: linear-gradient(90deg, #3b82f6, #6366f1);
    }
    
    .glass-card, div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(8, 12, 24, 0.95) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 1.5rem !important;
        padding: 0.5rem;
    }
    
    .sticky-header {
        position: -webkit-sticky;
        position: sticky;
        top: 0;
        z-index: 1000;
        background: transparent !important;
        padding-top: 1rem;
        margin-bottom: 1rem;
    }
    
    .gradient-text {
        background: linear-gradient(90deg, #60a5fa, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    
    .badge {
        padding: 0.2rem 0.6rem;
        border-radius: 0.5rem;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        white-space: nowrap;
    }
    
    .badge-lite { background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); color: #60a5fa; }
    .badge-pro { background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2); color: #fbbf24; }
    
    .badge-critical { background: rgba(127, 29, 29, 0.2); border: 1px solid rgba(127, 29, 29, 0.4); color: #f87171; }
    .badge-high { background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); color: #ef4444; }
    .badge-medium { background: rgba(249, 115, 22, 0.1); border: 1px solid rgba(249, 115, 22, 0.2); color: #f97316; }
    .badge-low { background: rgba(250, 204, 21, 0.1); border: 1px solid rgba(250, 204, 21, 0.2); color: #facc15; }
    .badge-passed { background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); color: #10b981; }
    .badge-consensus { background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.2); color: #818cf8; }
    .badge-supreme { background: rgba(192, 38, 211, 0.1); border: 1px solid rgba(192, 38, 211, 0.2); color: #e879f9; margin-top: 0.25rem; display: inline-block; }
    
    .score-display {
        font-size: 4rem;
        font-weight: 900;
        line-height: 1;
        margin-bottom: 0.5rem;
    }
    
    .issue-card {
        padding: 1.25rem;
        background: rgba(15, 23, 42, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-left: 6px solid #3b82f6;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
    }
    
    .issue-card b {
        color: #ffffff !important;
        font-size: 1.15rem;
        letter-spacing: 0.02em;
    }
    
    .issue-card p {
        color: #f1f5f9 !important;
        line-height: 1.6;
    }
    
    .severity-fail { border-left-color: #ef4444; }
    .severity-warn { border-left-color: #f97316; }
    .severity-pass { border-left-color: #10b981; }
    
    .violation-tag {
        display: inline-block;
        padding: 0.1rem 0.4rem;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 0.3rem;
        font-size: 0.65rem;
        color: #94a3b8;
        margin-right: 0.3rem;
        margin-top: 0.3rem;
        text-transform: uppercase;
    }
</style>
""")

# Try to get tier from backend
backend_url = "http://localhost:8000/"
current_tier = "lite"
backend_status = "offline"
try:
    response = httpx.get(backend_url, timeout=2.0)
    if response.status_code == 200:
        current_tier = response.json().get("tier", "lite")
        backend_status = "online"
    else:
        backend_status = "error"
except Exception:
    backend_status = "offline"

# Sidebar for config & status
with st.sidebar:
    tier_class = "badge-pro" if current_tier == "premium" else "badge-lite"
    
    st.html(f'''
    <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
        <h1 class="gradient-text" style="margin: 0; font-size: 2.2rem; line-height: 1;">AgentAudit</h1>
        <span class="badge {tier_class}" style="padding: 0.1rem 0.4rem; font-size: 0.65rem;">{current_tier.upper()}</span>
    </div>
    ''')
    
    st.markdown("v1.0.0 Beta")
    
    st.divider()
    
    if backend_status == "online":
        st.success("Backend Connected")
    elif backend_status == "error":
        st.error("Backend Error")
    else:
        st.warning("Backend Offline")
    
    st.divider()
    if current_tier in ("pro", "premium"):
        judge_text = "Multi-provider ensemble (OpenAI, Anthropic, Gemini) settles disputes for maximum precision."
    else:
        judge_text = "Multi-provider ensemble (Llama, Gemini, DeepSeek) settles disputes for maximum precision."

    st.html(f"""
        <div class="glass-card" style="padding: 1rem; border-radius: 1rem !important; background: rgba(15, 23, 42, 0.4) !important;">
            <h3 style="color: white; margin-top: 0; font-size: 1.1rem;">How it Works</h3>
            <div style="margin-bottom: 0.75rem;">
                <b style="color: #60a5fa; font-size: 0.85rem;">🛡️ Adversarial RedTeaming</b><br/>
                <span style="color: #94a3b8; font-size: 0.8rem;">Simulates complex attacks to find jailbreaks and security leaks.</span>
            </div>
            <div style="margin-bottom: 0.75rem;">
                <b style="color: #a78bfa; font-size: 0.85rem;">🇪🇺 Compliance Scanning</b><br/>
                <span style="color: #94a3b8; font-size: 0.8rem;">Validates responses against GDPR, HIPAA, and EU AI Act.</span>
            </div>
            <div>
                <b style="color: #34d399; font-size: 0.85rem;">⚖️ Court of Judges</b><br/>
                <span style="color: #94a3b8; font-size: 0.8rem;">{judge_text}</span>
            </div>
        </div>
    """)

# Main Layout
col1, col2 = st.columns([5, 7], gap="large")

with col1:
    st.markdown('<h1 class="gradient-text">Secure your AI Agents</h1>', unsafe_allow_html=True)
    st.markdown("""
    **AgentAudit** is an automated adversarial testing platform.
    Validate Safety, prevent Hallucinations, and ensure Compliance before you ship.
    """)
    
    with st.container(border=True):
        
        target_url = st.text_input("Target Endpoint", placeholder="https://api.yourcompany.com/v1/chat")
        
        mode = st.selectbox(
            "Agent Mode",
            options=["chatbot", "rag"],
            format_func=lambda x: "Chatbot" if x == "chatbot" else "RAG (Knowledge-Based)"
        )

        adversarial_count = _count_attacks_for_suites(mode, ["default"])
        extended_count = _count_attacks_for_suites(mode, ["adversarial_extended"])
        quick_count = _count_attacks_for_suites(mode, ["quick"])
        
        def _normalize_suites():
            selected = st.session_state.get("selected_suites", [])
            if "quick" in selected and len(selected) > 1:
                st.session_state.selected_suites = [s for s in selected if s != "quick"]
                return
            if "adversarial_extended" in selected and "default" in selected:
                st.session_state.selected_suites = [s for s in selected if s != "default"]

        if "selected_suites" not in st.session_state:
            st.session_state.selected_suites = ["quick"]

        suites = st.multiselect(
            "Compliance Suites",
            options=["default", "adversarial_extended", "gdpr", "hipaa", "eu_ai_act", "quick"],
            key="selected_suites",
            on_change=_normalize_suites,
            format_func=lambda x: {
                "default": f"🛡️ Adversarial ({adversarial_count})",
                "adversarial_extended": f"🛡️ Adversarial (Extended) ({extended_count})",
                "gdpr": "🇪🇺 GDPR",
                "hipaa": "🏥 HIPAA",
                "eu_ai_act": "📝 EU AI Act",
                "quick": f"⚡ Quick Test ({quick_count})"
            }.get(x, x)
        )
        
        st.write("")
        if "audit_running" not in st.session_state:
            st.session_state.audit_running = False

        if st.button("Initiate Audit Sequence", disabled=st.session_state.audit_running):
            if not target_url:
                st.error("Please provide a target endpoint URL.")
            else:
                st.session_state.audit_running = True
                progress = st.progress(0, text="Running audit...")
                total_attacks = _count_attacks_for_suites(mode, suites)
                estimated_seconds = max(10, total_attacks * 8)

                def _run_audit():
                    return httpx.post(
                        "http://localhost:8000/api/v1/audit",
                        json={"target_url": target_url, "suites": suites, "mode": mode},
                        timeout=httpx.Timeout(3600.0, connect=10.0)
                    )

                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(_run_audit)
                    start = time.time()
                    while not future.done():
                        elapsed = time.time() - start
                        pct = min(95, int((elapsed / estimated_seconds) * 100))
                        progress.progress(pct, text=f"Running audit... {pct}%")
                        time.sleep(0.5)
                    try:
                        resp = future.result()
                        progress.progress(100, text="Finalizing results...")
                        if resp.status_code == 200:
                            st.session_state.results = resp.json()
                            st.rerun()
                        else:
                            st.error(f"Audit Failed: {resp.text}")
                    except Exception as e:
                        st.error(f"Connection Error: {str(e)}")
                    finally:
                        st.session_state.audit_running = False
        
        

with col2:
    if "results" in st.session_state:
        results = st.session_state.results
        backend_results = results.get("results", [])
        
        # Calculate scores
        backend_results = results.get("results", [])
        is_rate_limited = results.get("rate_limited", False)
        
        is_failed = results.get("status") == "failed"
        if backend_results:
            avg_safety = sum(r.get("metrics", {}).get("safety_score", 50) for r in backend_results) / len(backend_results)
            score = round(avg_safety)
        else:
            score = 100
            
        score_display = "--" if (is_rate_limited or is_failed or not backend_results) else str(score)
        score_color = "#64748b" if (is_rate_limited or is_failed or not backend_results) else (
            "#34d399" if score > 80 else "#fbbf24" if score > 60 else "#f87171"
        )
        
        st.html(f"""
        <div class="sticky-header">
            <div class="glass-card">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <h3 style="margin: 0; color: white;">Audit Report</h3>
                        <p style="color: #94a3b8; font-size: 0.8rem;">Target: {target_url or 'System Prompt'}</p>
                    </div>
                    <div style="text-align: right;">
                        <div class="score-display" style="color: {score_color};">{score_display}<span style="font-size: 1.5rem; color: #64748b;">/100</span></div>
                        <div style="font-size: 0.7rem; color: #64748b; font-weight: 700; text-transform: uppercase;">Robustness Score</div>
                    </div>
                </div>
            </div>
        </div>
        """)
        
        if results.get("rate_limited"):
            st.warning(f"⚠️ **Audit Incomplete (Rate Limited)**\n\n{results.get('rate_limit_message', 'Groq API rate limit reached. Please wait before retrying.')}")

        if results.get("status") == "failed":
            st.error(f"🚫 **Connection Failed**\n\n{results.get('error_message', 'The engine could not connect to your agent endpoint.')}")
            st.info("💡 **Tip**: Make sure your agent is running and the URL is accessible from the backend.")
            if not backend_results:
                st.stop()

        # Check if there are any failures or warnings
        all_passed = all(r.get("metrics", {}).get("verdict") == "PASS" for r in backend_results)
        
        if all_passed:
            st.markdown('<h3 style="color: #10b981; margin-top: 2rem;">✅ No Vulnerabilities Detected</h3>', unsafe_allow_html=True)
        else:
            st.subheader("Vulnerabilities Detected")
        
        # Sort results by safety score (lowest first = highest risk first)
        backend_results.sort(key=lambda x: x.get("metrics", {}).get("safety_score", 50))
        
        for i, r in enumerate(backend_results):
            metrics = r.get("metrics", {})
            safety = metrics.get("safety_score", 50)
            attack = r.get("attack", "Unknown")
            category = r.get("category", "Security Test")
            
            # Use structured verdict from the new judge
            verdict = metrics.get("verdict", "FAIL")
            violations = metrics.get("violations", [])
            evidence = metrics.get("evidence", [])
            
            # Severity mapping for visual intensity
            severity_label = "Passed" if safety >= 95 else "Low" if safety >= 70 else "Medium" if safety >= 40 else "High" if safety >= 20 else "Critical"
            
            # CSS Class mapping
            sev_class = f"severity-{verdict.lower()}"
            badge_class = f"badge-{'passed' if verdict == 'PASS' else 'medium' if verdict == 'WARN' else 'high'}"
            
            # Simplify badge label
            badge_label = "PASSED" if verdict == "PASS" else f"{verdict} ({severity_label})"

            # Create violation tags HTML
            vuln_tags_html = "".join([f'<span class="violation-tag">{v}</span>' for v in violations])
            
            # Step 2: Extract consensus details
            is_consensus = metrics.get("is_consensus", True)
            consensus_badge = f'<span class="badge badge-consensus">Consensus Reached</span>' if is_consensus else f'<span class="badge badge-supreme">Supreme Court Verdict</span>'
            
            st.html(f"""
            <div class="issue-card {sev_class}">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <b style="color: #e2e8f0;">Security Test {i+1} - {category}</b>
                    <span class="badge {badge_class}">{badge_label}</span>
                </div>
                <p style="color: #94a3b8; font-size: 0.9rem; margin: 0;">{attack[:120]}...</p>
                <div style="margin-bottom: 0.5rem; margin-top: 0.5rem; display: flex; align-items: center; gap: 0.5rem;">
                    {vuln_tags_html}
                    {consensus_badge}
                </div>
            </div>
            """)
            
            # Using Streamlit expander for evidence to keep UI clean
            with st.expander(f"👁️ View Evidence & Reasoning"):
                if evidence:
                    st.markdown("**Evidence Quotes:**")
                    for e in evidence:
                        source_icon = "💬" if e['source'] == "response" else "📖"
                        st.info(f"{source_icon} *{e['source'].capitalize()}*: \"{e['quote']}\"")
                
                st.markdown("**Justification:**")
                st.write(metrics.get("reason", "No detailed reasoning provided."))
            
    else:
        st.markdown("""
        <div style="height: 600px; display: flex; flex-direction: column; align-items: center; justify-content: center; border: 2px dashed #1e293b; border-radius: 1.5rem; background: rgba(15, 23, 42, 0.2);">
            <div style="font-size: 5rem; color: #334155; margin-bottom: 2rem;">🛡️</div>
            <h3 style="color: #475569;">Ready for Audit</h3>
            <p style="color: #334155;">Configure a target and compliance suites to begin testing.</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown(
    """
    <div style="margin-top: 3rem; text-align: center; color: #64748b; font-size: 0.85rem;">
        Developed by <a href="https://www.linkedin.com/in/hananabukwaider/" target="_blank" style="color: #60a5fa; text-decoration: none;">Hanan Abu Kwaider</a>
    </div>
    """,
    unsafe_allow_html=True,
)
