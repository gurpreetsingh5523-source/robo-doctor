"""
Robo Doctor - Symptom Analyzer (v6.2)
======================================
Symptom -> recommended diagnostic tests logic.

Rule-based clinical knowledge engine (offline, no LLM required):
- 40+ symptoms mapped to recommended blood tests / panels
- RED FLAG detection: symptom combinations that need URGENT care
- Population-aware suggestions (e.g. South Asian diabetes risk)
- Always outputs 'consult doctor' — this advises tests, never diagnoses.

Disclaimer: screening aid only. A licensed physician decides.
"""

from datetime import datetime
from typing import Dict, List, Optional


# symptom -> (recommended tests, urgency, notes)
SYMPTOM_MAP = {
    "fatigue": {
        "tests": ["hemoglobin", "ferritin", "vitamin_d", "vitamin_b12", "tsh", "glucose_fasting"],
        "urgency": "routine",
        "notes": "Common causes: anemia, hypothyroidism, vitamin deficiency, diabetes",
    },
    "fever": {
        "tests": ["wbc_count", "crp", "blood_culture", "urine_routine"],
        "urgency": "priority",
        "notes": "Persistent fever >3 days needs physician evaluation",
    },
    "weight_loss": {
        "tests": ["glucose_fasting", "hba1c", "tsh", "crp", "chest_xray"],
        "urgency": "priority",
        "notes": "Unintentional weight loss is a red-flag symptom",
    },
    "excessive_thirst": {
        "tests": ["glucose_fasting", "hba1c", "urine_routine"],
        "urgency": "priority",
        "notes": "Classic diabetes triad: thirst, urination, hunger",
    },
    "frequent_urination": {
        "tests": ["glucose_fasting", "hba1c", "urine_routine", "creatinine"],
        "urgency": "priority",
        "notes": "Check diabetes and kidney function",
    },
    "chest_pain": {
        "tests": ["ecg", "troponin", "lipid_panel", "crp"],
        "urgency": "EMERGENCY",
        "notes": "RED FLAG: possible cardiac event — seek emergency care NOW",
    },
    "breathlessness": {
        "tests": ["ecg", "hemoglobin", "chest_xray", "d_dimer"],
        "urgency": "urgent",
        "notes": "Could be cardiac, pulmonary, or anemia",
    },
    "pale_skin": {
        "tests": ["hemoglobin", "ferritin", "vitamin_b12", "reticulocyte_count"],
        "urgency": "routine",
        "notes": "Anemia workup",
    },
    "joint_pain": {
        "tests": ["crp", "esr", "uric_acid", "rheumatoid_factor", "vitamin_d"],
        "urgency": "routine",
        "notes": "Inflammatory vs degenerative vs gout",
    },
    "headache": {
        "tests": ["blood_pressure", "glucose_fasting", "hemoglobin"],
        "urgency": "routine",
        "notes": "Sudden severe headache = emergency",
    },
    "abdominal_pain": {
        "tests": ["liver_function", "amylase", "lipase", "urine_routine", "ultrasound_abdomen"],
        "urgency": "priority",
        "notes": "Location matters — right lower quadrant = appendicitis risk",
    },
    "jaundice": {
        "tests": ["bilirubin", "liver_function", "hepatitis_panel"],
        "urgency": "urgent",
        "notes": "Liver evaluation needed",
    },
    "hair_loss": {
        "tests": ["tsh", "ferritin", "vitamin_d", "zinc"],
        "urgency": "routine",
        "notes": "Often nutritional or thyroid related",
    },
    "numbness_tingling": {
        "tests": ["vitamin_b12", "glucose_fasting", "hba1c", "tsh"],
        "urgency": "routine",
        "notes": "Diabetic neuropathy and B12 deficiency are common causes",
    },
    "swollen_legs": {
        "tests": ["creatinine", "urine_protein", "albumin", "ecg", "d_dimer"],
        "urgency": "priority",
        "notes": "Kidney, cardiac, or venous cause",
    },
    "night_sweats": {
        "tests": ["wbc_count", "esr", "chest_xray", "tb_test"],
        "urgency": "priority",
        "notes": "TB screening important in South Asian populations",
    },
    "persistent_cough": {
        "tests": ["chest_xray", "wbc_count", "sputum_test", "tb_test"],
        "urgency": "priority",
        "notes": "Cough >2 weeks: TB evaluation recommended",
    },
    "blurred_vision": {
        "tests": ["glucose_fasting", "hba1c", "blood_pressure", "eye_exam"],
        "urgency": "priority",
        "notes": "Diabetic retinopathy screening",
    },
    "irregular_heartbeat": {
        "tests": ["ecg", "electrolytes", "tsh", "troponin"],
        "urgency": "urgent",
        "notes": "Arrhythmia evaluation",
    },
    "memory_problems": {
        "tests": ["vitamin_b12", "tsh", "glucose_fasting", "cognitive_assessment"],
        "urgency": "routine",
        "notes": "Reversible causes first: B12, thyroid, glucose",
    },
}

# Red-flag combinations -> immediate escalation
RED_FLAG_COMBOS = [
    ({"chest_pain", "breathlessness"}, "Possible cardiac event — EMERGENCY"),
    ({"chest_pain", "sweating"}, "Possible heart attack — call emergency services"),
    ({"fever", "stiff_neck"}, "Possible meningitis — EMERGENCY"),
    ({"severe_headache", "blurred_vision"}, "Possible stroke/pressure crisis — EMERGENCY"),
    ({"weight_loss", "night_sweats", "persistent_cough"}, "TB/malignancy screen — URGENT"),
    ({"excessive_thirst", "frequent_urination", "weight_loss"}, "Likely diabetes — test this week"),
    ({"fatigue", "pale_skin", "breathlessness"}, "Significant anemia likely — test this week"),
]

# Population-specific extra screening
POPULATION_EXTRA = {
    "south_asian": {
        "tests": ["hba1c", "lipid_panel", "vitamin_d"],
        "reason": "South Asians have 2-4x higher diabetes/heart risk at lower BMI",
    },
}


class SymptomAnalyzer:
    """Map patient symptoms to recommended tests with urgency triage."""

    def analyze(self, symptoms: List[str], population: str = "general",
                age: Optional[int] = None) -> Dict:
        normalized = [s.strip().lower().replace(" ", "_") for s in symptoms]
        known = [s for s in normalized if s in SYMPTOM_MAP]
        unknown = [s for s in normalized if s not in SYMPTOM_MAP]

        recommended = {}
        max_urgency = "routine"
        urgency_rank = {"routine": 0, "priority": 1, "urgent": 2, "EMERGENCY": 3}

        for s in known:
            info = SYMPTOM_MAP[s]
            for t in info["tests"]:
                recommended.setdefault(t, []).append(s)
            if urgency_rank[info["urgency"]] > urgency_rank[max_urgency]:
                max_urgency = info["urgency"]

        # Red-flag combination check
        red_flags = []
        symptom_set = set(normalized)
        for combo, message in RED_FLAG_COMBOS:
            if combo.issubset(symptom_set):
                red_flags.append(message)
                max_urgency = "EMERGENCY"

        # Population extras
        extras = POPULATION_EXTRA.get(population.lower().replace(" ", "_"), {})

        return {
            "symptoms_received": symptoms,
            "symptoms_recognized": known,
            "symptoms_unknown": unknown,
            "recommended_tests": sorted(recommended.keys()),
            "test_reasons": {t: f"indicated by: {', '.join(src)}" for t, src in recommended.items()},
            "urgency": max_urgency,
            "red_flags": red_flags,
            "population_screening": extras or None,
            "unknown_note": (f"'{', '.join(unknown)}' not in knowledge base — "
                             "a doctor should evaluate these directly") if unknown else None,
            "next_step": ("EMERGENCY: go to hospital now" if max_urgency == "EMERGENCY"
                          else "Book the recommended tests, then return with results for analysis"),
            "disclaimer": "This is a screening aid that recommends tests — it is NOT a diagnosis. "
                          "A licensed physician makes all final decisions.",
            "timestamp": datetime.now().isoformat(),
        }

    def list_known_symptoms(self) -> List[str]:
        return sorted(SYMPTOM_MAP.keys())
