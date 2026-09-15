"""
AMRIT Patient Registry (v6.2)
=============================
Patient registration + longitudinal health history for the AMRIT seva mission.

Design principles:
1. PRIVACY    - Patients can be fully anonymous (no name required). All data
                stays in a local SQLite database. Nothing leaves the machine.
2. CONSENT    - Separate consent flags for general care and genomic analysis.
                Genomic events are refused without genomic consent.
3. MEMORY     - Every test, analysis and assessment is recorded as a timeline
                event, so the system "knows the patient" across visits and can
                spot early trends (e.g. fasting glucose creeping up over years).
4. SEVA       - Built for low-resource settings: works fully offline.
"""

import os
import json
import sqlite3
import threading
import hashlib
from datetime import datetime
from typing import Dict, List, Optional


class ConsentError(Exception):
    pass


class PatientNotFoundError(Exception):
    pass


class PatientRegistry:
    """
    Local patient registry with longitudinal history.

    Usage:
        reg = PatientRegistry()
        pid = reg.register_patient(age=45, sex='M', population='south_asian',
                                   consent_general=True, consent_genomic=True)
        reg.record_event(pid, 'blood_panel', {'glucose_fasting': 110, ...})
        history = reg.get_history(pid)
        signals = reg.early_signal_check(pid, {'glucose_fasting': 126})
    """

    def __init__(self, db_path: str = "data/patients.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.lock = threading.RLock()
        self._init_db()

    def _init_db(self):
        with self.lock, sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    patient_id TEXT PRIMARY KEY,
                    display_name TEXT,
                    age INTEGER,
                    sex TEXT,
                    population TEXT,
                    consent_general INTEGER DEFAULT 0,
                    consent_genomic INTEGER DEFAULT 0,
                    created_at TEXT,
                    anonymous INTEGER DEFAULT 1
                )""")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT,
                    event_type TEXT,
                    data TEXT,
                    recorded_at TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
                )""")
            conn.commit()

    # ------------------------------------------------------------------
    def _generate_id(self, seed: str) -> str:
        h = hashlib.sha256(f"{seed}{datetime.now().isoformat()}".encode()).hexdigest()
        return f"AMRIT-{h[:8].upper()}"

    def register_patient(self,
                         age: int,
                         sex: str,
                         population: str = "general",
                         display_name: Optional[str] = None,
                         consent_general: bool = False,
                         consent_genomic: bool = False) -> str:
        """Register a patient. Name is OPTIONAL — anonymous care is supported."""
        patient_id = self._generate_id(f"{age}{sex}{population}")
        with self.lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO patients
                   (patient_id, display_name, age, sex, population,
                    consent_general, consent_genomic, created_at, anonymous)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (patient_id, display_name, age, sex, population,
                 int(consent_general), int(consent_genomic),
                 datetime.now().isoformat(), int(display_name is None)))
            conn.commit()
        return patient_id

    def get_patient(self, patient_id: str) -> Dict:
        with self.lock, sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM patients WHERE patient_id = ?", (patient_id,)
            ).fetchone()
        if row is None:
            raise PatientNotFoundError(f"Patient {patient_id} not found")
        d = dict(row)
        d['consent_general'] = bool(d['consent_general'])
        d['consent_genomic'] = bool(d['consent_genomic'])
        d['anonymous'] = bool(d['anonymous'])
        return d

    # ------------------------------------------------------------------
    GENOMIC_EVENTS = {'dna_analysis', 'variant_analysis', 'alphagenome_lookup'}

    def record_event(self, patient_id: str, event_type: str, data: Dict) -> int:
        """Record a health event. Genomic events require genomic consent."""
        patient = self.get_patient(patient_id)  # raises if missing
        if event_type in self.GENOMIC_EVENTS and not patient['consent_genomic']:
            raise ConsentError(
                f"Genomic event '{event_type}' BLOCKED for {patient_id}: "
                "patient has not given genomic consent.")
        with self.lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO events (patient_id, event_type, data, recorded_at) VALUES (?,?,?,?)",
                (patient_id, event_type, json.dumps(data, default=str),
                 datetime.now().isoformat()))
            conn.commit()
            return cur.lastrowid

    def get_history(self, patient_id: str, event_type: Optional[str] = None) -> List[Dict]:
        self.get_patient(patient_id)  # raises if missing
        with self.lock, sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if event_type:
                rows = conn.execute(
                    "SELECT * FROM events WHERE patient_id=? AND event_type=? ORDER BY recorded_at",
                    (patient_id, event_type)).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM events WHERE patient_id=? ORDER BY recorded_at",
                    (patient_id,)).fetchall()
        return [{**dict(r), 'data': json.loads(r['data'])} for r in rows]

    # ------------------------------------------------------------------
    def early_signal_check(self, patient_id: str, new_panel: Dict[str, float]) -> Dict:
        """
        Compare a new blood panel against the patient's history to catch
        early trends BEFORE they become disease (e.g. glucose rising
        95 -> 105 -> 118 over three visits = pre-diabetes trajectory).
        """
        past_panels = [e['data'] for e in self.get_history(patient_id, 'blood_panel')]
        trends = []
        for test, value in new_panel.items():
            series = [p[test] for p in past_panels if test in p] + [value]
            if len(series) >= 2:
                delta = series[-1] - series[0]
                pct = (delta / series[0] * 100) if series[0] else 0
                if abs(pct) >= 10:  # >=10% drift across history is noteworthy
                    trends.append({
                        'test': test,
                        'history': series,
                        'change_pct': round(pct, 1),
                        'direction': 'rising' if delta > 0 else 'falling',
                        'note': f"{test} has moved {pct:+.0f}% across {len(series)} visits",
                    })
        return {
            'patient_id': patient_id,
            'visits_compared': len(past_panels) + 1,
            'early_trends': trends,
            'disclaimer': 'Trend signals are screening aids, not diagnoses. '
                          'A physician must confirm.',
            'timestamp': datetime.now().isoformat(),
        }

    def patient_summary(self, patient_id: str) -> Dict:
        patient = self.get_patient(patient_id)
        events = self.get_history(patient_id)
        counts = {}
        for e in events:
            counts[e['event_type']] = counts.get(e['event_type'], 0) + 1
        return {
            'patient': patient,
            'total_events': len(events),
            'event_counts': counts,
            'first_visit': events[0]['recorded_at'] if events else None,
            'last_visit': events[-1]['recorded_at'] if events else None,
        }

    def registry_stats(self) -> Dict:
        """Counts only — never leak patient details in bulk."""
        with self.lock, sqlite3.connect(self.db_path) as conn:
            n_patients = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
            n_events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        return {'registered_patients': n_patients, 'total_events': n_events}
