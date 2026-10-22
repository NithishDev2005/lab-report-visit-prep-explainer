# Lab Report Visit-Prep Explainer

An agentic clinical assistant that parses patient lab reports to generate plain-language biomarker explanations and structured doctor discussion questions without issuing medical diagnoses.

Developed by **Team smart_Builders** for the **Ziro.Digital Agentic AI Hackathon 2026** (Healthcare & Wellness AI Track).

---

## Why This Exists (Engineering Context)

Patients frequently receive laboratory blood panels days before meeting their physicians. Standard search engines often return alarming, out-of-context medical diagnoses, while generic LLMs are prone to clinical hallucination. 

This agent solves three specific real-world problems:
1. **Instrument Calibration Priority:** Different laboratories use different reagent lots and analyzers (e.g., Hexokinase vs. Glucose Oxidase). The agent enforces the lab's printed range as ground truth, ignoring generic population averages.
2. **OCR Uncertainty Intercepts:** Scanned documents frequently suffer from blur or artifacts around decimal points (e.g., \1.0\ vs \10\). Rather than guessing, the agent suspends execution and requests patient confirmation.
3. **Clinical Escalation without Diagnosis:** For life-threatening results (e.g., Potassium > 6.2 mmol/L), the agent provides an immediate emergency advisory without assigning diagnostic labels.

---

## Architecture & State Machine

\\\
[ Raw Report (PDF / Synthetic) ]
              ¦
              ?
   [ 1. Ingestion & Tokenizer ] --? Extracts values, units, printed analyzer ranges
              ¦
              ?
   [ 2. Ambiguity Guardrail ] ----? Checks OCR token confidence (< 0.70)
              ¦                    +-- If unsure (e.g. 1.0 vs 10) --? Pause & prompt user
              ?
   [ 3. Decision Engine ] --------? 1. Evaluate against printed lab range (overrides generic)
              ¦                     2. Check critical physiological thresholds (urgent flags)
              ¦                     3. Retrieve MedlinePlus/NIH context definitions
              ¦                     4. AST/Regex sanitizer strips diagnostic language
              ?
   [ 4. Dual Verification ] ------? Programmatic audit: raw input vs parsed output (zero drift)
              ¦
              ?
   [ 5. Human-in-the-Loop Action ] ? User reviews prep note --? Explicit click stores to SQLite
\\\

---

## Official Test Cases & Verification Evidence

All 4 official hackathon scenarios pass deterministically:

| Test Case | Scenario | Expected Outcome | Observed Result | Status |
|:---|:---|:---|:---|:---|
| **TC1** | Values Copied | Exact match to report with units | Value variance: 0.00%. All units and ranges preserved. | **PASS** |
| **TC2** | Range Discrepancy | Lab-specific printed range takes priority | Fasting Glucose 104 mg/dL evaluated as Normal against lab range (75-110 mg/dL), ignoring generic range (70-99 mg/dL). | **PASS** |
| **TC3** | OCR Ambiguity | Agent halts and asks user to confirm | Low-confidence token (\1.0*\) pauses state machine; user confirms \1.0 mg/dL\ before note generation. | **PASS** |
| **TC4** | Critical Value | Urgent clinician warning with zero diagnosis | Potassium 6.8 mmol/L flags urgent clinician advisory; zero diagnostic strings generated. | **PASS** |

---

## Local Setup & Reproduction

\\\ash
# 1. Clone repository
git clone https://github.com/NithishDev2005/lab-report-visit-prep-explainer.git
cd lab-report-visit-prep-explainer

# 2. Virtual environment setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install requirements
pip install -r requirements.txt

# 4. Run automated test suite
python tests/test_official_cases.py -v

# 5. Run CLI scenario verification runner
python run_demo.py

# 6. Launch Web Dashboard
streamlit run app/ui/streamlit_app.py
\\\

---

## Tech Stack

- **Runtime:** Python 3.10+
- **Agent Orchestration:** Custom State Machine with explicit human-in-the-loop transition states
- **Interface:** Streamlit
- **Document Ingestion:** PyMuPDF / ReportLab
- **Grounding Database:** NIH MedlinePlus Clinical Reference Corpus
- **Persistence:** SQLite3 (audit logging and approved note storage)

---

## Team & Hackathon Details

- **Team:** smart_Builders
- **Team Leader:** Nithish Kumar
- **Event:** Agentic AI Hackathon 2026 (Ziro.Digital)
- **Track:** Healthcare & Wellness AI
