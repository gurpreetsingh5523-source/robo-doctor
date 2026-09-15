"""Real capability test - exercise actual AMRIT modules directly."""
import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def section(name):
    print("\n" + "=" * 60)
    print(f"  {name}")
    print("=" * 60)

# 1. BloodAnalyzer - real analysis with abnormal values
section("1. BloodAnalyzer (real module, abnormal panel)")
try:
    from src.medical.blood_analyzer import BloodAnalyzer
    ba = BloodAnalyzer()
    result = ba.analyze_panel({
        'glucose_fasting': 180, 'hba1c': 7.2, 'ldl_cholesterol': 165,
        'vitamin_d': 12, 'hemoglobin': 10.5
    }, population='south_asian')
    for name, r in list(result.items())[:6]:
        print(f"  {name}: {r}")
except Exception:
    traceback.print_exc()

# 2. HealthAdvisor - DNA analysis
section("2. HealthAdvisor (real DNA analysis)")
try:
    from src.medical.health_advisor import PersonalizedHealthAdvisor
    ha = PersonalizedHealthAdvisor()
    dna_result = ha.analyze_dna({'APOE4': '1_copy', 'MTHFR_C677T': 'CT', 'FTO': 'AT'})
    print(str(dna_result)[:800])
except Exception:
    traceback.print_exc()

# 3. EthicsFilter - real ethics module
section("3. EthicsFilter (real module, eugenics text)")
try:
    from src.ethics.ethics_filter import EthicsFilter
    ef = EthicsFilter()
    bad = ef.check_action("eugenics-based embryo selection without consent")
    good = ef.check_action("Research on genetic markers for diabetes prevention")
    print(f"  eugenics action -> approved={bad.approved if hasattr(bad,'approved') else bad}")
    print(f"  legit research  -> approved={good.approved if hasattr(good,'approved') else good}")
except Exception:
    traceback.print_exc()

# 4. ResearchBrain - hypothesis generation
section("4. ResearchBrain (hypothesis generation)")
try:
    from src.core.research_brain import ResearchBrain
    brain = ResearchBrain()
    hyps = brain.generate_hypothesis("oncology", ["tumor suppressor", "mutation", "pathway"])
    for h in hyps[:2]:
        print(f"  - {getattr(h, 'statement', h)} | confidence={getattr(h, 'confidence', '?')}")
except Exception:
    traceback.print_exc()

# 5. StatisticalEngine
section("5. StatisticalEngine (Monte Carlo + Bayesian)")
try:
    from src.core.statistical_engine import StatisticalEngine
    se = StatisticalEngine()
    mc = se.monte_carlo_simulation(lambda a, b: a + b, {'a': lambda: 1.0, 'b': lambda: 2.0}, 200)
    print(f"  Monte Carlo mean={mc['mean']:.3f} ci_95={mc['ci_95']}")
    bi = se.bayesian_inference(1, 1, 8, 10)
    print(f"  Bayesian posterior mean={bi['mean']:.3f}")
except Exception:
    traceback.print_exc()

# 6. KnowledgeGraph
section("6. KnowledgeGraph (medical graph)")
try:
    from src.knowledge.knowledge_graph import KnowledgeGraph, create_medical_knowledge_graph
    kg = create_medical_knowledge_graph()
    print(f"  graph created: {kg}")
except Exception:
    traceback.print_exc()

# 7. AgentManager - 7-agent debate
section("7. AgentManager (7-agent swarm debate)")
try:
    from src.agents.agent_manager import AgentManager
    am = AgentManager()
    print(f"  agents: {len(am.agents) if hasattr(am,'agents') else '?'}")
    debate = am.run_debate("Should AI be used for drug repurposing?") if hasattr(am, 'run_debate') else 'no run_debate method'
    print(f"  debate result: {str(debate)[:400]}")
except Exception:
    traceback.print_exc()

# 8. UnifiedAgent - autonomous research (the v6.0 flagship)
section("8. UnifiedAgent (autonomous research)")
try:
    from src.autonomous.unified_agent import UnifiedAgent
    ua = UnifiedAgent()
    result = ua.run_autonomous_research("metformin repurposing for cancer")
    print(str(result)[:800])
except Exception:
    traceback.print_exc()

# 9. DataCollector - real network fetch (PubMed)
section("9. DataCollector (LIVE network fetch from PubMed)")
try:
    from src.core.data_collector import DataCollector
    dc = DataCollector()
    methods = [m for m in dir(dc) if not m.startswith('_')]
    print(f"  available methods: {methods}")
except Exception:
    traceback.print_exc()

section("DONE")
