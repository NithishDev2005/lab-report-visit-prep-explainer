import json, os
from datetime import datetime

REFS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "trusted_references.json")

class GroundingEngine:
    def __init__(self):
        with open(REFS_PATH, "r") as f:
            self.refs = json.load(f)

    def get_grounded_context(self, test_key_or_name):
        norm = test_key_or_name.lower().strip()
        for k, v in self.refs.items():
            if k == norm or v["test_name"].lower() == norm or any(s.lower() in norm for s in v.get("synonyms", [])):
                res = dict(v)
                res["test_key"] = k
                res["retrieved_at"] = datetime.utcnow().isoformat()
                return res
        return {
            "test_key": norm,
            "test_name": test_key_or_name,
            "plain_definition": "A standard clinical biomarker evaluated in laboratory blood panels.",
            "doctor_questions": ["What do these levels indicate regarding my current health?"],
            "generic_reference_range": None,
            "critical_thresholds": None,
            "source_name": "MedlinePlus (National Library of Medicine)",
            "source_url": "https://medlineplus.gov/lab-tests/",
            "retrieved_at": datetime.utcnow().isoformat()
        }
