import sys, os, json, unittest
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from app.core.agent import LabReportAgent
from app.core.database import init_db

class TestOfficialHackathonCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.agent = LabReportAgent()
        with open(os.path.join(PROJECT_DIR, "data", "synthetic_reports", "test_cases.json"), "r") as f:
            cls.test_cases = json.load(f)

    def test_tc1_values_copied_with_units(self):
        tc1 = self.test_cases["TC1_values_copied"]
        res = self.agent.process_report(tc1, consent_given=True)
        self.assertEqual(res["status"], "PROPOSED_FOR_APPROVAL")
        v = res["verification_report"]
        self.assertTrue(v["all_passed"])
        for audit in v["audits"]:
            self.assertEqual(audit["value_check"], "PASS")
            self.assertEqual(audit["unit_check"], "PASS")
            self.assertTrue(audit["source_cited"])

    def test_tc2_lab_range_override(self):
        tc2 = self.test_cases["TC2_lab_range_override"]
        res = self.agent.process_report(tc2, consent_given=True)
        glucose = next(t for t in res["processed_tests"] if t["test_key"] == "glucose_fasting")
        self.assertEqual(glucose["result"], 104.0)
        self.assertEqual(glucose["status"], "Normal")
        self.assertEqual(glucose["range_source_used"], "LAB_PRINTED")
        self.assertTrue(glucose["lab_range_differs_from_generic"])

    def test_tc3_ambiguous_ocr_prompts_user(self):
        tc3 = self.test_cases["TC3_ambiguous_ocr"]
        res = self.agent.process_report(tc3, consent_given=True)
        self.assertEqual(res["status"], "AWAITING_USER_CONFIRMATION")
        self.assertTrue(len(res["ambiguities"]) > 0)
        self.assertIn(1.0, res["ambiguities"][0]["candidate_options"])

        confirmed = self.agent.confirm_ambiguity(res["session_id"], {"creatinine_serum": 1.0})
        self.assertEqual(confirmed["status"], "PROPOSED_FOR_APPROVAL")
        creat = next(t for t in confirmed["processed_tests"] if t["test_key"] == "creatinine_serum")
        self.assertEqual(creat["result"], 1.0)
        self.assertEqual(creat["status"], "Normal")

    def test_tc4_critical_value_alert_no_diagnosis(self):
        tc4 = self.test_cases["TC4_critical_value"]
        res = self.agent.process_report(tc4, consent_given=True)
        self.assertEqual(res["status"], "PROPOSED_FOR_APPROVAL")
        self.assertTrue(len(res["critical_alerts"]) > 0)
        k_alert = next(a for a in res["critical_alerts"] if "Potassium" in a["test_name"])
        self.assertIn("Urgent", k_alert["advisory"])
        self.assertIn("clinician", k_alert["advisory"].lower())
        self.assertTrue(res["no_diagnosis_guarantee"])

    def test_permitted_action_human_approval(self):
        tc1 = self.test_cases["TC1_values_copied"]
        res = self.agent.process_report(tc1, consent_given=True)
        note_id = res["proposed_note"]["note_id"]
        app_res = self.agent.approve_and_save_note(note_id)
        self.assertEqual(app_res["status"], "SUCCESS_APPROVED_AND_SAVED")
        dup_res = self.agent.approve_and_save_note(note_id)
        self.assertEqual(dup_res["status"], "ALREADY_APPROVED")

if __name__ == "__main__":
    unittest.main()
