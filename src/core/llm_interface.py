"""
Robo Doctor - Pluggable LLM Interface (v6.2)
=============================================
Open option for ANY LLM provider via the OpenAI-compatible chat API.

Works with (no code changes, just env config):
  - Qwen (Alibaba DashScope)      base_url=https://dashscope.aliyuncs.com/compatible-mode/v1
  - DeepSeek                      base_url=https://api.deepseek.com/v1
  - OpenRouter (100+ models)      base_url=https://openrouter.ai/api/v1
  - Ollama (fully offline, free)  base_url=http://localhost:11434/v1
  - OpenAI                        base_url=https://api.openai.com/v1

Design: honesty first — if no LLM is configured, every call says so.
The rest of Robo Doctor works fully offline without an LLM.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    requests = None


class LLMNotConfigured(Exception):
    pass


class LLMInterface:
    """
    Provider-agnostic LLM chat interface.

    Config via environment variables:
        ROBO_LLM_API_KEY   - API key for the provider
        ROBO_LLM_BASE_URL  - OpenAI-compatible endpoint
        ROBO_LLM_MODEL     - model name (e.g. 'qwen-plus', 'llama3.1')

    Usage:
        llm = LLMInterface()
        if llm.configured:
            answer = llm.chat([{"role": "user", "content": "..."}])
    """

    def __init__(self, api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 model: Optional[str] = None,
                 timeout: int = 60):
        self.api_key = api_key or os.environ.get("ROBO_LLM_API_KEY")
        self.base_url = (base_url or os.environ.get("ROBO_LLM_BASE_URL")
                         or "http://localhost:11434/v1")  # default: local Ollama
        self.model = model or os.environ.get("ROBO_LLM_MODEL", "qwen-plus")
        self.timeout = timeout
        self.call_log: List[Dict] = []

    @property
    def configured(self) -> bool:
        # Ollama local needs no key; remote providers do
        if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
            return requests is not None
        return bool(self.api_key) and requests is not None

    def status(self) -> Dict:
        return {
            "configured": self.configured,
            "base_url": self.base_url,
            "model": self.model,
            "note": ("Ready" if self.configured else
                     "Set ROBO_LLM_API_KEY / ROBO_LLM_BASE_URL / ROBO_LLM_MODEL. "
                     "Robo Doctor's core (tests, DNA, ethics, registry) works "
                     "without any LLM."),
        }

    def chat(self, messages: List[Dict], temperature: float = 0.3,
             max_tokens: int = 2000) -> str:
        """Send a chat request. Raises LLMNotConfigured if not set up."""
        if not self.configured:
            raise LLMNotConfigured(
                "No LLM configured. Set ROBO_LLM_API_KEY and ROBO_LLM_BASE_URL "
                "(or run local Ollama). No fake answer was generated.")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {"model": self.model, "messages": messages,
                   "temperature": temperature, "max_tokens": max_tokens}
        resp = requests.post(f"{self.base_url.rstrip('/')}/chat/completions",
                             headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        answer = data["choices"][0]["message"]["content"]
        self.call_log.append({"model": self.model, "at": datetime.now().isoformat(),
                              "tokens": data.get("usage", {}).get("total_tokens")})
        return answer

    def summarize_patient_history(self, history: List[Dict]) -> str:
        """LLM-assisted patient history summary (for the doctor's review)."""
        prompt = (
            "You are assisting a licensed physician. Summarize this patient's "
            "timeline in 5 bullet points, flag any concerning trends, and "
            "explicitly state this is a draft for doctor review only.\n\n"
            f"History JSON:\n{json.dumps(history, default=str)[:4000]}"
        )
        return self.chat([{"role": "user", "content": prompt}])
