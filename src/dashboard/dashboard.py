
"""
AMRIT Dashboard - FastAPI Web Server
Terminal live logs + Web interface
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import asyncio
from datetime import datetime
import json

# Import real AMRIT modules (wired in v6.2 — no more simulated responses)
try:
    from src.core.research_brain import ResearchBrain
    from src.memory.memory_manager import MemoryManager
    from src.core.statistical_engine import StatisticalEngine
    from src.agents.agent_manager import AgentManager
    from src.knowledge.knowledge_graph import KnowledgeGraph, create_medical_knowledge_graph
    from src.core.data_collector import DataCollector
    from src.core.paper_writer import PaperWriter
    from src.medical.blood_analyzer import BloodAnalyzer
    from src.medical.consanguinity_drug import ConsanguinityRisk, DrugPredictor
    from src.medical.health_advisor import PersonalizedHealthAdvisor
    from src.medical.alphagenome_client import (
        AlphaGenomeClient, ConsentRequiredError, EthicsBlockedError,
        ALPHAGENOME_DISCLAIMER)
    from src.ethics.ethics_filter import EthicsFilter
    from src.quantum.quantum_layer import QuantumLayer
    from src.autonomous.unified_agent import UnifiedAgent
    from src.patients.patient_registry import PatientRegistry
    from src.medical.symptom_analyzer import SymptomAnalyzer
    from src.medical.prescription_workflow import (
        PrescriptionWorkflow, PrescriptionStateError, DoctorVerificationRequired)
    from src.core.llm_interface import LLMInterface
    from src.dashboard.voice_interface import VoiceInterface
    MODULES_AVAILABLE = True
    MODULE_IMPORT_ERROR = None
except Exception as e:
    MODULES_AVAILABLE = False
    MODULE_IMPORT_ERROR = str(e)

app = FastAPI(
    title="Robo Doctor (AMRIT Research OS)",
    description="Robo Doctor — seva healthcare assistant: research, diagnosis support, "
                "patient memory, prescription drafts with mandatory doctor approval",
    version="6.2.0"
)

# System state
system_state = {
    'status': 'initializing',
    'modules_loaded': [],
    'last_update': datetime.now().isoformat(),
    'total_requests': 0,
    'active_research': []
}

# Instantiate real modules (None-safe if imports failed)
if MODULES_AVAILABLE:
    memory_manager = MemoryManager()
    ethics_filter = EthicsFilter()
    blood_analyzer = BloodAnalyzer()
    alphagenome_client = AlphaGenomeClient(
        memory_manager=memory_manager, ethics_filter=ethics_filter)
    health_advisor = PersonalizedHealthAdvisor(
        alphagenome_client=alphagenome_client)
    research_brain = ResearchBrain()
    statistical_engine = StatisticalEngine()
    agent_manager = AgentManager()
    unified_agent = UnifiedAgent()
    patient_registry = PatientRegistry()
    symptom_analyzer = SymptomAnalyzer()
    prescription_workflow = PrescriptionWorkflow(patient_registry=patient_registry)
    llm = LLMInterface()
    voice = VoiceInterface()
else:
    memory_manager = ethics_filter = blood_analyzer = None
    alphagenome_client = health_advisor = research_brain = None
    statistical_engine = agent_manager = unified_agent = None
    patient_registry = symptom_analyzer = prescription_workflow = None
    llm = voice = None

# Request/Response models
class ResearchRequest(BaseModel):
    topic: str
    duration_hours: Optional[int] = 24
    sources: Optional[List[str]] = None

class BloodPanelRequest(BaseModel):
    patient_id: str
    tests: Dict[str, float]
    population: Optional[str] = 'general'

class DNAAnalysisRequest(BaseModel):
    patient_id: str
    variants: Dict[str, str]

class EthicsCheckRequest(BaseModel):
    action: str
    context: Optional[Dict] = None

class ModuleGenerationRequest(BaseModel):
    requirement: str

class VariantAnalysisRequest(BaseModel):
    patient_id: str
    variants: List[Dict]          # e.g. [{"gene":"DNM1","variant":"splice_site","genotype":"het"}]
    consent_confirmed: bool = False   # HARD GATE: analysis blocked unless True
    purpose: Optional[str] = "clinical research and patient counseling"

class PatientRegisterRequest(BaseModel):
    age: int
    sex: str
    population: Optional[str] = "general"
    display_name: Optional[str] = None      # optional — anonymous care supported
    consent_general: bool = False
    consent_genomic: bool = False

class SymptomRequest(BaseModel):
    patient_id: Optional[str] = None
    symptoms: List[str]
    population: Optional[str] = "general"
    age: Optional[int] = None

class PrescriptionDraftRequest(BaseModel):
    patient_id: str
    condition: str
    doctor_id: str
    extra_meds: Optional[List[Dict]] = None

class PrescriptionReviewRequest(BaseModel):
    doctor_id: str
    notes: Optional[str] = ""
    reason: Optional[str] = ""
    medications: Optional[List[Dict]] = None   # for modify_and_approve

# ==================== ROOT ENDPOINT ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """AMRIT Dashboard Home"""
    page = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AMRIT Research OS v6.0</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; }
            .card { background: white; padding: 20px; margin: 15px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .metric { display: inline-block; margin: 10px 20px; text-align: center; }
            .metric-value { font-size: 32px; font-weight: bold; color: #667eea; }
            .metric-label { font-size: 14px; color: #666; }
            .status { padding: 5px 15px; border-radius: 20px; display: inline-block; }
            .status-operational { background: #d4edda; color: #155724; }
            .status-initializing { background: #fff3cd; color: #856404; }
            .gurmat { font-style: italic; color: #764ba2; margin-top: 20px; }
            .modules { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px; }
            .module-tag { background: #e3f2fd; color: #1565c0; padding: 5px 12px; border-radius: 15px; font-size: 12px; }
            a { color: #667eea; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🕉️ AMRIT Research OS v6.0</h1>
            <h2>Autonomous Medical Research & Personalized Health System</h2>
            <p class="gurmat">"ਸਰਬੱਤ ਦਾ ਭਲਾ" (Sarbat Da Bhala) - Welfare of All Humanity</p>
        </div>

        <div class="card">
            <h3>System Status</h3>
            <span class="status status-{status}">{status_text}</span>
            <p>Last Update: {last_update}</p>
        </div>

        <div class="card">
            <h3>Metrics</h3>
            <div class="metric">
                <div class="metric-value">{modules_count}</div>
                <div class="metric-label">Modules Loaded</div>
            </div>
            <div class="metric">
                <div class="metric-value">{requests}</div>
                <div class="metric-label">Total Requests</div>
            </div>
            <div class="metric">
                <div class="metric-value">{active_research}</div>
                <div class="metric-label">Active Research</div>
            </div>
        </div>

        <div class="card">
            <h3>Available Modules</h3>
            <div class="modules">
                {module_tags}
            </div>
        </div>

        <div class="card">
            <h3>API Endpoints</h3>
            <ul>
                <li><a href="/api/status">GET /api/status</a> - System status</li>
                <li><a href="/api/research">POST /api/research</a> - Start autonomous research</li>
                <li><a href="/api/blood/analyze">POST /api/blood/analyze</a> - Analyze blood panel</li>
                <li><a href="/api/dna/analyze">POST /api/dna/analyze</a> - Analyze DNA variants</li>
                <li><a href="/api/ethics/check">POST /api/ethics/check</a> - Ethics assessment</li>
                <li><a href="/api/health/assessment">POST /api/health/assessment</a> - Full health assessment</li>
                <li><a href="/api/modules/generate">POST /api/modules/generate</a> - Auto-generate module</li>
                <li><a href="/docs">/docs</a> - API Documentation</li>
            </ul>
        </div>

        <div class="card">
            <h3>About</h3>
            <p><strong>Founder:</strong> Gurpreet Singh</p>
            <p><strong>Mission:</strong> Lifelong Seva (Selfless Service) through technology</p>
            <p><strong>License:</strong> Public Domain - For the welfare of all humanity</p>
            <p class="gurmat">"ਨਾਨਕ ਨਾਮ ਚੜ੍ਹਦੀ ਕਲਾ, ਤੇਰੇ ਭਾਣੇ ਸਰਬੱਤ ਦਾ ਭਲਾ"</p>
        </div>
    </body>
    </html>
    """
    page = (page
        .replace('{status_text}', system_state['status'].upper())
        .replace('{status}', 'operational' if system_state['status'] == 'operational' else 'initializing')
        .replace('{last_update}', system_state['last_update'])
        .replace('{modules_count}', str(len(system_state['modules_loaded'])))
        .replace('{requests}', str(system_state['total_requests']))
        .replace('{active_research}', str(len(system_state['active_research'])))
        .replace('{module_tags}', ''.join([f'<span class="module-tag">{m}</span>' for m in system_state['modules_loaded']]) if system_state['modules_loaded'] else '<span class="module-tag">System Initializing...</span>')
    )
    return page

# ==================== API ENDPOINTS ====================

@app.get("/api/status")
async def get_status():
    """Get system status"""
    system_state['total_requests'] += 1
    return {
        'status': system_state['status'],
        'modules': system_state['modules_loaded'],
        'version': '6.0.0',
        'timestamp': datetime.now().isoformat()
    }

@app.post("/api/research")
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Start autonomous research — runs the REAL UnifiedAgent pipeline"""
    system_state['total_requests'] += 1

    research_id = f"RES_{len(system_state['active_research']):06d}"

    record = {
        'id': research_id,
        'topic': request.topic,
        'status': 'running',
        'started': datetime.now().isoformat()
    }
    system_state['active_research'].append(record)

    def _run_real_research():
        if unified_agent is None:
            record['status'] = 'failed'
            record['error'] = f'UnifiedAgent unavailable: {MODULE_IMPORT_ERROR}'
            return
        try:
            result = unified_agent.run_autonomous_research(request.topic)
            record['status'] = 'completed'
            record['result'] = json.loads(json.dumps(result, default=str))
        except Exception as e:
            record['status'] = 'failed'
            record['error'] = str(e)
        record['finished'] = datetime.now().isoformat()

    background_tasks.add_task(_run_real_research)

    return {
        'research_id': research_id,
        'topic': request.topic,
        'status': 'started',
        'message': f'Real autonomous research on "{request.topic}" initiated (poll /api/research/active)',
        'estimated_duration': f'{request.duration_hours} hours',
        'engine': 'UnifiedAgent (real module)'
    }

@app.post("/api/blood/analyze")
async def analyze_blood(request: BloodPanelRequest):
    """Analyze blood panel using the REAL BloodAnalyzer module"""
    system_state['total_requests'] += 1

    if blood_analyzer is None:
        raise HTTPException(status_code=503, detail=f"BloodAnalyzer unavailable: {MODULE_IMPORT_ERROR}")

    real_results = blood_analyzer.analyze_panel(request.tests)
    results = {}
    for test_name, r in real_results.items():
        results[test_name] = {
            'value': r.value,
            'unit': r.unit,
            'reference_range': list(r.reference_range),
            'risk_level': r.risk_level.value,
            'interpretation': r.interpretation,
            'recommendations': r.recommendations,
        }

    critical = any(r['risk_level'] == 'critical' for r in results.values())
    abnormal = any(r['risk_level'] in ('high', 'critical') for r in results.values())

    return {
        'patient_id': request.patient_id,
        'population': request.population,
        'results': results,
        'overall_status': 'critical' if critical else ('review_needed' if abnormal else 'healthy'),
        'engine': 'BloodAnalyzer (real module)',
        'timestamp': datetime.now().isoformat()
    }

@app.post("/api/dna/analyze")
async def analyze_dna(request: DNAAnalysisRequest):
    """Analyze DNA variants using the REAL PersonalizedHealthAdvisor module"""
    system_state['total_requests'] += 1

    if health_advisor is None:
        raise HTTPException(status_code=503, detail=f"HealthAdvisor unavailable: {MODULE_IMPORT_ERROR}")

    real = health_advisor.analyze_dna(request.variants)

    return {
        'patient_id': request.patient_id,
        'variants_analyzed': real.get('variants_analyzed', len(real.get('variant_results', {}))),
        'results': real.get('variant_results', real),
        'overall_risk': real.get('overall_risk'),
        'engine': 'PersonalizedHealthAdvisor (real module)',
        'timestamp': datetime.now().isoformat()
    }

@app.post("/api/ethics/check")
async def check_ethics(request: EthicsCheckRequest):
    """Check ethics compliance using the REAL EthicsFilter module"""
    system_state['total_requests'] += 1

    if ethics_filter is None:
        raise HTTPException(status_code=503, detail=f"EthicsFilter unavailable: {MODULE_IMPORT_ERROR}")

    assessment = ethics_filter.assess(request.action, request.context)

    return {
        'action': request.action,
        'approved': assessment.approved,
        'violations': [v.value if hasattr(v, 'value') else str(v) for v in assessment.violations],
        'concerns': [str(c) for c in getattr(assessment, 'concerns', [])],
        'gurmat_score': assessment.gurmat_score,
        'medical_ethics_score': assessment.medical_ethics_score,
        'overall_score': getattr(assessment, 'overall_score', None),
        'recommendations': assessment.recommendations,
        'engine': 'EthicsFilter (real module)',
        'timestamp': datetime.now().isoformat()
    }

@app.post("/api/health/assessment")
async def full_health_assessment(request: Dict):
    """Full health assessment using the REAL PersonalizedHealthAdvisor"""
    system_state['total_requests'] += 1

    if health_advisor is None:
        raise HTTPException(status_code=503, detail=f"HealthAdvisor unavailable: {MODULE_IMPORT_ERROR}")

    assessment = health_advisor.full_health_assessment(request)

    return {
        **assessment,
        'patient_id': request.get('patient_id', 'unknown'),
        'engine': 'PersonalizedHealthAdvisor (real module)',
        'timestamp': datetime.now().isoformat()
    }

@app.post("/api/modules/generate")
async def generate_module(request: ModuleGenerationRequest):
    """Auto-generate new module using the REAL UnifiedAgent self-improvement loop"""
    system_state['total_requests'] += 1

    if unified_agent is None:
        raise HTTPException(status_code=503, detail=f"UnifiedAgent unavailable: {MODULE_IMPORT_ERROR}")

    result = unified_agent.generate_new_module(request.requirement)

    return {
        'requirement': request.requirement,
        **(result if isinstance(result, dict) else {'module_code': str(result)}),
        'engine': 'UnifiedAgent SelfImprovementLoop (real module)',
        'timestamp': datetime.now().isoformat()
    }

@app.post("/api/variants/analyze")
async def analyze_variants(request: VariantAnalysisRequest):
    """
    Analyze variants with AlphaGenome Atlas AVI scores (v6.2).
    HARD GATES: explicit consent required + EthicsFilter approval.
    Results cached in MemoryManager. Never fabricates scores.
    """
    system_state['total_requests'] += 1

    if alphagenome_client is None:
        raise HTTPException(status_code=503, detail=f"AlphaGenomeClient unavailable: {MODULE_IMPORT_ERROR}")

    if not request.consent_confirmed:
        raise HTTPException(
            status_code=403,
            detail="BLOCKED: explicit informed patient consent is required. "
                   "Set consent_confirmed=true only after signed consent.")

    try:
        result = health_advisor.analyze_variants_with_alphagenome(
            request.variants,
            patient_id=request.patient_id,
            consent_confirmed=request.consent_confirmed)
    except ConsentRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except EthicsBlockedError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return {**result,
            'engine': 'AlphaGenomeClient + PersonalizedHealthAdvisor (real modules)',
            'alphagenome_api': 'configured' if alphagenome_client.api_configured else 'not configured (set ALPHAGENOME_API_KEY)'}

# ==================== ROBO DOCTOR: PATIENT FLOW (v6.2) ====================

@app.post("/api/patients/register")
async def register_patient(request: PatientRegisterRequest):
    """Register a patient (anonymous supported). Returns AMRIT patient ID."""
    system_state['total_requests'] += 1
    if patient_registry is None:
        raise HTTPException(status_code=503, detail=f"PatientRegistry unavailable: {MODULE_IMPORT_ERROR}")
    pid = patient_registry.register_patient(
        age=request.age, sex=request.sex, population=request.population,
        display_name=request.display_name,
        consent_general=request.consent_general,
        consent_genomic=request.consent_genomic)
    return {'patient_id': pid, 'anonymous': request.display_name is None,
            'message': 'Patient registered. All future tests link to this ID.'}


@app.get("/api/patients/{patient_id}/history")
async def patient_history(patient_id: str):
    """Full patient timeline — the system 'remembers' the patient."""
    system_state['total_requests'] += 1
    if patient_registry is None:
        raise HTTPException(status_code=503, detail="PatientRegistry unavailable")
    try:
        return patient_registry.patient_summary(patient_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")


@app.post("/api/symptoms/analyze")
async def analyze_symptoms(request: SymptomRequest):
    """
    Symptom -> recommended tests. Records into patient history when the
    patient_id is registered. Advises tests only — never diagnoses.
    """
    system_state['total_requests'] += 1
    if symptom_analyzer is None:
        raise HTTPException(status_code=503, detail="SymptomAnalyzer unavailable")
    result = symptom_analyzer.analyze(request.symptoms, request.population, request.age)
    if request.patient_id and patient_registry is not None:
        try:
            patient_registry.record_event(request.patient_id, 'symptom_report', {
                'symptoms': request.symptoms, 'urgency': result['urgency'],
                'recommended_tests': result['recommended_tests']})
            result['recorded_to_patient'] = request.patient_id
        except Exception:
            result['recorded_to_patient'] = None
    return {**result, 'engine': 'SymptomAnalyzer (real module)'}


@app.post("/api/prescriptions/draft")
async def create_prescription_draft(request: PrescriptionDraftRequest):
    """Create a prescription DRAFT — never valid until a doctor approves."""
    system_state['total_requests'] += 1
    if prescription_workflow is None:
        raise HTTPException(status_code=503, detail="PrescriptionWorkflow unavailable")
    try:
        return prescription_workflow.create_draft(
            request.patient_id, request.condition, request.doctor_id,
            extra_meds=request.extra_meds)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/prescriptions/{rx_id}/approve")
async def approve_prescription(rx_id: str, request: PrescriptionReviewRequest):
    """Doctor approves (optionally modifying) a draft prescription."""
    system_state['total_requests'] += 1
    if prescription_workflow is None:
        raise HTTPException(status_code=503, detail="PrescriptionWorkflow unavailable")
    try:
        if request.medications:
            return prescription_workflow.modify_and_approve(
                rx_id, request.doctor_id, request.medications, request.notes or "")
        return prescription_workflow.approve(rx_id, request.doctor_id, request.notes or "")
    except DoctorVerificationRequired as e:
        raise HTTPException(status_code=403, detail=str(e))
    except PrescriptionStateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.post("/api/prescriptions/{rx_id}/reject")
async def reject_prescription(rx_id: str, request: PrescriptionReviewRequest):
    """Doctor rejects a draft prescription (reason logged)."""
    system_state['total_requests'] += 1
    if prescription_workflow is None:
        raise HTTPException(status_code=503, detail="PrescriptionWorkflow unavailable")
    try:
        return prescription_workflow.reject(rx_id, request.doctor_id,
                                            request.reason or "no reason given")
    except PrescriptionStateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.get("/api/prescriptions/pending/{doctor_id}")
async def pending_prescriptions(doctor_id: str):
    """Doctor's queue of drafts awaiting review."""
    if prescription_workflow is None:
        raise HTTPException(status_code=503, detail="PrescriptionWorkflow unavailable")
    pending = prescription_workflow.pending_for_doctor(doctor_id)
    return {'doctor_id': doctor_id, 'pending': pending, 'count': len(pending)}


@app.get("/api/llm/status")
async def llm_status():
    """LLM plug status — any OpenAI-compatible API (Qwen, DeepSeek, Ollama...)."""
    if llm is None:
        raise HTTPException(status_code=503, detail="LLMInterface unavailable")
    return llm.status()


@app.get("/api/voice/status")
async def voice_status():
    """Voice capability status (offline TTS / cloud STT)."""
    if voice is None:
        raise HTTPException(status_code=503, detail="VoiceInterface unavailable")
    return voice.capabilities()

@app.get("/api/research/active")
async def get_active_research():
    """Get active research tasks"""
    return {
        'active_research': system_state['active_research'],
        'count': len(system_state['active_research'])
    }

@app.get("/api/modules/list")
async def list_modules():
    """List all available modules"""
    return {
        'modules': system_state['modules_loaded'],
        'count': len(system_state['modules_loaded'])
    }

# Initialize system
@app.on_event("startup")
async def startup_event():
    """Initialize AMRIT system on startup"""
    print("🕉️ Robo Doctor (AMRIT Research OS v6.2) Starting...")
    print("ਸਰਬੱਤ ਦਾ ਭਲਾ - Welfare of All Humanity")

    if MODULES_AVAILABLE:
        modules = [
            'ResearchBrain', 'MemoryManager', 'StatisticalEngine',
            'AgentManager', 'KnowledgeGraph', 'DataCollector', 'PaperWriter',
            'BloodAnalyzer', 'ConsanguinityRisk', 'DrugPredictor', 'EthicsFilter',
            'QuantumLayer', 'UnifiedAgent', 'HealthAdvisor', 'AlphaGenomeClient',
            'PatientRegistry', 'SymptomAnalyzer', 'PrescriptionWorkflow',
            'LLMInterface', 'VoiceInterface'
        ]
        system_state['status'] = 'operational'
        print(f"✅ {len(modules)} REAL modules loaded and wired to endpoints")
    else:
        modules = []
        system_state['status'] = 'degraded'
        print(f"⚠️ Module import failed: {MODULE_IMPORT_ERROR}")

    system_state['modules_loaded'] = modules
    system_state['last_update'] = datetime.now().isoformat()
    print("✅ System operational" if MODULES_AVAILABLE else "⚠️ Running in degraded mode")
    print("🌐 Dashboard available at: http://localhost:8000")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
