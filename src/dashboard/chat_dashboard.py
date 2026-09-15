"""
AMRIT Smart Chat Dashboard v6.1
Single chat interface that auto-detects and routes to correct module
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
import asyncio
from datetime import datetime
from typing import Dict, List

app = FastAPI(title="AMRIT Smart Chat Dashboard v6.1")

# Store chat history
chat_sessions = {}
active_connections = {}

# Module router - detects intent and routes to correct module
class ModuleRouter:
    """Auto-detect user intent and route to appropriate module"""

    MODULES = {
        'blood': {
            'keywords': ['blood', 'glucose', 'cholesterol', 'hemoglobin', 'hba1c', 'vitamin', 'iron', 'creatinine'],
            'module': 'BloodAnalyzer',
            'description': 'Analyze blood test results'
        },
        'dna': {
            'keywords': ['dna', 'gene', 'genetic', 'variant', 'apoe', 'mthfr', 'brca', 'carrier', 'screening'],
            'module': 'HealthAdvisor',
            'description': 'DNA analysis and genetic risk'
        },
        'consanguinity': {
            'keywords': ['cousin', 'marriage', 'consanguinity', 'thalassemia', 'sickle', 'carrier'],
            'module': 'ConsanguinityRisk',
            'description': 'Consanguinity risk assessment'
        },
        'drug': {
            'keywords': ['drug', 'medicine', 'pharmacogenomics', 'cyp2d6', 'warfarin', 'clopidogrel', 'metformin'],
            'module': 'DrugPredictor',
            'description': 'Drug response prediction'
        },
        'research': {
            'keywords': ['research', 'paper', 'hypothesis', 'study', 'literature', 'pubmed', 'arxiv'],
            'module': 'UnifiedAgent',
            'description': 'Autonomous research'
        },
        'ethics': {
            'keywords': ['ethics', 'moral', 'consent', 'eugenics', 'gurmat', 'sarbat da bhala'],
            'module': 'EthicsFilter',
            'description': 'Ethics assessment'
        },
        'pandemic': {
            'keywords': ['pandemic', 'outbreak', 'covid', 'virus', 'infection', 'disease spread'],
            'module': 'PredictionEngine',
            'description': 'Pandemic prediction'
        },
        'health': {
            'keywords': ['health', 'diet', 'exercise', 'lifestyle', 'supplement', 'screening', 'recommendation'],
            'module': 'HealthAdvisor',
            'description': 'Personalized health advice'
        },
        'team': {
            'keywords': ['team', 'agent', 'swarm', 'debate', 'collaborate', 'harness'],
            'module': 'HarnessTeams',
            'description': 'Multi-agent team configuration'
        },
        'quantum': {
            'keywords': ['quantum', 'qubit', 'grover', 'vqe', 'molecular', 'binding'],
            'module': 'QuantumLayer',
            'description': 'Quantum biology simulation'
        }
    }

    def detect_intent(self, message: str) -> Dict:
        """Detect user intent from message"""
        message_lower = message.lower()
        scores = {}

        for module_key, module_info in self.MODULES.items():
            score = 0
            for keyword in module_info['keywords']:
                if keyword in message_lower:
                    score += 1
            if score > 0:
                scores[module_key] = score

        if scores:
            best_match = max(scores, key=scores.get)
            return {
                'intent': best_match,
                'module': self.MODULES[best_match]['module'],
                'description': self.MODULES[best_match]['description'],
                'confidence': scores[best_match] / len(self.MODULES[best_match]['keywords']),
                'all_matches': scores
            }

        return {
            'intent': 'general',
            'module': 'UnifiedAgent',
            'description': 'General assistance',
            'confidence': 0.0,
            'all_matches': {}
        }

    def generate_response(self, intent: str, message: str) -> str:
        """Generate response based on detected intent"""
        responses = {
            'blood': "I'll analyze your blood test results. Please provide your test values (e.g., glucose: 95, hba1c: 5.8).",
            'dna': "I'll analyze your genetic variants. Please share your DNA test results (e.g., APOE4: 1_copy, MTHFR: CT).",
            'consanguinity': "I'll assess consanguinity risks. Please specify the relationship type (e.g., first cousin, double first cousin).",
            'drug': "I'll predict drug responses based on your pharmacogenomic profile. Which medication are you interested in?",
            'research': "I'll start autonomous research on your topic. What would you like to research?",
            'ethics': "I'll assess the ethical implications. Please describe the action or research proposal.",
            'pandemic': "I'll analyze pandemic risk factors. Please provide population data or location.",
            'health': "I'll provide personalized health recommendations. Please share your health profile.",
            'team': "I'll configure an optimal agent team for your task. What type of task do you have?",
            'quantum': "I'll run quantum biology simulations. What biological system would you like to model?"
        }

        return responses.get(intent, "I'm here to help! I can assist with blood analysis, DNA testing, drug predictions, research, ethics review, pandemic modeling, health advice, or multi-agent teams. What do you need?")

router = ModuleRouter()

# HTML Template for Chat Dashboard
CHAT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AMRIT Smart Chat v6.1</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 15px 30px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid rgba(255,255,255,0.2);
        }
        .header h1 {
            color: white;
            font-size: 24px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .header .gurmat {
            color: rgba(255,255,255,0.8);
            font-size: 12px;
            font-style: italic;
        }
        .status {
            display: flex;
            align-items: center;
            gap: 8px;
            color: white;
            font-size: 14px;
        }
        .status-dot {
            width: 10px;
            height: 10px;
            background: #4ade80;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .main-container {
            display: flex;
            flex: 1;
            overflow: hidden;
        }
        .sidebar {
            width: 280px;
            background: rgba(0,0,0,0.2);
            backdrop-filter: blur(10px);
            padding: 20px;
            overflow-y: auto;
            border-right: 1px solid rgba(255,255,255,0.1);
        }
        .sidebar h3 {
            color: white;
            font-size: 14px;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .module-card {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.3s;
            border: 1px solid transparent;
        }
        .module-card:hover {
            background: rgba(255,255,255,0.2);
            border-color: rgba(255,255,255,0.3);
            transform: translateX(5px);
        }
        .module-card.active {
            background: rgba(102, 126, 234, 0.5);
            border-color: #667eea;
        }
        .module-card h4 {
            color: white;
            font-size: 13px;
            margin-bottom: 4px;
        }
        .module-card p {
            color: rgba(255,255,255,0.6);
            font-size: 11px;
        }
        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: rgba(255,255,255,0.95);
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 30px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .message {
            max-width: 80%;
            padding: 15px 20px;
            border-radius: 20px;
            animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.user {
            align-self: flex-end;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-bottom-right-radius: 5px;
        }
        .message.bot {
            align-self: flex-start;
            background: #f3f4f6;
            color: #1f2937;
            border-bottom-left-radius: 5px;
        }
        .message .timestamp {
            font-size: 10px;
            opacity: 0.6;
            margin-top: 5px;
        }
        .message .intent-tag {
            display: inline-block;
            background: rgba(102, 126, 234, 0.2);
            color: #667eea;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            margin-bottom: 5px;
        }
        .input-area {
            padding: 20px 30px;
            background: white;
            border-top: 1px solid #e5e7eb;
            display: flex;
            gap: 15px;
            align-items: center;
        }
        .input-area input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e5e7eb;
            border-radius: 30px;
            font-size: 15px;
            outline: none;
            transition: border-color 0.3s;
        }
        .input-area input:focus {
            border-color: #667eea;
        }
        .input-area button {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 30px;
            font-size: 15px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .input-area button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        .typing-indicator {
            display: none;
            align-self: flex-start;
            background: #f3f4f6;
            padding: 15px 20px;
            border-radius: 20px;
            border-bottom-left-radius: 5px;
        }
        .typing-indicator.active {
            display: flex;
            gap: 5px;
        }
        .typing-indicator span {
            width: 8px;
            height: 8px;
            background: #667eea;
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out;
        }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        .welcome-message {
            text-align: center;
            padding: 40px;
            color: #6b7280;
        }
        .welcome-message h2 {
            color: #1f2937;
            margin-bottom: 10px;
        }
        .quick-actions {
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        .quick-action {
            background: rgba(102, 126, 234, 0.1);
            color: #667eea;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.3s;
            border: 1px solid rgba(102, 126, 234, 0.2);
        }
        .quick-action:hover {
            background: #667eea;
            color: white;
        }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>🕉️ AMRIT Smart Chat v6.1</h1>
            <span class="gurmat">"ਸਰਬੱਤ ਦਾ ਭਲਾ" - Welfare of All Humanity</span>
        </div>
        <div class="status">
            <div class="status-dot"></div>
            <span>System Online</span>
        </div>
    </div>

    <div class="main-container">
        <div class="sidebar">
            <h3>🧠 Available Modules</h3>
            <div class="module-card" onclick="sendQuick('Analyze my blood: glucose 95, hba1c 5.8')">
                <h4>🩸 Blood Analyzer</h4>
                <p>30+ tests with 4-level detection</p>
            </div>
            <div class="module-card" onclick="sendQuick('My DNA: APOE4 1_copy, MTHFR CT')">
                <h4>🧬 DNA Analysis</h4>
                <p>10 variants, personalized risk</p>
            </div>
            <div class="module-card" onclick="sendQuick('First cousin marriage risk')">
                <h4>👨‍👩‍👧‍👦 Consanguinity</h4>
                <p>20 diseases, 6 relationships</p>
            </div>
            <div class="module-card" onclick="sendQuick('Drug prediction for warfarin')">
                <h4>💊 Drug Predictor</h4>
                <p>13 biomarkers, 10 drugs</p>
            </div>
            <div class="module-card" onclick="sendQuick('Research on diabetes genetics')">
                <h4>🔬 Autonomous Research</h4>
                <p>5 agents, self-improving</p>
            </div>
            <div class="module-card" onclick="sendQuick('Ethics check for genetic screening')">
                <h4>⚖️ Ethics Filter</h4>
                <p>Gurmat + Medical ethics</p>
            </div>
            <div class="module-card" onclick="sendQuick('Pandemic risk for Delhi')">
                <h4>🌍 Pandemic Prediction</h4>
                <p>Risk assessment, mitigation</p>
            </div>
            <div class="module-card" onclick="sendQuick('Health advice for South Asian')">
                <h4>🏥 Health Advisor</h4>
                <p>DNA + Blood + Environment</p>
            </div>
            <div class="module-card" onclick="sendQuick('Configure agent team for research')">
                <h4>👥 Harness Teams</h4>
                <p>6 patterns, auto-generation</p>
            </div>
        </div>

        <div class="chat-area">
            <div class="messages" id="messages">
                <div class="welcome-message">
                    <h2>Welcome to AMRIT Research OS v6.1</h2>
                    <p>I am your intelligent medical research assistant. I can analyze blood tests, DNA, predict drug responses, conduct autonomous research, check ethics, and much more.</p>
                    <p style="margin-top: 10px; font-size: 12px; color: #9ca3af;">Just type naturally - I will detect what you need!</p>
                    <div class="quick-actions">
                        <span class="quick-action" onclick="sendQuick('My blood glucose is 110, is that normal?')">Blood Test</span>
                        <span class="quick-action" onclick="sendQuick('Research diabetes in South Asians')">Research</span>
                        <span class="quick-action" onclick="sendQuick('Check ethics of genetic screening')">Ethics</span>
                        <span class="quick-action" onclick="sendQuick('Team for pandemic prediction')">Team</span>
                    </div>
                </div>
            </div>
            <div class="typing-indicator" id="typing">
                <span></span><span></span><span></span>
            </div>
            <div class="input-area">
                <input type="text" id="messageInput" placeholder="Type your health query, research topic, or any question..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>

    <script>
        const ws = new WebSocket('ws://' + window.location.host + '/ws/chat');
        const messagesDiv = document.getElementById('messages');
        const typingDiv = document.getElementById('typing');
        const input = document.getElementById('messageInput');

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            hideTyping();

            if (data.type === 'bot') {
                addMessage(data.content, 'bot', data.intent, data.module);
            } else if (data.type === 'user') {
                addMessage(data.content, 'user');
            }
        };

        function addMessage(content, sender, intent, module) {
            const div = document.createElement('div');
            div.className = 'message ' + sender;

            let html = '';
            if (intent && module) {
                html += '<span class="intent-tag">' + module + '</span><br>';
            }
            html += content.replace(/\\n/g, '<br>');
            html += '<div class="timestamp">' + new Date().toLocaleTimeString() + '</div>';

            div.innerHTML = html;
            messagesDiv.appendChild(div);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function showTyping() {
            typingDiv.classList.add('active');
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function hideTyping() {
            typingDiv.classList.remove('active');
        }

        function sendMessage() {
            const text = input.value.trim();
            if (!text) return;

            addMessage(text, 'user');
            input.value = '';
            showTyping();

            ws.send(JSON.stringify({
                message: text,
                timestamp: new Date().toISOString()
            }));
        }

        function sendQuick(text) {
            input.value = text;
            sendMessage();
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        ws.onopen = function() {
            console.log('Connected to AMRIT');
        };
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def chat_dashboard():
    """Main chat dashboard"""
    return CHAT_HTML

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket for real-time chat"""
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            user_message = data.get('message', '')

            # Detect intent
            intent_data = router.detect_intent(user_message)

            # Generate response based on intent
            response_text = router.generate_response(intent_data['intent'], user_message)

            # Simulate processing delay
            await asyncio.sleep(1)

            # Send response
            await websocket.send_json({
                'type': 'bot',
                'content': response_text,
                'intent': intent_data['intent'],
                'module': intent_data['module'],
                'confidence': intent_data['confidence'],
                'timestamp': datetime.now().isoformat()
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            'type': 'bot',
            'content': 'Error: %s' % str(e),
            'timestamp': datetime.now().isoformat()
        })

# API endpoints for direct module access
@app.post("/api/chat/analyze")
async def analyze_chat(message: str):
    """Direct chat analysis endpoint"""
    intent_data = router.detect_intent(message)
    return {
        'intent': intent_data['intent'],
        'module': intent_data['module'],
        'confidence': intent_data['confidence'],
        'suggested_action': router.generate_response(intent_data['intent'], message)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
