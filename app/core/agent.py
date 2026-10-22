import uuid, json
from datetime import datetime
from app.core.grounding import GroundingEngine
from app.core.safety_rules import evaluate_test_result, sanitize_and_audit_no_diagnosis
from app.core.verifier import VerificationEngine
from app.core.database import get_connection

class LabReportAgent:
    def __init__(self):
        self.grounding = GroundingEngine()
        self.verifier = VerificationEngine()

    def process_report(self, report_data, consent_given=True):
        session_id = f"SES-{uuid.uuid4().hex[:8].upper()}"
        if not consent_given:
            return {"session_id": session_id, "status": "CONSENT_REQUIRED", "message": "Patient consent required."}

        patient = report_data.get("patient", {"name": "Patient", "collection_date": "2026-10-22"})
        tests = report_data.get("tests", [])

        ambiguities = []
        for t in tests:
            if t.get("is_ambiguous") or t.get("ocr_confidence", 1.0) < 0.70:
                ambiguities.append({
                    "test_key": t.get("test_key"),
                    "test_name": t.get("test_name"),
                    "raw_string": t.get("raw_ocr_string", "1.0*"),
                    "candidate_options": t.get("candidate_options", [1.0, 10.0]),
                    "confidence": t.get("ocr_confidence", 0.45)
                })

        if ambiguities:
            self._save_session(session_id, patient, consent_given, "AWAITING_USER_CONFIRMATION", tests)
            return {
                "session_id": session_id,
                "status": "AWAITING_USER_CONFIRMATION",
                "patient": patient,
                "ambiguities": ambiguities,
                "message": "OCR detected ambiguous readings. User confirmation is required before proceeding."
            }

        processed_tests = []
        grounded_map = {}
        critical_alerts = []
        doctor_questions = []

        for t in tests:
            k = t.get("test_key")
            name = t.get("test_name")
            res = t.get("result")
            p_range = t.get("printed_range", "")

            g = self.grounding.get_grounded_context(k or name)
            grounded_map[k] = g

            eval_res = evaluate_test_result(res, p_range, g)
            item = {
                "test_key": k,
                "test_name": name,
                "result": res,
                "unit": t.get("unit"),
                "printed_range": p_range,
                "status": eval_res["status"],
                "is_critical": eval_res["is_critical"],
                "critical_message": eval_res.get("critical_message"),
                "range_source_used": eval_res["range_source_used"],
                "lab_range_differs_from_generic": eval_res["lab_range_differs_from_generic"],
                "plain_definition": g.get("plain_definition"),
                "source_name": g.get("source_name"),
                "source_url": g.get("source_url")
            }
            processed_tests.append(item)

            if eval_res["is_critical"]:
                critical_alerts.append({
                    "test_name": name,
                    "value": f"{res} {t.get('unit')}",
                    "advisory": eval_res["critical_message"]
                })

            for q in g.get("doctor_questions", []):
                doctor_questions.append(f"Regarding {name}: {q}")

        v_rep = self.verifier.verify_extraction(tests, processed_tests, grounded_map)
        summary_md = self._build_plain_summary(patient, processed_tests, critical_alerts)
        clean_summary, no_diag_passed = sanitize_and_audit_no_diagnosis(summary_md)

        proposed_note = {
            "note_id": f"NOTE-{uuid.uuid4().hex[:8].upper()}",
            "session_id": session_id,
            "summary_markdown": clean_summary,
            "doctor_questions": doctor_questions,
            "critical_alerts": critical_alerts,
            "verification": v_rep,
            "approval_state": "PENDING"
        }

        self._save_session(session_id, patient, consent_given, "PROPOSED_FOR_APPROVAL", processed_tests)
        self._save_proposed_note(proposed_note)

        return {
            "session_id": session_id,
            "status": "PROPOSED_FOR_APPROVAL",
            "patient": patient,
            "processed_tests": processed_tests,
            "critical_alerts": critical_alerts,
            "doctor_questions": doctor_questions,
            "verification_report": v_rep,
            "proposed_note": proposed_note,
            "no_diagnosis_guarantee": no_diag_passed
        }

    def confirm_ambiguity(self, session_id, confirmed_values):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM report_sessions WHERE session_id = ?", (session_id,))
        session = c.fetchone()
        c.execute("SELECT * FROM extracted_tests WHERE session_id = ?", (session_id,))
        rows = c.fetchall()
        conn.close()

        tests = []
        for r in rows:
            k = r["test_key"]
            val = confirmed_values.get(k, r["result_value"])
            tests.append({
                "test_key": k,
                "test_name": r["test_name"],
                "result": float(val) if val is not None else None,
                "unit": r["unit"],
                "printed_range": r["printed_range"],
                "ocr_confidence": 1.0,
                "is_ambiguous": False
            })
        return self.process_report({"patient": {"name": session["patient_name"], "collection_date": session["collection_date"]}, "tests": tests}, consent_given=True)

    def approve_and_save_note(self, note_id, edits=None):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM visit_prep_notes WHERE note_id = ?", (note_id,))
        note = c.fetchone()
        if not note:
            conn.close()
            return {"status": "ERROR", "message": "Note not found"}
        if note["approval_status"] == "APPROVED":
            conn.close()
            return {"status": "ALREADY_APPROVED", "note_id": note_id, "approved_at": note["approved_at"]}
        
        now = datetime.utcnow().isoformat()
        txt = edits if edits else note["summary_markdown"]
        c.execute("UPDATE visit_prep_notes SET approval_status = 'APPROVED', summary_markdown = ?, approved_at = ? WHERE note_id = ?", (txt, now, note_id))
        conn.commit()
        conn.close()
        return {"status": "SUCCESS_APPROVED_AND_SAVED", "note_id": note_id, "approved_at": now}

    def _build_plain_summary(self, patient, tests, critical_alerts):
        lines = [
            f"## Doctor Visit Preparation Note",
            f"**Patient:** {patient.get('name')} | **Date:** {patient.get('collection_date')}",
            f"*Disclaimer: This document is for doctor-visit preparation only. It does NOT provide a diagnosis.*\n"
        ]
        if critical_alerts:
            lines.append("### ⚠️ Urgent Clinical Advisory")
            for a in critical_alerts:
                lines.append(f"- **{a['test_name']} ({a['value']}):** {a['advisory']}")
            lines.append("")
        lines.append("### Summary of Laboratory Biomarkers")
        for t in tests:
            status_desc = "within the expected range" if t["status"] == "Normal" else f"flagged as {t['status']}"
            lines.append(f"- **{t['test_name']}:** {t['result']} {t['unit']} ({status_desc} for lab range: {t['printed_range']})")
            if t.get("lab_range_differs_from_generic"):
                lines.append(f"  *Note:* Evaluated using the lab's analyzer range ({t['printed_range']}).")
            lines.append(f"  *What it measures:* {t['plain_definition']}")
            lines.append(f"  *Source Citation:* [{t['source_name']}]({t['source_url']})")
        return "\n".join(lines)

    def _save_session(self, session_id, patient, consent, status, tests):
        conn = get_connection()
        c = conn.cursor()
        now = datetime.utcnow().isoformat()
        c.execute("INSERT OR REPLACE INTO report_sessions VALUES (?, ?, ?, ?, ?, ?)", (session_id, patient.get("name"), patient.get("collection_date"), 1 if consent else 0, status, now))
        c.execute("DELETE FROM extracted_tests WHERE session_id = ?", (session_id,))
        for t in tests:
            c.execute("INSERT INTO extracted_tests (session_id, test_key, test_name, result_value, result_str, unit, printed_range, lab_flag, ocr_confidence, is_ambiguous) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (session_id, t.get("test_key"), t.get("test_name"), t.get("result"), str(t.get("result", "")), t.get("unit"), t.get("printed_range"), t.get("flag", "Normal"), t.get("ocr_confidence", 1.0), 1 if t.get("is_ambiguous") else 0))
        conn.commit()
        conn.close()

    def _save_proposed_note(self, note):
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO visit_prep_notes VALUES (?, ?, ?, ?, ?, ?, NULL)", (note["note_id"], note["session_id"], note["summary_markdown"], json.dumps(note["doctor_questions"]), json.dumps(note["critical_alerts"]), note["approval_state"]))
        conn.commit()
        conn.close()
