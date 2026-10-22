class VerificationEngine:
    def verify_extraction(self, original_tests, extracted_tests, grounded_data):
        audits = []
        all_passed = True
        for orig in original_tests:
            name = orig.get("test_name")
            key = orig.get("test_key")
            match = next((t for t in extracted_tests if t.get("test_key") == key or t.get("test_name") == name), None)
            if not match:
                audits.append({"test_name": name, "status": "FAIL", "reason": "Missing extracted item"})
                all_passed = False
                continue

            orig_val = orig.get("result")
            ext_val = match.get("result")
            is_ambiguous = orig.get("is_ambiguous") or match.get("is_ambiguous")

            if is_ambiguous:
                val_check = "PENDING_CONFIRMATION"
            elif orig_val is not None and ext_val is not None:
                val_check = "PASS" if abs(float(orig_val) - float(ext_val)) < 1e-4 else "FAIL"
            else:
                val_check = "PASS" if orig_val == ext_val else "FAIL"

            orig_unit = str(orig.get("unit", "")).strip().lower()
            ext_unit = str(match.get("unit", "")).strip().lower()
            unit_check = "PASS" if orig_unit == ext_unit else "FAIL"

            g = grounded_data.get(key, {})
            has_source = bool(g.get("source_url") and g.get("source_name"))
            source_check = "PASS" if has_source else "FAIL"

            item_status = "PASS" if (val_check == "PASS" and unit_check == "PASS" and source_check == "PASS") else ("PENDING" if is_ambiguous else "FAIL")
            if item_status == "FAIL":
                all_passed = False

            audits.append({
                "test_name": name,
                "input_value": orig_val if not is_ambiguous else orig.get("raw_ocr_string", "1.0*"),
                "extracted_value": ext_val if not is_ambiguous else "Awaiting Confirmation",
                "value_check": val_check,
                "input_unit": orig.get("unit"),
                "extracted_unit": match.get("unit"),
                "unit_check": unit_check,
                "source_cited": has_source,
                "source_url": g.get("source_url"),
                "overall_status": item_status
            })

        return {"all_passed": all_passed, "audits": audits}
