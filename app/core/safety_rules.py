import re
from typing import Dict, Any, Tuple, Optional

BANNED_PATTERNS = [
    r"\byou have\b", r"\byou are suffering from\b", r"\bdiagnosed with\b",
    r"\bdiagnosis:\b", r"\bdiabetic\b", r"\bkidney failure\b", r"\bcardiac arrest\b"
]

def parse_range(range_str: str) -> Tuple[Optional[float], Optional[float]]:
    if not range_str:
        return None, None
    m = re.findall(r"[-+]?\d*\.\d+|\d+", range_str)
    if len(m) >= 2:
        return float(m[0]), float(m[1])
    return None, None

def evaluate_test_result(result: Optional[float], printed_range: str, grounded_info: Dict[str, Any]) -> Dict[str, Any]:
    if result is None:
        return {
            "status": "UNCERTAIN",
            "is_critical": False,
            "critical_message": None,
            "range_source_used": "LAB_PRINTED",
            "lab_range_differs_from_generic": False,
            "reason": "Value is ambiguous or requires confirmation."
        }
    
    lab_min, lab_max = parse_range(printed_range)
    generic = grounded_info.get("generic_reference_range")
    gen_min = generic.get("min") if generic else None
    gen_max = generic.get("max") if generic else None

    lab_differs = False
    if lab_min is not None and gen_min is not None:
        if abs(lab_min - gen_min) > 0.01 or abs(lab_max - gen_max) > 0.01:
            lab_differs = True

    status = "Normal"
    if lab_min is not None and lab_max is not None:
        if result < lab_min:
            status = "Low"
        elif result > lab_max:
            status = "High"

    is_critical = False
    critical_message = None
    crit = grounded_info.get("critical_thresholds")
    if crit:
        c_low = crit.get("low")
        c_high = crit.get("high")
        if c_low is not None and result <= c_low:
            is_critical = True
            status = "CRITICAL_LOW"
            critical_message = f"Urgent: Observed value ({result}) is critically below safe baseline. Please contact your clinician or seek urgent medical attention immediately. (No diagnosis is made)."
        elif c_high is not None and result >= c_high:
            is_critical = True
            status = "CRITICAL_HIGH"
            critical_message = f"Urgent: Observed value ({result}) is critically above safe baseline. Please contact your clinician or seek urgent medical attention immediately. (No diagnosis is made)."

    return {
        "status": status,
        "is_critical": is_critical,
        "critical_message": critical_message,
        "range_source_used": "LAB_PRINTED",
        "lab_range_differs_from_generic": lab_differs,
        "lab_range": {"min": lab_min, "max": lab_max, "raw": printed_range},
        "generic_range": {"min": gen_min, "max": gen_max}
    }

def sanitize_and_audit_no_diagnosis(text: str) -> Tuple[str, bool]:
    clean = text
    passed = True
    for p in BANNED_PATTERNS:
        if re.search(p, clean, re.IGNORECASE):
            passed = False
            clean = re.sub(p, "[Observation noted - consult physician for diagnosis]", clean, flags=re.IGNORECASE)
    return clean, passed
