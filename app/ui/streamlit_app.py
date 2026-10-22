import streamlit as st
import json, os, sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.agent import LabReportAgent
from app.core.database import init_db

init_db()
agent = LabReportAgent()

st.set_page_config(page_title="Lab Report Visit-Prep Explainer", page_icon="??", layout="wide")

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E293B; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1rem; color: #64748B; margin-bottom: 1.5rem; }
    .badge-normal { background-color: #DEF7EC; color: #03543F; padding: 4px 10px; border-radius: 9999px; font-size: 0.8rem; font-weight: 600; }
    .badge-critical { background-color: #FDE8E8; color: #9B1C1C; padding: 4px 10px; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; border: 1px solid #F98080; }
    .badge-lab { background-color: #E1EFFE; color: #1E429F; padding: 4px 10px; border-radius: 9999px; font-size: 0.8rem; font-weight: 600; }
    .metric-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">?? Lab Report Visit-Prep Explainer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Agentic Healthcare Assistant • Ziro.Digital Hackathon 2026 • Team smart_Builders</div>', unsafe_allow_html=True)

with open(os.path.join(PROJECT_ROOT, "data", "synthetic_reports", "test_cases.json")) as f:
    test_cases = json.load(f)

st.sidebar.header("?? Agent Controls")
scenario_choice = st.sidebar.selectbox("Select Test Case Scenario", list(test_cases.keys()), format_func=lambda k: test_cases[k]["title"])
active_case = test_cases[scenario_choice]
st.sidebar.info(f"**Target Objective:**\n{active_case['description']}")

st.sidebar.markdown("---")
consent = st.sidebar.checkbox("Explicit Patient Consent Granted", value=True)
if not consent:
    st.warning("?? **Consent Required:** User consent must be granted in the sidebar to process laboratory biomarker panels.")
    st.stop()

col1, col2 = st.columns([3, 1])
with col1:
    st.write(f"**Selected Panel:** {active_case['patient']['name']} | Collection: {active_case['patient']['collection_date']}")
with col2:
    run_btn = st.button("?? Analyze Lab Report", type="primary", use_container_width=True)

if run_btn or "result" not in st.session_state or st.session_state.get("current_scenario") != scenario_choice:
    st.session_state["result"] = agent.process_report(active_case, consent_given=True)
    st.session_state["current_scenario"] = scenario_choice

res = st.session_state.get("result", {})
session_id = res.get("session_id")

if res.get("status") == "AWAITING_USER_CONFIRMATION":
    st.error("?? **Human-in-the-Loop Intercept: OCR Token Ambiguity Detected**")
    amb = res["ambiguities"][0]
    st.markdown(f"The document reader detected visual smudging on **{amb['test_name']}** (Raw token: {amb['raw_string']}).")
    confirmed_val = st.radio("Please select the exact printed value on your physical paper report:", amb["candidate_options"], format_func=lambda x: f"{x} mg/dL (Printed on report)", horizontal=True)
    if st.button("Confirm Reading & Resume Agent", type="primary"):
        st.session_state["result"] = agent.confirm_ambiguity(session_id, {amb["test_key"]: confirmed_val})
        st.rerun()
    st.stop()

if res.get("critical_alerts"):
    for alert in res["critical_alerts"]:
        st.error(f"?? **HIGH-PRIORITY CLINICAL ESCALATION: {alert['test_name']} ({alert['value']})**\n{alert['advisory']}\n*(Safety Rule: Zero medical diagnoses are generated).*")

tab1, tab2, tab3, tab4 = st.tabs(["?? Biomarker Breakdown", "??? Dual-Verification Audit", "?? Questions for Your Doctor", "?? Exportable Visit Note"])

with tab1:
    st.markdown("### Verified Biomarker Cards")
    for t in res.get("processed_tests", []):
        is_crit = t.get("is_critical")
        status = t.get("status")
        badge_html = '<span class="badge-critical">CRITICAL</span>' if is_crit else ('<span class="badge-normal">Within Range</span>' if status == "Normal" else f'<span class="badge-critical">{status}</span>')
        lab_badge = '<span class="badge-lab">Lab-Analyzer Calibrated</span>' if t.get("lab_range_differs_from_generic") else ''
        st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; color: #1E293B;">{t['test_name']}</h4>
                <div>{lab_badge} &nbsp; {badge_html}</div>
            </div>
            <div style="margin: 8px 0; font-size: 1.25rem; font-weight: 700; color: #0F172A;">
                {t['result']} <span style="font-size: 0.9rem; font-weight: 500; color: #64748B;">{t['unit']}</span>
                <span style="font-size: 0.85rem; font-weight: normal; color: #64748B; margin-left: 15px;">(Lab Range: {t['printed_range']})</span>
            </div>
            <p style="margin: 4px 0; font-size: 0.9rem; color: #334155;"><b>What this measures:</b> {t['plain_definition']}</p>
            <div style="font-size: 0.8rem; color: #64748B;">Reference Source: <a href="{t['source_url']}" target="_blank" style="color: #2563EB;">{t['source_name']}</a></div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    v = res.get("verification_report", {})
    st.markdown("### Programmatic Copy & Grounding Audit")
    audit_data = []
    for a in v.get("audits", []):
        audit_data.append({
            "Biomarker": a["test_name"],
            "Input Value": a["input_value"],
            "Parsed Value": a["extracted_value"],
            "Value Check": "? PASS" if a["value_check"] == "PASS" else a["value_check"],
            "Unit Preserved": f"? {a['extracted_unit']}" if a["unit_check"] == "PASS" else "? FAIL",
            "NIH Citation Verified": "? PASS" if a["source_cited"] else "? FAIL",
            "Audit Verdict": "? VERIFIED" if a["overall_status"] == "PASS" else a["overall_status"]
        })
    st.dataframe(audit_data, use_container_width=True)

with tab3:
    st.markdown("### Personalized Doctor Consultation Questions")
    for q in res.get("doctor_questions", []):
        st.markdown(f"- **{q}**")

with tab4:
    note = res.get("proposed_note", {})
    st.markdown("### Proposed Doctor Visit Preparation Note")
    st.markdown(note.get("summary_markdown", ""))
    st.markdown("---")
    st.markdown("#### ?? Permitted Action: Human Approval Gate")
    col_a, col_b = st.columns([2, 1])
    with col_a:
        if st.button("? Approve & Save Visit-Prep Note", type="primary", use_container_width=True):
            app_res = agent.approve_and_save_note(note["note_id"])
            if app_res["status"] == "SUCCESS_APPROVED_AND_SAVED":
                st.success(f"?? **Note Stored!** Note ID {note['note_id']} securely recorded in SQLite at {app_res['approved_at']}.")
            elif app_res["status"] == "ALREADY_APPROVED":
                st.info(f"?? Note {note['note_id']} was already approved and stored.")
    with col_b:
        st.download_button(label="?? Download Prep Note (.md)", data=note.get("summary_markdown", ""), file_name=f"visit_prep_note_{session_id}.md", mime="text/markdown", use_container_width=True)
