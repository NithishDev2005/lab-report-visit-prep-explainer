"""
Streamlit Web UI for Lab Report Visit-Prep Explainer.
Run locally in VS Code:
    streamlit run app/ui/streamlit_app.py
"""

import streamlit as st
import json
import os
import sys

# Ensure root directory is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.agent import LabReportAgent
from app.core.database import init_db

init_db()
agent = LabReportAgent()

st.set_page_config(
    page_title="Lab Report Visit-Prep Explainer",
    page_icon="🩺",
    layout="wide"
)

st.title("🩺 Lab Report Visit-Prep Explainer")
st.caption("Agentic AI • Healthcare & Wellness • Ziro.Digital Hackathon 2026")

# Sidebar: Test Scenarios and Options
st.sidebar.header("📁 Report Ingestion")
mode = st.sidebar.radio("Select Input Mode", ["Official Hackathon Scenarios", "Custom Report Input"])

# Load Official Test Cases
with open(os.path.join(PROJECT_ROOT, "data", "synthetic_reports", "test_cases.json")) as f:
    test_cases = json.load(f)

selected_case = None
if mode == "Official Hackathon Scenarios":
    case_choice = st.sidebar.selectbox("Choose Official Test Case", list(test_cases.keys()), format_func=lambda k: test_cases[k]["title"])
    selected_case = test_cases[case_choice]
    st.sidebar.info(f"**Scenario Objective:** {selected_case['description']}")

# Patient Consent Gate
st.subheader("1. Patient Consent")
consent = st.checkbox("I consent to private, local analysis of my laboratory report for doctor-visit preparation. (Zero diagnostic claims will be generated).", value=True)

if not consent:
    st.warning("⚠️ User consent must be granted before health biomarker processing can initiate.")
    st.stop()

# Execution Trigger
if st.button("🚀 Run Agent Analysis", type="primary"):
    with st.spinner("Analyzing biomarkers, verifying lab ranges, and retrieving NIH citations..."):
        st.session_state["result"] = agent.process_report(selected_case, consent_given=True)

if "result" in st.session_state:
    res = st.session_state["result"]
    session_id = res.get("session_id")

    # Handling TC3: Ambiguity Intercept
    if res["status"] == "AWAITING_USER_CONFIRMATION":
        st.error("⚠️ Human Clarification Required (OCR Ambiguity Detected)")
        amb = res["ambiguities"][0]
        st.write(f"The OCR detected an ambiguous value for **{amb['test_name']}** (scanned text: `{amb['raw_string']}`).")
        confirmed_val = st.radio("Please select the correct printed reading from your physical report:", amb["candidate_options"], format_func=lambda x: f"{x} mg/dL")
        
        if st.button("Confirm Reading and Resume"):
            st.session_state["result"] = agent.confirm_ambiguity(session_id, {amb["test_key"]: confirmed_val})
            st.rerun()
        st.stop()

    # Handling TC4: Critical Clinical Alert Banner
    if res.get("critical_alerts"):
        for alert in res["critical_alerts"]:
            st.error(f"🚨 **{alert['test_name']} ({alert['value']}):** {alert['advisory']}")

    # Display Processed Biomarkers & Verification Table
    st.subheader("2. Biomarker Extraction & Verification Audit")
    tabs = st.tabs(["Biomarker Summary", "Dual Verification Audit", "Doctor Questions", "Visit Note Preview"])

    with tabs[0]:
        cols = st.columns(3)
        cols[0].metric("Patient", res["patient"].get("name"))
        cols[1].metric("Collection Date", res["patient"].get("collection_date"))
        cols[2].metric("Agent State", res["status"])

        for t in res.get("processed_tests", []):
            with st.expander(f"{t['test_name']} — {t['result']} {t['unit']} ({t['status']})", expanded=True):
                st.write(f"**Laboratory Reference Interval:** `{t['printed_range']}`")
                if t.get("lab_range_differs_from_generic"):
                    st.info("ℹ️ **Lab Range Priority Active:** This value was evaluated using the laboratory instrument's printed reference range, overriding generic population averages.")
                st.write(f"**What it measures:** {t['plain_definition']}")
                st.caption(f"Source: [{t['source_name']}]({t['source_url']})")

    with tabs[1]:
        v = res.get("verification_report", {})
        st.write(f"**Audit Status:** {'✅ 100% Fidelity Pass' if v.get('all_passed') else '❌ Verification Discrepancy'}")
        audit_rows = []
        for a in v.get("audits", []):
            audit_rows.append({
                "Test Name": a["test_name"],
                "Input Value": a["input_value"],
                "Extracted Value": a["extracted_value"],
                "Value Match": a["value_check"],
                "Unit Match": a["unit_check"],
                "Source Cited": "PASS" if a["source_cited"] else "FAIL",
                "Overall": a["overall_status"]
            })
        st.dataframe(audit_rows, use_container_width=True)

    with tabs[2]:
        st.write("Targeted discussion questions prepared for your attending physician:")
        for q in res.get("doctor_questions", []):
            st.markdown(f"- {q}")

    with tabs[3]:
        note = res.get("proposed_note", {})
        st.markdown(note.get("summary_markdown", ""))
        
        st.divider()
        st.subheader("3. Human-in-the-Loop Permitted Action")
        st.write("The agent proposes saving this private visit-prep note to your secure clinical database. Explicit user approval is required.")
        
        if st.button("✅ Approve and Save Visit-Prep Note", type="primary"):
            app_res = agent.approve_and_save_note(note["note_id"])
            if app_res["status"] == "SUCCESS_APPROVED_AND_SAVED":
                st.success(f"🎉 Note `{note['note_id']}` approved by user and securely stored in SQLite at {app_res['approved_at']}!")
            elif app_res["status"] == "ALREADY_APPROVED":
                st.info(f"ℹ️ Note `{note['note_id']}` was already approved and stored. Duplicate write prevented.")
