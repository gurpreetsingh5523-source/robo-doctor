"""
AMRIT LIVE RESEARCH DEMO (v6.2)
================================
End-to-end REAL test:
  Part 1: Patient journey (register -> 3 visits -> early trend detection)
  Part 2: LIVE autonomous research with real PubMed literature mining
  Part 3: Real research paper generated from the live findings
Everything printed here comes from actual module output — nothing staged.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def section(t):
    print("\n" + "=" * 64)
    print(f"  {t}")
    print("=" * 64)

# ---------------- PART 1: Patient journey ----------------
section("PART 1: Patient journey (register, history, early signals)")
from src.patients.patient_registry import PatientRegistry, ConsentError

reg = PatientRegistry(db_path="data/demo_patients.db")
pid = reg.register_patient(age=45, sex='M', population='south_asian',
                           consent_general=True, consent_genomic=True)
print(f"Patient registered anonymously: {pid}")

p = reg.get_patient(pid)
print(f"  age={p['age']} sex={p['sex']} population={p['population']} anonymous={p['anonymous']}")

# Three visits over time - glucose creeping up (pre-diabetes trajectory)
visits = [
    {'glucose_fasting': 95, 'hba1c': 5.4, 'vitamin_d': 22},
    {'glucose_fasting': 105, 'hba1c': 5.6, 'vitamin_d': 19},
    {'glucose_fasting': 118, 'hba1c': 5.9, 'vitamin_d': 16},
]
for i, panel in enumerate(visits, 1):
    reg.record_event(pid, 'blood_panel', panel)
    print(f"  Visit {i} recorded: glucose={panel['glucose_fasting']}")

# Consent enforcement check
pid2 = reg.register_patient(age=30, sex='F', population='south_asian',
                            consent_general=True, consent_genomic=False)
try:
    reg.record_event(pid2, 'dna_analysis', {'APOE4': '1_copy'})
    print("  FAIL: genomic event allowed without consent!")
except ConsentError as e:
    print(f"  Consent gate works: genomic event blocked for {pid2}")

# Early signal detection
signals = reg.early_signal_check(pid, {'glucose_fasting': 126, 'hba1c': 6.1, 'vitamin_d': 14})
print(f"\nEarly signal check for {pid}:")
for t in signals['early_trends']:
    print(f"  ⚠ {t['test']}: {t['direction']} {t['change_pct']}% over {t['history']}")
print(f"  ({signals['disclaimer']})")

# ---------------- PART 2: LIVE autonomous research ----------------
section("PART 2: LIVE autonomous research (real PubMed fetch)")
from src.autonomous.unified_agent import UnifiedAgent

topic = "metformin repurposing for cancer therapy"
print(f"Topic: {topic}")
print("Calling real PubMed API now... (network)")
ua = UnifiedAgent()
print(f"Literature agent has real DataCollector: {ua.literature_agent.data_collector is not None}")

result = ua.run_autonomous_research(topic)
findings = ua.literature_agent.findings
real_findings = [f for f in findings if f.source != 'SIMULATED']
print(f"\nREAL findings mined from PubMed: {len(real_findings)}")
for f in real_findings[:5]:
    print(f"  📄 {f.finding[:90]}")
print(f"\nPipeline result: patterns={result['patterns_detected']}, "
      f"hypotheses={result['hypotheses_generated']}, status={result['status']}")

# ---------------- PART 3: Real paper from live findings ----------------
section("PART 3: Research paper generated from LIVE findings")
from src.core.paper_writer import PaperWriter

pw = PaperWriter(citation_format='Vancouver')
findings_dicts = [
    {'finding': f.finding, 'source': f.source, 'confidence': f.confidence,
     'authors': getattr(f, 'authors', []), 'url': getattr(f, 'url', '')}
    for f in real_findings
]
paper = pw.generate_paper(topic, findings_dicts, format='Vancouver')
md = pw.export_to_markdown(paper) if hasattr(pw, 'export_to_markdown') else None

out_path = os.path.join("data", "amrit_live_research_paper.md")
if md:
    with open(out_path, "w") as fh:
        fh.write(md)
    print(f"Paper saved: {out_path} ({paper['word_count']} words)")
else:
    with open(out_path, "w") as fh:
        fh.write(json.dumps(paper, indent=2, default=str))
    print(f"Paper saved (json): {out_path}")

print(f"Title: {paper['title']}")
print(f"Sections: {[s.get('heading', s.get('title','?')) for s in paper['sections']]}")
print(f"References: {len(paper['references'])}")

section("DEMO COMPLETE")
print(json.dumps(reg.registry_stats(), indent=2))
