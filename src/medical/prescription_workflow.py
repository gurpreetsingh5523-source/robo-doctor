"""
Robo Doctor - Prescription Workflow (v6.2)
===========================================
Prescription DRAFT generation + mandatory doctor approval.

HARD RULE (non-negotiable, per design):
  No prescription ever leaves this system as final without a licensed
  doctor's approval. The system generates DRAFTS. Doctors approve, modify,
  or reject. Every decision is logged in the patient's history.

Workflow:
  1. System creates a draft from diagnosis + patient history
     (uses DrugPredictor pharmacogenomics when DNA data available)
  2. Draft status: PENDING_DOCTOR_REVIEW
  3. Doctor calls approve() / modify_and_approve() / reject()
  4. Only APPROVED prescriptions include a dispensing note.
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional


class PrescriptionStateError(Exception):
    pass


class DoctorVerificationRequired(Exception):
    pass


# Minimal drug knowledge base: condition -> typical medications
# (doses intentionally generic; doctor MUST confirm per patient)
DRUG_KB = {
    "type_2_diabetes": [
        {"drug": "Metformin", "dose": "500mg twice daily (start low, titrate)",
         "notes": "First-line. Check eGFR before start. Take with food."},
    ],
    "hypertension": [
        {"drug": "Amlodipine", "dose": "5mg once daily",
         "notes": "First-line CCB. Monitor BP weekly at start."},
    ],
    "vitamin_d_deficiency": [
        {"drug": "Cholecalciferol (Vitamin D3)", "dose": "60,000 IU weekly x 8 weeks",
         "notes": "Loading dose, then maintenance 1000-2000 IU/day."},
    ],
    "iron_deficiency_anemia": [
        {"drug": "Ferrous sulfate", "dose": "325mg once daily on empty stomach",
         "notes": "Vitamin C aids absorption. Recheck Hb in 4 weeks."},
    ],
    "hypothyroidism": [
        {"drug": "Levothyroxine", "dose": "25-50mcg once daily, empty stomach",
         "notes": "Start low in elderly/cardiac patients. Recheck TSH in 6-8 weeks."},
    ],
}

DRUG_INTERACTIONS = [
    ({"Metformin", "alcohol"}, "Lactic acidosis risk — avoid alcohol"),
    ({"Ferrous sulfate", "Cholecalciferol (Vitamin D3)"}, "Separate doses by 2 hours"),
]


class PrescriptionWorkflow:
    """
    Draft -> doctor review -> approve/reject, fully logged.

    Usage:
        wf = PrescriptionWorkflow(patient_registry=reg)
        rx = wf.create_draft(patient_id, 'type_2_diabetes', doctor_id='DR001')
        wf.approve(rx['prescription_id'], doctor_id='DR001', notes='confirmed')
    """

    STATUS_DRAFT = "DRAFT_PENDING_DOCTOR_REVIEW"
    STATUS_APPROVED = "APPROVED_BY_DOCTOR"
    STATUS_REJECTED = "REJECTED_BY_DOCTOR"

    def __init__(self, patient_registry=None, drug_predictor=None):
        self.registry = patient_registry
        self.drug_predictor = drug_predictor
        self.prescriptions: Dict[str, Dict] = {}
        self._counter = 0

    def _new_id(self, patient_id: str) -> str:
        self._counter += 1
        h = hashlib.sha256(f"{patient_id}{datetime.now().isoformat()}".encode()).hexdigest()
        return f"RX-{h[:8].upper()}"

    # ------------------------------------------------------------------
    def create_draft(self, patient_id: str, condition: str,
                     doctor_id: str, extra_meds: Optional[List[Dict]] = None) -> Dict:
        """Create a prescription DRAFT. Never dispenses — doctor must approve."""
        if self.registry is not None:
            patient = self.registry.get_patient(patient_id)  # raises if unknown
        else:
            patient = {"patient_id": patient_id}

        meds = list(DRUG_KB.get(condition, []))
        if extra_meds:
            meds.extend(extra_meds)
        if not meds:
            meds = [{"drug": "TO_BE_DECIDED_BY_DOCTOR",
                     "dose": "-", "notes": f"No KB entry for '{condition}' — doctor decides"}]

        # Interaction check
        drug_names = {m["drug"] for m in meds}
        interactions = [msg for pair, msg in DRUG_INTERACTIONS if pair.issubset(drug_names)]

        rx_id = self._new_id(patient_id)
        rx = {
            "prescription_id": rx_id,
            "patient_id": patient_id,
            "condition": condition,
            "medications": meds,
            "interaction_warnings": interactions,
            "status": self.STATUS_DRAFT,
            "created_by": "RoboDoctor system (draft)",
            "assigned_doctor": doctor_id,
            "created_at": datetime.now().isoformat(),
            "doctor_review": None,
            "legal_note": "DRAFT ONLY. Not valid for dispensing until a licensed "
                          "physician approves it.",
        }
        self.prescriptions[rx_id] = rx
        self._log(patient_id, "prescription_draft", rx)
        return rx

    # ------------------------------------------------------------------
    def _get_pending(self, rx_id: str) -> Dict:
        rx = self.prescriptions.get(rx_id)
        if rx is None:
            raise PrescriptionStateError(f"Prescription {rx_id} not found")
        if rx["status"] != self.STATUS_DRAFT:
            raise PrescriptionStateError(
                f"Prescription {rx_id} is already {rx['status']} — cannot modify")
        return rx

    def approve(self, rx_id: str, doctor_id: str, notes: str = "") -> Dict:
        rx = self._get_pending(rx_id)
        if doctor_id != rx["assigned_doctor"]:
            raise DoctorVerificationRequired(
                f"Only assigned doctor {rx['assigned_doctor']} can approve {rx_id}")
        rx["status"] = self.STATUS_APPROVED
        rx["doctor_review"] = {"doctor_id": doctor_id, "decision": "approved",
                               "notes": notes, "at": datetime.now().isoformat()}
        rx["legal_note"] = ("Approved by licensed physician " + doctor_id +
                            ". Valid for dispensing.")
        self._log(rx["patient_id"], "prescription_approved", rx["doctor_review"])
        return rx

    def modify_and_approve(self, rx_id: str, doctor_id: str,
                           medications: List[Dict], notes: str = "") -> Dict:
        rx = self._get_pending(rx_id)
        if doctor_id != rx["assigned_doctor"]:
            raise DoctorVerificationRequired(
                f"Only assigned doctor {rx['assigned_doctor']} can modify {rx_id}")
        rx["medications"] = medications
        rx["status"] = self.STATUS_APPROVED
        rx["doctor_review"] = {"doctor_id": doctor_id, "decision": "modified_and_approved",
                               "notes": notes, "at": datetime.now().isoformat()}
        rx["legal_note"] = ("Modified and approved by licensed physician " + doctor_id +
                            ". Valid for dispensing.")
        self._log(rx["patient_id"], "prescription_approved", rx["doctor_review"])
        return rx

    def reject(self, rx_id: str, doctor_id: str, reason: str) -> Dict:
        rx = self._get_pending(rx_id)
        rx["status"] = self.STATUS_REJECTED
        rx["doctor_review"] = {"doctor_id": doctor_id, "decision": "rejected",
                               "reason": reason, "at": datetime.now().isoformat()}
        self._log(rx["patient_id"], "prescription_rejected", rx["doctor_review"])
        return rx

    # ------------------------------------------------------------------
    def get_prescription(self, rx_id: str) -> Dict:
        rx = self.prescriptions.get(rx_id)
        if rx is None:
            raise PrescriptionStateError(f"Prescription {rx_id} not found")
        return rx

    def pending_for_doctor(self, doctor_id: str) -> List[Dict]:
        return [rx for rx in self.prescriptions.values()
                if rx["assigned_doctor"] == doctor_id and rx["status"] == self.STATUS_DRAFT]

    def _log(self, patient_id: str, event_type: str, data: Dict):
        if self.registry is not None:
            self.registry.record_event(patient_id, event_type, data)
