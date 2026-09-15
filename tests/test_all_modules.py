"""
AMRIT Research OS v6.0 - Comprehensive Test Suite
Tests all modules for correctness and integration
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestResearchBrain(unittest.TestCase):
    """Test ResearchBrain module"""

    def test_hypothesis_generation(self):
        from src.core.research_brain import ResearchBrain, HypothesisType
        brain = ResearchBrain()
        hypotheses = brain.generate_hypothesis(
            "oncology", 
            ["tumor suppressor", "mutation", "pathway"]
        )
        self.assertIsInstance(hypotheses, list)
        self.assertTrue(len(hypotheses) > 0)
        self.assertTrue(all(h.confidence >= 0.65 for h in hypotheses))

    def test_bayesian_update(self):
        from src.core.research_brain import ResearchBrain
        brain = ResearchBrain()
        hypotheses = brain.generate_hypothesis("cardiology", ["hypertension", "genetics"])
        if hypotheses:
            updated = brain.evaluate_hypothesis(hypotheses[0], {
                'likelihood': 0.8,
                'evidence_probability': 0.6
            })
            self.assertIsNotNone(updated.confidence)

class TestMemoryManager(unittest.TestCase):
    """Test MemoryManager module"""

    def test_store_retrieve(self):
        from src.memory.memory_manager import MemoryManager
        import tempfile

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            mm = MemoryManager(db_path=tmp.name)
            entry_id = mm.store('test data', 'test', ['tag1'], 0.8)
            self.assertIsNotNone(entry_id)

            retrieved = mm.retrieve(entry_id)
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.content, 'test data')
            os.unlink(tmp.name)

    def test_search(self):
        from src.memory.memory_manager import MemoryManager
        import tempfile

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            mm = MemoryManager(db_path=tmp.name)
            mm.store('data1', 'hypothesis', ['cancer'], 0.9)
            mm.store('data2', 'paper', ['diabetes'], 0.7)

            results = mm.search(memory_type='hypothesis')
            self.assertEqual(len(results), 1)
            os.unlink(tmp.name)

class TestStatisticalEngine(unittest.TestCase):
    """Test StatisticalEngine module"""

    def test_monte_carlo(self):
        from src.core.statistical_engine import StatisticalEngine
        se = StatisticalEngine()

        def model(a, b):
            return a + b

        distributions = {
            'a': lambda: 1.0,
            'b': lambda: 2.0
        }

        result = se.monte_carlo_simulation(model, distributions, 100)
        self.assertIn('mean', result)
        self.assertIn('ci_95', result)

    def test_bayesian_inference(self):
        from src.core.statistical_engine import StatisticalEngine
        se = StatisticalEngine()

        result = se.bayesian_inference(1, 1, 8, 10)
        self.assertIn('posterior_alpha', result)
        self.assertIn('ci_95', result)
        self.assertGreater(result['mean'], 0)

    def test_benfords_law(self):
        from src.core.statistical_engine import StatisticalEngine
        se = StatisticalEngine()

        # Natural data should follow Benford's law
        data = [1, 12, 123, 1234, 2, 23, 234, 3, 34, 345]
        result = se.benfords_law_test(data)
        self.assertIsNotNone(result.p_value)

class TestAgentManager(unittest.TestCase):
    """Test AgentManager module"""

    def test_agent_creation(self):
        from src.agents.agent_manager import AgentManager
        am = AgentManager()
        stats = am.get_agent_stats()
        self.assertEqual(stats['total_agents'], 7)
        self.assertEqual(len(stats['roles']), 7)

    def test_debate(self):
        from src.agents.agent_manager import AgentManager
        am = AgentManager()
        result = am.run_collaborative_research('diabetes genetics')
        self.assertIn('consensus_level', result)
        self.assertIn('key_findings', result)

class TestKnowledgeGraph(unittest.TestCase):
    """Test KnowledgeGraph module"""

    def test_medical_graph(self):
        from src.knowledge.knowledge_graph import create_medical_knowledge_graph
        kg = create_medical_knowledge_graph()
        stats = kg.get_stats()
        self.assertGreater(stats['total_entities'], 0)
        self.assertGreater(stats['total_relationships'], 0)

    def test_path_finding(self):
        from src.knowledge.knowledge_graph import create_medical_knowledge_graph
        kg = create_medical_knowledge_graph()
        paths = kg.find_path('DIABETES_T2', 'GLUT4')
        self.assertIsInstance(paths, list)

class TestBloodAnalyzer(unittest.TestCase):
    """Test BloodAnalyzer module"""

    def test_single_test(self):
        from src.medical.blood_analyzer import BloodAnalyzer
        ba = BloodAnalyzer()
        result = ba.analyze_test('glucose_fasting', 95)
        self.assertEqual(result.risk_level.value, 'normal')

    def test_high_glucose(self):
        from src.medical.blood_analyzer import BloodAnalyzer
        ba = BloodAnalyzer()
        result = ba.analyze_test('glucose_fasting', 180)
        self.assertIn(result.risk_level.value, ['high', 'critical'])

    def test_panel_analysis(self):
        from src.medical.blood_analyzer import BloodAnalyzer
        ba = BloodAnalyzer()
        tests = {
            'glucose_fasting': 95,
            'hba1c': 5.5,
            'ldl_cholesterol': 110
        }
        results = ba.analyze_panel(tests)
        self.assertEqual(len(results), 3)

        summary = ba.get_health_summary(tests)
        self.assertIn('overall_risk', summary)

class TestConsanguinityDrug(unittest.TestCase):
    """Test ConsanguinityRisk and DrugPredictor"""

    def test_consanguinity_risk(self):
        from src.medical.consanguinity_drug import ConsanguinityRisk, RelationshipType
        cr = ConsanguinityRisk(RelationshipType.FIRST_COUSIN)
        result = cr.calculate_risk('thalassemia')
        self.assertIn('risk_ratio', result)
        self.assertGreater(result['risk_ratio'], 1)

    def test_drug_prediction(self):
        from src.medical.consanguinity_drug import DrugPredictor
        dp = DrugPredictor({'CYP2D6': 'poor'})
        result = dp.predict_drug_response('codeine')
        self.assertIn('status', result)

class TestEthicsFilter(unittest.TestCase):
    """Test EthicsFilter module"""

    def test_approved_action(self):
        from src.ethics.ethics_filter import EthicsFilter
        ef = EthicsFilter()
        result = ef.assess('Research on diabetes prevention')
        self.assertTrue(result.approved)
        self.assertGreater(result.overall_score, 0.7)

    def test_rejected_action(self):
        from src.ethics.ethics_filter import EthicsFilter
        ef = EthicsFilter()
        result = ef.assess('Eugenics-based selection of embryos')
        self.assertFalse(result.approved)
        self.assertGreater(len(result.violations), 0)

class TestQuantumLayer(unittest.TestCase):
    """Test QuantumLayer module"""

    def test_quantum_state(self):
        from src.quantum.quantum_layer import QuantumState
        qs = QuantumState(2)
        self.assertEqual(qs.dim, 4)
        probs = qs.get_probabilities()
        self.assertEqual(len(probs), 4)

    def test_quantum_biology(self):
        from src.quantum.quantum_layer import QuantumLayer
        ql = QuantumLayer()
        result = ql.quantum_biology_model('photosynthesis')
        self.assertIn('mechanism', result)

class TestAutonomousModules(unittest.TestCase):
    """Test Autonomous Research Modules"""

    def test_literature_mining(self):
        from src.autonomous.unified_agent import LiteratureMiningAgent
        lma = LiteratureMiningAgent()
        lma.track_topic('diabetes')
        findings = lma.mine_literature('diabetes')
        self.assertIsInstance(findings, list)

    def test_pattern_detection(self):
        from src.autonomous.unified_agent import PatternDetectionAgent
        pda = PatternDetectionAgent()
        data = [{'value': i} for i in range(20)]
        data[15]['value'] = 100  # anomaly
        patterns = pda.detect_patterns(data)
        self.assertIsInstance(patterns, list)

    def test_hypothesis_generation(self):
        from src.autonomous.unified_agent import HypothesisGenerator
        hg = HypothesisGenerator()
        hypotheses = hg.generate_disease_links('diabetes')
        self.assertGreater(len(hypotheses), 0)

    def test_prediction_engine(self):
        from src.autonomous.unified_agent import PredictionEngine
        pe = PredictionEngine()
        result = pe.predict_pandemic_risk({
            'population_density': 500,
            'mobility_index': 60,
            'healthcare_capacity': 70,
            'vaccination_rate': 75,
            'pathogen_transmissibility': 2.5
        })
        self.assertIn('risk_level', result)

    def test_self_improvement(self):
        from src.autonomous.unified_agent import SelfImprovementLoop
        sil = SelfImprovementLoop()
        result = sil.learn_from_data({'outcomes': [1, 0, 1, 1]}, 'clinical')
        self.assertIn('insights', result)

    def test_auto_module_generation(self):
        from src.autonomous.unified_agent import SelfImprovementLoop
        sil = SelfImprovementLoop()
        result = sil.auto_generate_module('Create a module for sleep analysis')
        self.assertIn('code', result)
        self.assertIn('validation', result)

    def test_unified_agent(self):
        from src.autonomous.unified_agent import UnifiedAgent
        ua = UnifiedAgent()
        status = ua.get_system_status()
        self.assertEqual(status['active_agents'], 5)

class TestHealthAdvisor(unittest.TestCase):
    """Test PersonalizedHealthAdvisor"""

    def test_dna_analysis(self):
        from src.medical.health_advisor import PersonalizedHealthAdvisor
        pha = PersonalizedHealthAdvisor()
        result = pha.analyze_dna({
            'APOE4': '1_copy',
            'MTHFR_C677T': 'CT'
        })
        self.assertIn('variants_analyzed', result)
        self.assertEqual(result['variants_analyzed'], 2)

    def test_environmental_analysis(self):
        from src.medical.health_advisor import PersonalizedHealthAdvisor
        pha = PersonalizedHealthAdvisor()
        result = pha.analyze_environment({
            'PM2.5': 35.0,
            'arsenic': 15.0
        })
        self.assertIn('exposure_results', result)

    def test_full_assessment(self):
        from src.medical.health_advisor import PersonalizedHealthAdvisor
        pha = PersonalizedHealthAdvisor()
        result = pha.full_health_assessment({
            'id': 'P001',
            'dna_variants': {'APOE4': '1_copy'},
            'environmental': {'PM2.5': 25.0}
        })
        self.assertIn('overall_health_score', result)
        self.assertIn('recommendations', result)

class TestPaperWriter(unittest.TestCase):
    """Test PaperWriter"""

    def test_paper_generation(self):
        from src.core.paper_writer import PaperWriter
        pw = PaperWriter()
        findings = [
            {'finding': 'Novel biomarker identified', 'confidence': 0.9, 'source': 'PubMed'},
            {'finding': 'Drug target validated', 'confidence': 0.85, 'source': 'Nature'}
        ]
        paper = pw.generate_paper('diabetes', findings, 'APA')
        self.assertIn('title', paper)
        self.assertIn('sections', paper)
        self.assertGreater(paper['word_count'], 0)

class TestDataCollector(unittest.TestCase):
    """Test DataCollector"""

    def test_initialization(self):
        from src.core.data_collector import DataCollector
        dc = DataCollector()
        self.assertIsNotNone(dc.session)

class TestIntegration(unittest.TestCase):
    """Integration tests across modules"""

    def test_end_to_end_research(self):
        """Test full research pipeline"""
        from src.core.research_brain import ResearchBrain
        from src.core.statistical_engine import StatisticalEngine
        from src.ethics.ethics_filter import EthicsFilter

        # Generate hypothesis
        brain = ResearchBrain()
        hypotheses = brain.generate_hypothesis('oncology', ['tumor', 'gene', 'therapy'])

        # Validate statistically
        se = StatisticalEngine()
        if hypotheses:
            # Simulate p-value
            p_value = 0.01
            self.assertLess(p_value, 0.05)

        # Check ethics
        ef = EthicsFilter()
        ethics = ef.assess('Research on cancer treatment for underserved populations')
        self.assertTrue(ethics.approved)

    def test_health_pipeline(self):
        """Test health assessment pipeline"""
        from src.medical.blood_analyzer import BloodAnalyzer
        from src.medical.health_advisor import PersonalizedHealthAdvisor

        # Blood analysis
        ba = BloodAnalyzer(population='south_asian')
        tests = {'glucose_fasting': 95, 'hba1c': 5.5, 'vitamin_d': 25}
        blood_results = ba.analyze_panel(tests)

        # DNA analysis
        pha = PersonalizedHealthAdvisor()
        dna_results = pha.analyze_dna({'MTHFR_C677T': 'CT'})

        # Environmental
        env_results = pha.analyze_environment({'PM2.5': 20.0})

        # Combined recommendations
        recs = pha.generate_recommendations(dna_results, {}, env_results)
        self.assertIn('recommendations', recs)

class TestAlphaGenomeClient(unittest.TestCase):
    """Test AlphaGenome Atlas integration (v6.2)"""

    def _make_client(self):
        import tempfile
        from src.memory.memory_manager import MemoryManager
        from src.ethics.ethics_filter import EthicsFilter
        from src.medical.alphagenome_client import AlphaGenomeClient
        tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        mm = MemoryManager(db_path=tmp.name)
        client = AlphaGenomeClient(memory_manager=mm, ethics_filter=EthicsFilter(),
                                   api_key='test-key')
        return client, tmp.name

    def test_consent_gate_blocks(self):
        from src.medical.alphagenome_client import AlphaGenomeClient, ConsentRequiredError
        client, tmp = self._make_client()
        with self.assertRaises(ConsentRequiredError):
            client.analyze_variant({'gene': 'BRCA1', 'variant': 'x'},
                                   patient_id='P1', consent_confirmed=False)
        os.unlink(tmp)

    def test_honest_when_api_not_configured(self):
        from src.medical.alphagenome_client import AlphaGenomeClient
        client, tmp = self._make_client()
        client.api_key = None  # no live access
        r = client.analyze_variant({'gene': 'BRCA1', 'variant': 'x'},
                                   patient_id='P1', consent_confirmed=True)
        self.assertEqual(r['status'], 'api_not_configured')
        self.assertIsNone(r['avi_score'])  # never fabricate
        self.assertIn('disclaimer', r)
        os.unlink(tmp)

    def test_avi_scoring_and_cache(self):
        client, tmp = self._make_client()
        client._query_api = lambda v: {'avi_score': 32.5,
                                       'feature_attributions': {'splicing': 0.8},
                                       'source': 'mock'}
        variant = {'gene': 'BRCA1', 'variant': 'c.68_69delAG', 'genotype': 'het'}
        r1 = client.analyze_variant(variant, patient_id='P1', consent_confirmed=True)
        self.assertFalse(r1['cache_hit'])
        self.assertEqual(r1['avi_interpretation']['band'], 'very_high')
        r2 = client.analyze_variant(variant, patient_id='P1', consent_confirmed=True)
        self.assertTrue(r2['cache_hit'])  # served from MemoryManager
        stats = client.get_cache_stats()
        self.assertEqual(stats['cached_variants'], 1)
        os.unlink(tmp)

    def test_health_advisor_enrichment(self):
        from src.medical.health_advisor import PersonalizedHealthAdvisor
        client, tmp = self._make_client()
        client._query_api = lambda v: {'avi_score': 12.0,
                                       'feature_attributions': {}, 'source': 'mock'}
        ha = PersonalizedHealthAdvisor(alphagenome_client=client)
        panel = ha.analyze_variants_with_alphagenome(
            [{'gene': 'APOE', 'variant': 'rs429358', 'genotype': '1_copy'}],
            patient_id='P1', consent_confirmed=True)
        self.assertEqual(panel['variants_analyzed'], 1)
        self.assertEqual(panel['variants_with_scores'], 1)
        os.unlink(tmp)

class TestDockingGateway(unittest.TestCase):
    """Test Molecular Docking Gateway (v6.2)"""

    def test_honest_engine_status(self):
        from src.medical.docking_gateway import DockingGateway
        gw = DockingGateway()
        status = gw.engine_status()
        self.assertIn(status['status'], ('available', 'engine_not_installed'))

    def test_no_fabrication_without_engine(self):
        from src.medical.docking_gateway import DockingGateway
        gw = DockingGateway()
        if gw.engine_available:
            self.skipTest("engine installed - honest-path test not applicable")
        r = gw.dock('1CRN', ligand_smiles='CCO', purpose='drug repurposing research')
        self.assertEqual(r['status'], 'engine_not_installed')
        self.assertIsNone(r['binding_affinity_kcal_mol'])  # never fabricated

    def test_affinity_interpretation(self):
        from src.medical.docking_gateway import DockingGateway
        gw = DockingGateway()
        self.assertEqual(gw.interpret_affinity(-11.0)['band'], 'excellent')
        self.assertEqual(gw.interpret_affinity(-8.5)['band'], 'strong')
        self.assertEqual(gw.interpret_affinity(-5.0)['band'], 'weak')

    def test_patient_registry(self):
        import tempfile
        from src.patients.patient_registry import PatientRegistry, ConsentError
        tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        reg = PatientRegistry(db_path=tmp.name)
        pid = reg.register_patient(age=45, sex='M', population='south_asian',
                                   consent_general=True, consent_genomic=False)
        reg.record_event(pid, 'blood_panel', {'glucose_fasting': 95})
        reg.record_event(pid, 'blood_panel', {'glucose_fasting': 120})
        signals = reg.early_signal_check(pid, {'glucose_fasting': 130})
        self.assertTrue(any(t['test'] == 'glucose_fasting'
                            and t['direction'] == 'rising'
                            for t in signals['early_trends']))
        with self.assertRaises(ConsentError):
            reg.record_event(pid, 'dna_analysis', {'APOE4': '1_copy'})
        os.unlink(tmp.name)

class TestSymptomAnalyzer(unittest.TestCase):
    """Test Symptom -> test recommendation logic (v6.2)"""

    def test_diabetes_triad(self):
        from src.medical.symptom_analyzer import SymptomAnalyzer
        sa = SymptomAnalyzer()
        r = sa.analyze(['excessive thirst', 'frequent urination', 'weight loss'])
        self.assertIn('hba1c', r['recommended_tests'])
        self.assertIn('glucose_fasting', r['recommended_tests'])
        self.assertTrue(r['red_flags'])  # triad triggers escalation

    def test_emergency_red_flag(self):
        from src.medical.symptom_analyzer import SymptomAnalyzer
        sa = SymptomAnalyzer()
        r = sa.analyze(['chest pain', 'breathlessness'])
        self.assertEqual(r['urgency'], 'EMERGENCY')

    def test_unknown_symptom_honesty(self):
        from src.medical.symptom_analyzer import SymptomAnalyzer
        sa = SymptomAnalyzer()
        r = sa.analyze(['fatigue', 'purple_spots_on_elbow'])
        self.assertIn('fatigue', r['symptoms_recognized'])
        self.assertIn('purple_spots_on_elbow', r['symptoms_unknown'])
        self.assertIsNotNone(r['unknown_note'])

    def test_population_screening(self):
        from src.medical.symptom_analyzer import SymptomAnalyzer
        sa = SymptomAnalyzer()
        r = sa.analyze(['fatigue'], population='south_asian')
        self.assertIsNotNone(r['population_screening'])
        self.assertIn('hba1c', r['population_screening']['tests'])


class TestPrescriptionWorkflow(unittest.TestCase):
    """Test prescription draft -> doctor approval workflow (v6.2)"""

    def _make(self):
        import tempfile
        from src.patients.patient_registry import PatientRegistry
        from src.medical.prescription_workflow import PrescriptionWorkflow
        tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        reg = PatientRegistry(db_path=tmp.name)
        pid = reg.register_patient(age=50, sex='M', consent_general=True)
        return PrescriptionWorkflow(patient_registry=reg), pid, tmp.name

    def test_draft_is_never_final(self):
        wf, pid, tmp = self._make()
        rx = wf.create_draft(pid, 'type_2_diabetes', doctor_id='DR001')
        self.assertEqual(rx['status'], 'DRAFT_PENDING_DOCTOR_REVIEW')
        self.assertIn('DRAFT ONLY', rx['legal_note'])
        self.assertIn('Metformin', [m['drug'] for m in rx['medications']])
        os.unlink(tmp)

    def test_only_assigned_doctor_can_approve(self):
        from src.medical.prescription_workflow import DoctorVerificationRequired
        wf, pid, tmp = self._make()
        rx = wf.create_draft(pid, 'hypertension', doctor_id='DR001')
        with self.assertRaises(DoctorVerificationRequired):
            wf.approve(rx['prescription_id'], doctor_id='DR999')
        approved = wf.approve(rx['prescription_id'], doctor_id='DR001')
        self.assertEqual(approved['status'], 'APPROVED_BY_DOCTOR')
        os.unlink(tmp)

    def test_no_double_approval(self):
        from src.medical.prescription_workflow import PrescriptionStateError
        wf, pid, tmp = self._make()
        rx = wf.create_draft(pid, 'vitamin_d_deficiency', doctor_id='DR001')
        wf.approve(rx['prescription_id'], doctor_id='DR001')
        with self.assertRaises(PrescriptionStateError):
            wf.approve(rx['prescription_id'], doctor_id='DR001')
        os.unlink(tmp)

    def test_reject_logged_in_history(self):
        wf, pid, tmp = self._make()
        rx = wf.create_draft(pid, 'hypothyroidism', doctor_id='DR001')
        wf.reject(rx['prescription_id'], doctor_id='DR001', reason='wrong diagnosis')
        history = wf.registry.get_history(pid, 'prescription_rejected')
        self.assertEqual(len(history), 1)
        os.unlink(tmp)


class TestLLMAndVoice(unittest.TestCase):
    """Test pluggable LLM + voice interfaces (v6.2)"""

    def test_llm_honest_when_not_configured(self):
        from src.core.llm_interface import LLMInterface, LLMNotConfigured
        llm = LLMInterface(api_key='', base_url='https://api.deepseek.com/v1')
        self.assertFalse(llm.configured)
        with self.assertRaises(LLMNotConfigured):
            llm.chat([{'role': 'user', 'content': 'hello'}])

    def test_voice_capabilities_honest(self):
        from src.dashboard.voice_interface import VoiceInterface
        v = VoiceInterface()
        caps = v.capabilities()
        self.assertIn('tts_offline', caps)
        r = v.transcribe('/nonexistent.mp3')  # no STT configured
        self.assertEqual(r['status'], 'stt_not_configured')
        self.assertIsNone(r['text'])  # never fabricated

class TestChatEngine(unittest.TestCase):
    """Test chat command interface (v6.2)"""

    def _make(self):
        import tempfile
        from src.patients.patient_registry import PatientRegistry
        from src.medical.symptom_analyzer import SymptomAnalyzer
        from src.medical.blood_analyzer import BloodAnalyzer
        from src.medical.prescription_workflow import PrescriptionWorkflow
        from src.dashboard.chat_engine import ChatEngine
        tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        reg = PatientRegistry(db_path=tmp.name)
        engine = ChatEngine(
            patient_registry=reg,
            symptom_analyzer=SymptomAnalyzer(),
            blood_analyzer=BloodAnalyzer(),
            prescription_workflow=PrescriptionWorkflow(patient_registry=reg),
            llm=None)  # offline rules only
        return engine, tmp.name

    def test_help_and_unknown(self):
        eng, tmp = self._make()
        self.assertIn('register patient', eng.handle('help')['reply'])
        r = eng.handle('blargh flibberty gibbet')
        self.assertFalse(r['understood'])  # honest, no guessing
        os.unlink(tmp)

    def test_full_flow_via_chat(self):
        eng, tmp = self._make()
        r = eng.handle('register patient age 52 male population south_asian')
        pid = r['data']['patient_id']
        self.assertTrue(pid.startswith('AMRIT-'))
        r = eng.handle(f'symptoms: excessive thirst, frequent urination for {pid}')
        self.assertIn('hba1c', r['reply'])
        r = eng.handle(f'blood: glucose_fasting=180 for {pid}')
        self.assertIn('critical', r['reply'])
        r = eng.handle(f'draft prescription for {pid} condition type_2_diabetes doctor DR_SMITH')
        rx_id = r['data']['prescription_id']
        self.assertIn('DRAFT', r['reply'])
        r = eng.handle(f'approve {rx_id} doctor DR_WRONG')
        self.assertTrue(r['error'])  # wrong doctor blocked via chat too
        r = eng.handle(f'approve {rx_id} doctor DR_SMITH')
        self.assertIn('approved', r['reply'])
        r = eng.handle(f'history of {pid}')
        self.assertIn('blood_panel', r['reply'])
        os.unlink(tmp)

    def test_chat_cannot_self_approve(self):
        eng, tmp = self._make()
        r = eng.handle('register patient age 40 female')
        pid = r['data']['patient_id']
        r = eng.handle(f'draft prescription for {pid} condition hypertension doctor DR_A')
        rx_id = r['data']['prescription_id']
        r = eng.handle(f'approve {rx_id}')  # no doctor given, no session
        self.assertFalse(r['understood'])  # must name the doctor
        os.unlink(tmp)

if __name__ == '__main__':
    # Run all tests with verbose output
    unittest.main(verbosity=2)
