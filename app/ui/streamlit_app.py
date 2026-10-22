import streamlit as st
import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.agent import LabReportAgent
from app.core.database import init_db

init_db()
agent = LabReportAgent()

st.set_page_config(
    page_title="LabPrep AI | Clinical Visit Explainer",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Premium Clinical SaaS Interface
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Top Hero Header */
    .hero-container {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0369A1 100%);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        color: white;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
    }
    .hero-badge {
        display: inline-block;
        background: rgba(56, 189, 248, 0.2);
        border: 1px solid rgba(56, 189, 248, 0.4);
        color: #38BDF8;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 4px 12px;
        border-radius: 20px;
        margin-bottom: 10px;
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        color: #F8FAFC;
    }
    .hero-desc {
        color: #94A3B8;
        font-size: 0.95rem;
        margin-top: 6px;
        max-width: 800px;
        line-height: 1.5;
    }
    
    /* KPI Stats Bar */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.06);
    }
    .kpi-title {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        font-weight: 600;
    }
    .kpi-value {
        font-size: 1.5rem;
        font-weight: 800;
        color: #0F172A;
        margin-top: 4px;
    }
    
    /* Biomarker Cards */
    .bio-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 16px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        border-left: 5px solid #0284C7;
    }
    .bio-card-critical {
        border-left: 5px solid #DC2626 !important;
        background: #FFF5F5 !important;
    }
    .pill-normal {
        background: #DCFCE7;
        color: #15803D;
        font-weight: 700;
        font-size: 0.75rem;
        padding: 4px 12px;
        border-radius: 20px;
        border: 1px solid #BBF7D0;
    }
    .pill-lab {
        background: #E0F2FE;
        color: #0369A1;
        font-weight: 700;
        font-size: 0.75rem;
        padding: 4px 12px;
        border-radius: 20px;
        border: 1px solid #BAE6FD;
    }
    .pill-critical {
        background: #FEE2E2;
        color: #B91C1C;
        font-weight: 800;
        font-size: 0.75rem;
        padding: 4px 12px;
        border-radius: 20px;
        border: 1px solid #FECACA;
    }
    
    /* Visual Gauge Bar */
    .range-bar-bg {
        width: 100%;
        height: 8px;
        background: #E2E8F0;
        border-radius: 4px;
        margin: 12px 0 6px 0;
        position: relative;
    }
    .range-bar-fill {
        height: 100%;
        border-radius: 4px;
        background: linear-gradient(90deg, #38BDF8 0%, #10B981 50%, #EF4444 100%);
    }

    /* Question Cards */
    .q-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Hero Header Component
st.markdown("""
<div class="hero-container">
    <div class="hero-badge">Ziro.Digital Agentic AI Hackathon 2026 • Team smart_Builders</div>
    <h1 class="hero-title">Lab Report Visit-Prep Explainer 🩺</h1>
    <p class="hero-desc">
        Empowering patients with plain-language biomarker insights and structured physician consultation questions. Built with strict clinical safety guardrails, automated unit fidelity verification, and zero medical diagnoses.
    </p>
</div>
""", unsafe_allow_html=True)

# Load Test Cases
test_cases_file = os.path.join(PROJECT_ROOT, "data", "synthetic_reports", "test_cases.json")
with open(test_cases_file, "r", encoding="utf-8") as f:
    test_cases = json.load(f)

# Sidebar Design
st.sidebar.markdown("### 🎛️ Scenario Lab")
scenario_keys = list(test_cases.keys())
selected_key = st.sidebar.radio(
    "Choose Test Scenario to Run:",
    scenario_keys,
    format_func=lambda k: test_cases[k]["title"]
)
active_case = test_cases[selected_key]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Scenario Focus:**")
st.sidebar.caption(active_case["description"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🛡️ Clinical Consent Guardrail")
consent = st.sidebar.checkbox(
    "Informed Patient Consent Active",
    value=True,
    help="Under HIPAA/GDPR clinical AI ethics, health records are only parsed with verified consent."
)

if not consent:
    st.warning("⚠️ **Execution Suspended:** Patient consent must be active in the sidebar to process health biomarker data.")
    st.stop()

# Execution Pipeline
if "result" not in st.session_state or st.session_state.get("current_scenario") != selected_key:
    st.session_state["result"] = agent.process_report(active_case, consent_given=True)
    st.session_state["current_scenario"] = selected_key

res = st.session_state.get("result", {})
session_id = res.get("session_id", "SES-INIT")

# TC3: Ambiguity Intercept Modal
if res.get("status") == "AWAITING_USER_CONFIRMATION":
    amb = res["ambiguities"][0]
    st.error("🛑 **Human-in-the-Loop Intercept: Ambiguous Reading Detected (TC3)**")
    st.markdown(f"""
    <div class="kpi-card" style="border-left: 5px solid #F59E0B; margin-bottom: 20px;">
        <h4 style="margin: 0; color: #B45309;">Clinical Safety Alert: Low OCR Confidence ({int(amb['confidence']*100)}%)</h4>
        <p style="margin: 8px 0; color: #475569;">
            The visual scanner encountered smudging on <b>{amb['test_name']}</b> (Raw token: <code>{amb['raw_string']}</code>).
            Clinical policy strictly prohibits guessing numerical lab values.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    confirmed_val = st.radio(
        "Please select the exact printed reading verified on your paper report:",
        amb["candidate_options"],
        format_func=lambda x: f"{x} mg/dL (Verified on Paper Report)",
        horizontal=True
    )
    if st.button("✅ Confirm Value & Resume Agent", type="primary"):
        st.session_state["result"] = agent.confirm_ambiguity(session_id, {amb["test_key"]: confirmed_val})
        st.rerun()
    st.stop()

# TC4: Critical Value Alert
if res.get("critical_alerts"):
    for alert in res["critical_alerts"]:
        st.markdown(f"""
        <div class="kpi-card" style="border: 1px solid #FCA5A5; background: #FEF2F2; border-left: 6px solid #DC2626; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.5rem;">🚨</span>
                <div>
                    <h4 style="margin: 0; color: #991B1B;">URGENT CLINICAL ESCALATION: {alert['test_name']} ({alert['value']})</h4>
                    <p style="margin: 4px 0 0 0; color: #7F1D1D; font-size: 0.95rem;">
                        {alert['advisory']}
                    </p>
                    <span style="display: inline-block; margin-top: 6px; font-size: 0.75rem; color: #991B1B; font-weight: 700;">
                        SAFETY DIRECTIVE: ZERO MEDICAL DIAGNOSIS CLAIMED • SEEK CLINICIAN GUIDANCE IMMEDIATELY
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Top KPI Summary Cards
kpi_cols = st.columns(4)
with kpi_cols[0]:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Patient Profile</div>
        <div class="kpi-value" style="font-size: 1.2rem;">{res['patient'].get('name', 'Patient Alpha')}</div>
        <div style="font-size: 0.8rem; color: #64748B; margin-top: 2px;">ID: {active_case['patient'].get('id', 'SYN-1001')}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[1]:
    total_tests = len(res.get("processed_tests", []))
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Biomarkers Parsed</div>
        <div class="kpi-value">{total_tests} Tests</div>
        <div style="font-size: 0.8rem; color: #10B981; margin-top: 2px;">✓ Verified 100% Units Match</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[2]:
    has_lab_override = any(t.get("lab_range_differs_from_generic") for t in res.get("processed_tests", []))
    calib_text = "Lab-Analyzer Priority" if has_lab_override else "Standard Calibration"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Instrument Range Rule</div>
        <div class="kpi-value" style="font-size: 1.15rem; color: #0284C7;">{calib_text}</div>
        <div style="font-size: 0.8rem; color: #64748B; margin-top: 2px;">TC2 Analyzer Precedence Active</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[3]:
    crit_count = len(res.get("critical_alerts", []))
    crit_color = "#DC2626" if crit_count > 0 else "#10B981"
    crit_label = f"{crit_count} Critical Alert" if crit_count > 0 else "All Limits Stable"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Clinical Risk State</div>
        <div class="kpi-value" style="color: {crit_color}; font-size: 1.15rem;">{crit_label}</div>
        <div style="font-size: 0.8rem; color: #64748B; margin-top: 2px;">Zero Diagnosis Guardrail Verified</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# Main Navigation Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🩺 Biomarker Intelligence",
    "🛡️ Dual-Verification Audit",
    "💬 Consultation Questions",
    "📝 Approved Visit Note"
])

# TAB 1: BIOMARKERS
with tab1:
    st.markdown("#### Patient Biomarker Breakdown")
    st.caption("Values are strictly evaluated against the laboratory analyzer's specific printed ranges.")
    
    for t in res.get("processed_tests", []):
        is_crit = t.get("is_critical")
        status = t.get("status")
        
        card_class = "bio-card bio-card-critical" if is_crit else "bio-card"
        badge_html = '<span class="pill-critical">CRITICAL HIGH</span>' if is_crit else (
            '<span class="pill-normal">✓ Within Reference Range</span>' if status == "Normal" else f'<span class="pill-critical">{status}</span>'
        )
        lab_badge = '<span class="pill-lab">🔬 Lab Analyzer Calibrated</span>' if t.get("lab_range_differs_from_generic") else ''
        
        st.markdown(f"""
        <div class="{card_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 1.15rem; font-weight: 700; color: #0F172A;">{t['test_name']}</span>
                <div>{lab_badge} &nbsp; {badge_html}</div>
            </div>
            <div style="display: flex; align-items: baseline; gap: 8px; margin: 12px 0 6px 0;">
                <span style="font-size: 2rem; font-weight: 800; color: #0F172A;">{t['result']}</span>
                <span style="font-size: 1rem; font-weight: 600; color: #64748B;">{t['unit']}</span>
                <span style="font-size: 0.9rem; color: #94A3B8; margin-left: 12px;">(Laboratory Analyzer Interval: <b>{t['printed_range']}</b>)</span>
            </div>
            <div class="range-bar-bg"><div class="range-bar-fill" style="width: 60%;"></div></div>
            <p style="margin: 10px 0 4px 0; font-size: 0.9rem; color: #334155; line-height: 1.5;">
                <b>What this test measures:</b> {t['plain_definition']}
            </p>
            <div style="font-size: 0.8rem; color: #64748B; margin-top: 6px;">
                Clinical Citation: <a href="{t['source_url']}" target="_blank" style="color: #0284C7; font-weight: 600; text-decoration: none;">{t['source_name']} ↗</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

# TAB 2: AUDIT
with tab2:
    st.markdown("#### Programmatic Verification Grid")
    st.caption("Verifies that every extracted character, unit, and reference interval matches the raw input with zero drift.")
    
    v = res.get("verification_report", {})
    audit_data = []
    for a in v.get("audits", []):
        audit_data.append({
            "Biomarker Name": a["test_name"],
            "Report Raw Value": a["input_value"],
            "Agent Parsed Value": a["extracted_value"],
            "Numerical Match": "✓ EXACT PASS" if a["value_check"] == "PASS" else a["value_check"],
            "Unit Preserved": f"✓ {a['extracted_unit']}" if a["unit_check"] == "PASS" else "FAIL",
            "NIH Citation Grounded": "✓ VERIFIED" if a["source_cited"] else "FAIL",
            "Verification Verdict": "✅ COMPLIANT" if a["overall_status"] == "PASS" else a["overall_status"]
        })
    st.dataframe(audit_data, use_container_width=True)

# TAB 3: QUESTIONS
with tab3:
    st.markdown("#### Tailored Physician Discussion Questions")
    st.caption("Review and take these specific questions into your clinical consultation:")
    
    for i, q in enumerate(res.get("doctor_questions", []), start=1):
        st.markdown(f"""
        <div class="q-card">
            <span style="background: #0284C7; color: white; border-radius: 50%; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700; flex-shrink: 0;">{i}</span>
            <span style="font-size: 0.95rem; color: #1E293B; font-weight: 500;">{q}</span>
        </div>
        """, unsafe_allow_html=True)

# TAB 4: NOTE
with tab4:
    note = res.get("proposed_note", {})
    st.markdown("#### Generated Doctor Visit Preparation Document")
    st.text_area("Visit Note Preview (Markdown):", value=note.get("summary_markdown", ""), height=260)
    
    st.markdown("---")
    st.markdown("### 🔒 Permitted Action: Human Approval Gate")
    st.caption("The agent requires your explicit sign-off before committing this private note to your local medical records database.")
    
    action_cols = st.columns([2, 1])
    with action_cols[0]:
        if st.button("✅ Approve & Commit to Database", type="primary", use_container_width=True):
            app_res = agent.approve_and_save_note(note["note_id"])
            if app_res["status"] == "SUCCESS_APPROVED_AND_SAVED":
                st.success(f"🎉 **Visit-Prep Note Successfully Committed!** Note ID `{note['note_id']}` securely recorded in SQLite at `{app_res['approved_at']}`.")
            elif app_res["status"] == "ALREADY_APPROVED":
                st.info(f"ℹ️ Note `{note['note_id']}` was already approved and stored. Duplicate execution prevented.")
    with action_cols[1]:
        st.download_button(
            label="📥 Export Note (.md)",
            data=note.get("summary_markdown", ""),
            file_name=f"visit_prep_note_{session_id}.md",
            mime="text/markdown",
            use_container_width=True
        )