"""API integration tests for OmniPharma FastAPI endpoints.

Tests exercise the full HTTP stack with a seeded in-memory database.
"""

import pytest


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_health_has_status_field(self, client):
        data = client.get("/api/v1/health").json()
        assert "status" in data
        assert data["status"] in ("ok", "degraded")

    def test_health_has_dependencies(self, client):
        data = client.get("/api/v1/health").json()
        assert "dependencies" in data
        assert isinstance(data["dependencies"], list)


class TestPatientEndpoints:
    def test_list_patients_returns_list(self, client):
        resp = client.get("/api/v1/patients")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_get_patient_by_id(self, client):
        resp = client.get("/api/v1/patients/1")
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "patient_code" in data
        assert "g6pd_status" in data

    def test_get_nonexistent_patient_returns_404(self, client):
        resp = client.get("/api/v1/patients/99999")
        assert resp.status_code == 404

    def test_patient_search_by_name(self, client):
        # All patients were seeded; search should return results.
        resp = client.get("/api/v1/patients?q=Alice")
        assert resp.status_code == 200
        data = resp.json()
        assert any("Alice" in p["name"] for p in data)

    def test_get_patient_medications(self, client):
        resp = client.get("/api/v1/patients/1/medications")
        assert resp.status_code == 200
        data = resp.json()
        assert "current_prescriptions" in data
        assert "medication_history" in data


class TestMedicationEndpoints:
    def test_search_medications(self, client):
        resp = client.get("/api/v1/medications/search?q=metformin")
        assert resp.status_code == 200
        results = resp.json()
        assert isinstance(results, list)
        assert len(results) >= 1
        assert any("metformin" in m["canonical_name"] for m in results)

    def test_search_empty_query_returns_400(self, client):
        resp = client.get("/api/v1/medications/search?q=   ")
        assert resp.status_code == 400

    def test_get_medication_by_id(self, client):
        # Search first to get a real ID.
        meds = client.get("/api/v1/medications/search?q=warfarin").json()
        assert len(meds) >= 1
        med_id = meds[0]["id"]
        resp = client.get(f"/api/v1/medications/{med_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["canonical_name"] == "warfarin"

    def test_get_nonexistent_medication_returns_404(self, client):
        resp = client.get("/api/v1/medications/99999")
        assert resp.status_code == 404


class TestScreeningEndpoint:
    def test_ddi_warfarin_ibuprofen(self, client):
        """Patient 2 (Brian, no conditions) — warfarin + ibuprofen -> DDI."""
        resp = client.post(
            "/api/v1/screenings/interaction",
            json={"patient_id": 2, "medications": ["warfarin", "ibuprofen"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["patient_id"] == 2
        assert "findings" in data
        ddi_findings = [f for f in data["findings"] if f["type"] == "DRUG_DRUG_INTERACTION"]
        assert len(ddi_findings) >= 1

    def test_pregnancy_finding_for_pregnant_patient(self, client):
        """Patient 3 (Cynthia, PREGNANT) screened with isotretinoin -> PREGNANCY finding."""
        resp = client.post(
            "/api/v1/screenings/interaction",
            json={"patient_id": 3, "medications": ["isotretinoin"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        preg_findings = [f for f in data["findings"] if f["type"] == "PREGNANCY"]
        assert len(preg_findings) >= 1
        assert preg_findings[0]["severity"] == "CONTRAINDICATED"

    def test_renal_contraindication_for_ckd_patient(self, client):
        """Patient 6 (Felix, CKD, MODERATE_IMPAIRMENT) + metformin -> RENAL_CONTRAINDICATION."""
        resp = client.post(
            "/api/v1/screenings/interaction",
            json={"patient_id": 6, "medications": ["metformin"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        renal_findings = [f for f in data["findings"] if f["type"] == "RENAL_CONTRAINDICATION"]
        assert len(renal_findings) >= 1

    def test_status_clear_for_safe_combination(self, client):
        """Patient 2 + safe drug like omeprazole alone -> CLEAR or INCOMPLETE_CONTEXT."""
        resp = client.post(
            "/api/v1/screenings/interaction",
            json={"patient_id": 2, "medications": ["omeprazole"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("CLEAR", "INCOMPLETE_CONTEXT", "REVIEW_REQUIRED")

    def test_unresolved_drug_finding(self, client):
        """An unrecognised drug name -> UNRESOLVED_DRUG finding."""
        resp = client.post(
            "/api/v1/screenings/interaction",
            json={"patient_id": 1, "medications": ["xyzzy_fake_drug_12345"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        unresolved = [f for f in data["findings"] if f["type"] == "UNRESOLVED_DRUG"]
        assert len(unresolved) >= 1

    def test_nonexistent_patient_returns_404(self, client):
        resp = client.post(
            "/api/v1/screenings/interaction",
            json={"patient_id": 99999, "medications": ["warfarin"]},
        )
        assert resp.status_code == 404

    def test_empty_medication_list_returns_422(self, client):
        resp = client.post(
            "/api/v1/screenings/interaction",
            json={"patient_id": 1, "medications": []},
        )
        assert resp.status_code == 422

    def test_response_has_ruleset_version(self, client):
        resp = client.post(
            "/api/v1/screenings/interaction",
            json={"patient_id": 1, "medications": ["paracetamol"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "ruleset_version" in data
        assert data["ruleset_version"] != ""


class TestDeterministicDemoScenarios:
    """Prove the three required demo scenarios as per the spec."""

    def test_ddi_finding_produced(self, client):
        """Patient 10 (John Kiptoo, on warfarin) + ibuprofen -> DDI."""
        resp = client.post(
            "/api/v1/screenings/interaction",
            json={"patient_id": 10, "medications": ["warfarin", "ibuprofen"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        types = [f["type"] for f in data["findings"]]
        assert "DRUG_DRUG_INTERACTION" in types, f"Expected DDI but got: {types}"

    def test_pregnancy_finding_produced(self, client):
        """Patient 3 (Cynthia, PREGNANT) + isotretinoin -> PREGNANCY finding."""
        resp = client.post(
            "/api/v1/screenings/interaction",
            json={"patient_id": 3, "medications": ["isotretinoin"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        types = [f["type"] for f in data["findings"]]
        assert "PREGNANCY" in types, f"Expected PREGNANCY but got: {types}"

    def test_non_pregnancy_comorbidity_finding_produced(self, client):
        """Patient 6 (Felix, CKD/MODERATE_IMPAIRMENT) + metformin -> RENAL_CONTRAINDICATION."""
        resp = client.post(
            "/api/v1/screenings/interaction",
            json={"patient_id": 6, "medications": ["metformin"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        types = [f["type"] for f in data["findings"]]
        assert "RENAL_CONTRAINDICATION" in types, (
            f"Expected RENAL_CONTRAINDICATION but got: {types}"
        )

    def test_g6pd_finding_produced(self, client):
        """Patient 11 (Peter, G6PD DEFICIENT) + co-trimoxazole -> G6PD_CONTRAINDICATION."""
        resp = client.post(
            "/api/v1/screenings/interaction",
            json={"patient_id": 11, "medications": ["sulfamethoxazole-trimethoprim"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        types = [f["type"] for f in data["findings"]]
        assert "G6PD_CONTRAINDICATION" in types, f"Expected G6PD_CONTRAINDICATION but got: {types}"

    def test_respiratory_finding_produced(self, client):
        """Patient 5 (Esther, asthma) + ibuprofen -> RESPIRATORY_CONTRAINDICATION."""
        resp = client.post(
            "/api/v1/screenings/interaction",
            json={"patient_id": 5, "medications": ["ibuprofen"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        types = [f["type"] for f in data["findings"]]
        assert "RESPIRATORY_CONTRAINDICATION" in types, (
            f"Expected RESPIRATORY_CONTRAINDICATION but got: {types}"
        )

    def test_age_based_caution_produced(self, client):
        """Patient 12 (Mary Wambui, age 73) + diazepam -> AGE_BASED_CAUTION."""
        resp = client.post(
            "/api/v1/screenings/interaction",
            json={"patient_id": 12, "medications": ["diazepam"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        types = [f["type"] for f in data["findings"]]
        assert "AGE_BASED_CAUTION" in types, f"Expected AGE_BASED_CAUTION but got: {types}"

    def test_allergy_cross_reactivity_produced(self, client):
        """Patient 10 (John, penicillin allergy) + amoxicillin -> ALLERGY_CROSS_REACTIVITY."""
        resp = client.post(
            "/api/v1/screenings/interaction",
            json={"patient_id": 10, "medications": ["amoxicillin"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        types = [f["type"] for f in data["findings"]]
        assert "ALLERGY_CROSS_REACTIVITY" in types, (
            f"Expected ALLERGY_CROSS_REACTIVITY but got: {types}"
        )
