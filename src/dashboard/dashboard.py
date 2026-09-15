
"""
AMRIT Dashboard - FastAPI Web Server
Terminal live logs + Web interface
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import asyncio
import os
from datetime import datetime
import json

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

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
    from src.dashboard.chat_engine import ChatEngine
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
    chat_engine = ChatEngine(
        patient_registry=patient_registry,
        symptom_analyzer=symptom_analyzer,
        blood_analyzer=blood_analyzer,
        prescription_workflow=prescription_workflow,
        llm=llm,
        health_advisor=health_advisor)
    chat_sessions: Dict[str, Dict] = {}
else:
    memory_manager = ethics_filter = blood_analyzer = None
    alphagenome_client = health_advisor = research_brain = None
    statistical_engine = agent_manager = unified_agent = None
    patient_registry = symptom_analyzer = prescription_workflow = None
    llm = voice = chat_engine = None
    chat_sessions = {}

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

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

# ==================== ROOT ENDPOINT ====================

# PWA static assets (manifest, icons)
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/sw.js")
async def service_worker():
    """Service worker must be served from root scope for full PWA control."""
    return FileResponse(os.path.join(STATIC_DIR, 'sw.js'),
                        media_type='application/javascript')

@app.get("/", response_class=HTMLResponse)
async def root():
    """Robo Doctor Clinic UI — chat-first, works offline (installable PWA)"""
    page = """<!DOCTYPE html>
<html>
<head>
    <title>Robo Doctor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#0d7a5f">
    <link rel="manifest" href="/static/manifest.webmanifest">
    <link rel="apple-touch-icon" href="/static/icons/icon-192.png">
    <script>
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js').catch(() => {});
        }
    </script>
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, "Segoe UI", Arial, sans-serif; margin: 0;
               background: #0d1117; color: #e6edf3; }
        header { background: linear-gradient(135deg, #0d7a5f, #0a5c48); color: white;
                 padding: 14px 22px; display: flex; align-items: center; gap: 14px;
                 position: sticky; top: 0; }
        header img { width: 44px; height: 44px; border-radius: 10px; }
        header h1 { font-size: 20px; margin: 0; }
        header .tag { font-size: 12px; opacity: .85; margin: 2px 0 0; }
        .pill { margin-left: auto; background: #1f6f43; padding: 4px 12px;
                border-radius: 20px; font-size: 12px; }
        .pill.warn { background: #9e6a03; }
        main { max-width: 860px; margin: 0 auto; padding: 18px; }
        #chat { background: #161b22; border: 1px solid #30363d; border-radius: 14px;
                padding: 16px; height: 52vh; overflow-y: auto; }
        .msg { margin: 10px 0; padding: 10px 14px; border-radius: 12px;
               max-width: 85%; white-space: pre-wrap; line-height: 1.45; font-size: 15px; }
        .user { background: #1f6feb; margin-left: auto; }
        .robo { background: #21262d; border: 1px solid #30363d; }
        .robo.err { border-color: #cf222e; }
        .quick { display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0; }
        .quick button { background: #21262d; color: #e6edf3; border: 1px solid #30363d;
                padding: 8px 14px; border-radius: 20px; cursor: pointer; font-size: 13px; }
        .quick button:hover { border-color: #0d7a5f; }
        #inputrow { display: flex; gap: 10px; margin-top: 6px; }
        #msg { flex: 1; background: #161b22; border: 1px solid #30363d; color: #e6edf3;
               padding: 13px 16px; border-radius: 24px; font-size: 15px; }
        #msg:focus { outline: none; border-color: #0d7a5f; }
        #send { background: #0d7a5f; color: white; border: none; padding: 0 24px;
                border-radius: 24px; font-size: 15px; cursor: pointer; }
        #send:hover { background: #0f9669; }
        .meta { text-align: center; color: #8b949e; font-size: 12px; margin-top: 16px;
                line-height: 1.7; }
        .rule { color: #f85149; font-size: 12px; text-align: center; margin-top: 10px; }
    </style>
</head>
<body>
<header>
    <img src="/static/icons/icon-192.png" alt="Robo Doctor">
    <div>
        <h1>Robo Doctor</h1>
        <p class="tag">Seva Healthcare Assistant · ਸਰਬੱਤ ਦਾ ਭਲਾ</p>
    </div>
    <span class="pill" id="statuspill">…</span>
</header>
<main>
    <div id="chat">
        <div class="msg robo">Sat Sri Akal ji. I am Robo Doctor — your clinic assistant.
Type <b>help</b> to see what I understand, or tap a quick action below.
I remember every patient, and a licensed doctor approves every prescription.</div>
    </div>
    <div class="quick">
        <button onclick="quick('help')">❓ Help</button>
        <button onclick="quick('register patient age ')">🧍 Register patient</button>
        <button onclick="quick('symptoms: ')">🩺 Symptoms → tests</button>
        <button onclick="quick('blood: ')">🩸 Blood results</button>
        <button onclick="quick('pending prescriptions for ')">📋 Pending Rx</button>
        <button onclick="quick('status')">⚙️ Status</button>
    </div>
    <div id="inputrow">
        <input id="msg" placeholder="Type here… e.g. symptoms: fatigue, excessive thirst"
               onkeydown="if(event.key==='Enter')send()">
        <button id="send" onclick="send()">Send</button>
    </div>
    <p class="rule">HARD RULE: no prescription is final without a licensed doctor's approval.</p>
    <p class="meta" id="meta"></p>
</main>
<script>
const chat = document.getElementById('chat');
const box = document.getElementById('msg');
function add(text, cls) {
    const d = document.createElement('div');
    d.className = 'msg ' + cls;
    d.textContent = text;
    chat.appendChild(d);
    chat.scrollTop = chat.scrollHeight;
}
function quick(t) { box.value = t; box.focus(); if (t === 'help' || t === 'status') send(); }
async function send() {
    const text = box.value.trim();
    if (!text) return;
    add(text, 'user');
    box.value = '';
    add('…', 'robo');
    const thinking = chat.lastChild;
    try {
        const r = await fetch('/api/chat', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: text, session_id: 'clinic-ui'})
        });
        const d = await r.json();
        thinking.textContent = d.reply || ('Error: ' + (d.detail || r.status));
        if (d.error) thinking.classList.add('err');
    } catch (e) {
        thinking.textContent = 'Cannot reach server. Is Robo Doctor running?';
        thinking.classList.add('err');
    }
}
fetch('/api/status').then(r => r.json()).then(d => {
    const p = document.getElementById('statuspill');
    p.textContent = d.status === 'operational' ? '● operational' : '● ' + d.status;
    if (d.status !== 'operational') p.classList.add('warn');
    document.getElementById('meta').textContent =
        d.modules.length + ' real modules · offline-first · patient data stays on this machine';
}).catch(() => {});
fetch('/api/llm/status').then(r => r.json()).then(d => {
    document.getElementById('meta').textContent +=
        ' · LLM: ' + (d.configured ? d.model : 'offline rules (plug any API/Ollama)');
}).catch(() => {});
</script>
</body>
</html>"""
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


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Chat with Robo Doctor — type commands in plain English.
    Works offline with rule parser; understands free text when an LLM
    (Ollama local or any OpenAI-compatible API) is configured.
    Same safety gates as the API: consent, ethics, doctor approval.
    """
    system_state['total_requests'] += 1
    if chat_engine is None:
        raise HTTPException(status_code=503, detail="ChatEngine unavailable")
    session = chat_sessions.setdefault(request.session_id, {})
    result = chat_engine.handle(request.message, session)
    # keep lightweight context for follow-up messages
    if result.get('data', {}) and result['data'].get('patient_id'):
        session['patient_id'] = result['data']['patient_id']
    return result

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
