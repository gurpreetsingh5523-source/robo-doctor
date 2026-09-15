"""
Robo Doctor - Chat Engine (v6.2)
=================================
Type commands in plain English; get real work done.

Dual brain design:
1. OFFLINE RULE PARSER (default, always works) - recognizes command intents
   for the daily clinic flow: register, symptoms, blood, history,
   prescription draft, approve, help. Zero dependencies, zero cost.
2. LLM BRAIN (optional) - when an OpenAI-compatible LLM is configured
   (Qwen / DeepSeek / OpenRouter / local Ollama), free-text messages that
   the parser cannot handle are interpreted by the LLM into structured
   actions. If the LLM fails or is absent, the engine HONESTLY says what
   it understands instead of guessing.

Safety: chat goes through the same gates as the API - consent, ethics,
doctor approval. The chat can NEVER approve a prescription itself.
"""

import re
import json
from datetime import datetime
from typing import Dict, Optional, List


HELP_TEXT = """I understand these commands (English):
• register patient age 52 male [population south_asian] [consent genomic]
• symptoms: chest pain, fatigue [for patient AMRIT-XXXX]
• blood: glucose_fasting=110 hba1c=6.2 [for AMRIT-XXXX]
• history of AMRIT-XXXX
• draft prescription for AMRIT-XXXX condition type_2_diabetes doctor DR_SMITH
• approve RX-XXXXXXXX doctor DR_SMITH
• pending prescriptions for DR_SMITH
• status / help
Type naturally — if an LLM is connected (Ollama/API), I'll understand more."""


class ChatEngine:
    def __init__(self, patient_registry=None, symptom_analyzer=None,
                 blood_analyzer=None, prescription_workflow=None,
                 llm=None, health_advisor=None):
        self.registry = patient_registry
        self.symptoms = symptom_analyzer
        self.blood = blood_analyzer
        self.rx = prescription_workflow
        self.llm = llm
        self.advisor = health_advisor

    # ------------------------------------------------------------------
    def handle(self, message: str, session: Optional[Dict] = None) -> Dict:
        """Main entry. session carries last patient_id / doctor_id context."""
        session = session or {}
        text = message.strip()
        lower = text.lower()

        try:
            if lower in ("help", "?", "commands", "ki kar sakde ho"):
                return self._reply(HELP_TEXT)

            if lower.startswith("status"):
                return self._reply(self._status())

            m = re.search(r"register patient", lower)
            if m:
                return self._cmd_register(text)

            if lower.startswith("symptom") or "symptoms:" in lower:
                return self._cmd_symptoms(text, session)

            if lower.startswith("blood") or "blood:" in lower:
                return self._cmd_blood(text, session)

            m = re.search(r"history of (amrit-\w+)", lower)
            if m:
                return self._cmd_history(m.group(1).upper())

            if "draft prescription" in lower:
                return self._cmd_draft(text, session)

            m = re.search(r"approve (rx-\w+)", lower)
            if m:
                return self._cmd_approve(m.group(1).upper(), text, session)

            m = re.search(r"pending prescriptions for (\w+)", lower)
            if m:
                return self._cmd_pending(m.group(1).upper())

            # ---- LLM brain for free text (only if configured) ----
            if self.llm is not None and self.llm.configured:
                return self._llm_handle(text, session)

            return self._reply(
                "I didn't understand that, and no LLM is connected for free-text "
                "understanding. " + HELP_TEXT,
                understood=False)
        except Exception as e:
            return self._reply(f"Error: {e}", error=True)

    # ------------------------------------------------------------------
    def _reply(self, text: str, understood: bool = True,
               error: bool = False, data: Optional[Dict] = None) -> Dict:
        return {"reply": text, "understood": understood, "error": error,
                "data": data, "timestamp": datetime.now().isoformat()}

    def _status(self) -> str:
        parts = []
        if self.registry is not None:
            s = self.registry.registry_stats()
            parts.append(f"Patients: {s['registered_patients']}, events: {s['total_events']}")
        if self.llm is not None:
            parts.append("LLM: " + ("connected (" + self.llm.model + ")"
                                    if self.llm.configured else "not configured (offline rules only)"))
        return "Robo Doctor status — " + " | ".join(parts)

    # ------------------------------------------------------------------
    def _patient_from(self, text: str, session: Dict) -> Optional[str]:
        m = re.search(r"(amrit-\w+)", text.lower())
        if m:
            return m.group(1).upper()
        return session.get("patient_id")

    def _cmd_register(self, text: str) -> Dict:
        lower = text.lower()
        age_m = re.search(r"age (\d+)|(\d+)\s*(?:year|yr|y\.o)", lower)
        age = int(age_m.group(1) or age_m.group(2)) if age_m else None
        sex = "M" if re.search(r"\bmale\b|\bm\b", lower) else (
            "F" if re.search(r"\bfemale\b|\bf\b", lower) else None)
        if age is None or sex is None:
            return self._reply("To register, I need age and sex. Example: "
                               "'register patient age 52 male'", understood=False)
        pop_m = re.search(r"population (\w+)", lower)
        genomic = "consent genomic" in lower or "genomic consent" in lower
        pid = self.registry.register_patient(
            age=age, sex=sex,
            population=(pop_m.group(1) if pop_m else "general"),
            consent_general=True, consent_genomic=genomic)
        return self._reply(
            f"✅ Patient registered: **{pid}** (age {age}, {sex}, "
            f"genomic consent: {'yes' if genomic else 'no'}). "
            f"All future tests will link to this ID.",
            data={"patient_id": pid})

    def _cmd_symptoms(self, text: str, session: Dict) -> Dict:
        m = re.search(r"symptoms?:\s*(.+)", text, re.I)
        if not m:
            return self._reply("Format: symptoms: chest pain, fatigue", understood=False)
        symptoms = [s.strip() for s in re.split(r",| and ", m.group(1)) if s.strip()]
        pid = self._patient_from(text, session)
        result = self.symptoms.analyze(symptoms)
        if pid and self.registry is not None:
            try:
                self.registry.record_event(pid, "symptom_report", {
                    "symptoms": symptoms, "urgency": result["urgency"],
                    "recommended_tests": result["recommended_tests"]})
                result["recorded_to_patient"] = pid
            except Exception:
                pass
        lines = [f"Urgency: **{result['urgency']}**"]
        if result["red_flags"]:
            lines.append("🚩 Red flags: " + "; ".join(result["red_flags"]))
        lines.append("Recommended tests: " + ", ".join(result["recommended_tests"][:8]))
        lines.append(result["next_step"])
        if result.get("recorded_to_patient"):
            lines.append(f"(Recorded to {pid})")
        return self._reply("\n".join(lines), data=result)

    def _cmd_blood(self, text: str, session: Dict) -> Dict:
        pairs = re.findall(r"(\w+)\s*=\s*([\d.]+)", text)
        if not pairs:
            return self._reply("Format: blood: glucose_fasting=110 hba1c=6.2",
                               understood=False)
        panel = {k: float(v) for k, v in pairs}
        pid = self._patient_from(text, session)
        results = self.blood.analyze_panel(panel)
        lines = []
        worst = "normal"
        rank = {"normal": 0, "borderline": 1, "high": 2, "critical": 3}
        for name, r in results.items():
            lvl = r.risk_level.value
            if rank[lvl] > rank[worst]:
                worst = lvl
            icon = {"critical": "🔴", "high": "🟠", "borderline": "🟡"}.get(lvl, "🟢")
            lines.append(f"{icon} {name}: {r.value} {r.unit} — {lvl} "
                         f"(range {r.reference_range[0]}-{r.reference_range[1]})")
        if pid and self.registry is not None:
            try:
                self.registry.record_event(pid, "blood_panel", panel)
                lines.append(f"(Recorded to {pid})")
            except Exception:
                pass
        if worst == "critical":
            lines.append("⚠️ CRITICAL values present — doctor review advised NOW.")
        return self._reply("\n".join(lines))

    def _cmd_history(self, pid: str) -> Dict:
        summary = self.registry.patient_summary(pid)
        p = summary["patient"]
        lines = [f"Patient {pid}: age {p['age']}, {p['sex']}, {p['population']}",
                 f"Events: {summary['total_events']} — {summary['event_counts']}",
                 f"First visit: {summary['first_visit']}",
                 f"Last visit: {summary['last_visit']}"]
        return self._reply("\n".join(lines), data=summary)

    def _cmd_draft(self, text: str, session: Dict) -> Dict:
        pid = self._patient_from(text, session)
        cond_m = re.search(r"condition ([\w_]+)", text.lower())
        doc_m = re.search(r"doctor (\w+)", text.lower())
        if not (pid and cond_m and doc_m):
            return self._reply("Format: draft prescription for AMRIT-XXXX "
                               "condition type_2_diabetes doctor DR_SMITH",
                               understood=False)
        rx = self.rx.create_draft(pid, cond_m.group(1), doc_m.group(1).upper())
        meds = ", ".join(m["drug"] for m in rx["medications"])
        return self._reply(
            f"📋 Draft **{rx['prescription_id']}** created ({meds}).\n"
            f"Status: {rx['status']} — only {rx['assigned_doctor']} can approve.",
            data=rx)

    def _cmd_approve(self, rx_id: str, text: str, session: Dict) -> Dict:
        doc_m = re.search(r"doctor (\w+)", text.lower())
        doctor = doc_m.group(1).upper() if doc_m else session.get("doctor_id")
        if not doctor:
            return self._reply("Format: approve RX-XXXXXXXX doctor DR_SMITH",
                               understood=False)
        rx = self.rx.approve(rx_id, doctor)
        return self._reply(f"✅ {rx_id} approved by {doctor}. Valid for dispensing.")

    def _cmd_pending(self, doctor: str) -> Dict:
        pending = self.rx.pending_for_doctor(doctor)
        if not pending:
            return self._reply(f"No pending prescriptions for {doctor}.")
        lines = [f"Pending for {doctor}:"]
        for rx in pending:
            lines.append(f"• {rx['prescription_id']} — {rx['condition']} "
                         f"(patient {rx['patient_id']})")
        return self._reply("\n".join(lines))

    # ------------------------------------------------------------------
    def _llm_handle(self, text: str, session: Dict) -> Dict:
        """Let the configured LLM interpret free text into an action."""
        prompt = (
            "You are the command interpreter for Robo Doctor clinic software. "
            "Map the user's message to ONE action as compact JSON:\n"
            '{"action":"register|symptoms|blood|history|draft|approve|pending|answer",'
            ' "age":int, "sex":"M|F", "symptoms":[..], "patient_id":"AMRIT-..",'
            ' "condition":"..", "doctor_id":"..", "rx_id":"RX-..",'
            ' "reply":"..(only for action=answer)"}\n'
            "If it's general medical conversation, use action=answer with a "
            "short reply that ALWAYS ends with 'Discuss with your doctor.'\n"
            f"User: {text}"
        )
        try:
            raw = self.llm.chat([{"role": "user", "content": prompt}], max_tokens=400)
            m = re.search(r"\{.*\}", raw, re.S)
            action = json.loads(m.group(0)) if m else {}
        except Exception:
            return self._reply(
                "I can't interpret free text right now — the LLM is not reachable "
                "(Ollama not running / no API key). Offline commands still work:\n"
                + HELP_TEXT,
                understood=False)

        act = action.get("action")
        if act == "register":
            return self._cmd_register(
                f"register patient age {action.get('age')} "
                f"{'male' if action.get('sex') == 'M' else 'female'}")
        if act == "symptoms":
            return self._cmd_symptoms("symptoms: " + ", ".join(action.get("symptoms", []))
                                      + " " + action.get("patient_id", ""), session)
        if act == "history" and action.get("patient_id"):
            return self._cmd_history(action["patient_id"].upper())
        if act == "answer" and action.get("reply"):
            return self._reply(action["reply"] + " _(via LLM)_")
        return self._reply("I understood: " + json.dumps(action) +
                           " — but I can only run clinic commands. " + HELP_TEXT,
                           understood=False)
