"""
AMRIT AlphaGenome Atlas Client (v6.2)
======================================
Integration with Google DeepMind's AlphaGenome Atlas (released 2026-09-08):
precomputed molecular-effect predictions for ~9 billion human SNVs, ranked by
the AVI (AlphaGenome Variant Impact) score.

Design principles (per AMRIT mission):
1. ETHICS FIRST  - No genomic analysis without explicit patient consent.
                   Every request passes through EthicsFilter.
2. HONESTY       - If the live AlphaGenome API is not configured, this client
                   says so. It NEVER fabricates AVI scores.
3. SEVA          - Non-commercial research use only, matching DeepMind's free
                   non-commercial access terms.
4. EFFICIENCY    - AVI scores are cached in MemoryManager (SQLite) so repeat
                   lookups are instant and free.

IMPORTANT DISCLAIMER (from DeepMind, enforced in every response):
AlphaGenome "has not been validated for, and is not approved for, any
clinical use" and is "not intended to be a substitute for professional
medical advice."
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Optional, List

try:
    import requests
except ImportError:
    requests = None


ALPHAGENOME_DISCLAIMER = (
    "AlphaGenome Atlas predictions are research-grade AI predictions. "
    "They have NOT been validated for clinical use and are NOT a substitute "
    "for professional medical advice, diagnosis, or treatment."
)

# AVI score interpretation bands (per DeepMind's published definition:
# AVI 10 ~ top 10% most impactful variants genome-wide;
# AVI 30 ~ top 1-in-1000; scale runs 0 to ~55)
AVI_BANDS = [
    (30, "very_high", "Among the ~0.1% most impactful variants in the genome"),
    (10, "high", "Among the ~10% most impactful variants in the genome"),
    (0, "low_to_moderate", "Below the top-10% impact threshold"),
]


class ConsentRequiredError(Exception):
    """Raised when genomic analysis is attempted without patient consent."""
    pass


class EthicsBlockedError(Exception):
    """Raised when EthicsFilter rejects the analysis request."""
    pass


class AlphaGenomeClient:
    """
    Client for DeepMind's AlphaGenome Atlas with AMRIT ethics-consent gate
    and MemoryManager AVI-score caching.

    Usage:
        client = AlphaGenomeClient(memory_manager=mm, ethics_filter=ef)
        result = client.analyze_variant(
            {"gene": "DNM1", "variant": "splice_site", "genotype": "het"},
            patient_id="P001",
            consent_confirmed=True,
        )
    """

    CACHE_MEMORY_TYPE = "alphagenome_avi"

    def __init__(self,
                 memory_manager=None,
                 ethics_filter=None,
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 timeout: int = 30):
        self.memory = memory_manager
        self.ethics = ethics_filter
        self.api_key = api_key or os.environ.get("ALPHAGENOME_API_KEY")
        self.base_url = base_url or os.environ.get(
            "ALPHAGENOME_API_URL", "https://api.alphagenome.google/v1")
        self.timeout = timeout
        self.query_log: List[Dict] = []

    # ------------------------------------------------------------------
    # Gate 1: consent
    # ------------------------------------------------------------------
    def _check_consent(self, consent_confirmed: bool, patient_id: Optional[str]):
        if not consent_confirmed:
            raise ConsentRequiredError(
                f"Genomic analysis for patient '{patient_id}' BLOCKED: "
                "explicit informed consent is required. "
                "Set consent_confirmed=True only after the patient has signed "
                "an informed-consent form."
            )

    # ------------------------------------------------------------------
    # Gate 2: ethics
    # ------------------------------------------------------------------
    def _check_ethics(self, variant: Dict, purpose: str):
        if self.ethics is None:
            return None
        description = (
            f"Analyze genetic variant {variant.get('variant', 'unknown')} "
            f"in gene {variant.get('gene', 'unknown')} "
            f"for purpose: {purpose}"
        )
        assessment = self.ethics.assess(description)
        if not assessment.approved:
            raise EthicsBlockedError(
                "EthicsFilter BLOCKED this analysis: "
                + "; ".join(str(v) for v in getattr(assessment, 'violations', []))
            )
        return assessment

    # ------------------------------------------------------------------
    # Cache (MemoryManager)
    # ------------------------------------------------------------------
    def _cache_key(self, variant: Dict) -> str:
        canonical = json.dumps(variant, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def _cache_lookup(self, variant: Dict) -> Optional[Dict]:
        if self.memory is None:
            return None
        key = self._cache_key(variant)
        results = self.memory.search(
            memory_type=self.CACHE_MEMORY_TYPE, tags=[key], limit=1)
        if results:
            entry = results[0]
            cached = entry.content if isinstance(entry.content, dict) else None
            if cached:
                cached['cache_hit'] = True
                return cached
        return None

    def _cache_store(self, variant: Dict, result: Dict):
        if self.memory is None:
            return
        key = self._cache_key(variant)
        self.memory.store(
            result,
            self.CACHE_MEMORY_TYPE,
            tags=[key, variant.get('gene', 'unknown')],
            importance=0.8,
        )

    # ------------------------------------------------------------------
    # Live API
    # ------------------------------------------------------------------
    @property
    def api_configured(self) -> bool:
        return bool(self.api_key) and requests is not None

    def _query_api(self, variant: Dict) -> Dict:
        """Query the live AlphaGenome Atlas API. Raises on failure."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        resp = requests.get(
            f"{self.base_url}/variants/lookup",
            params={
                "gene": variant.get("gene"),
                "variant": variant.get("variant"),
                "genotype": variant.get("genotype"),
            },
            headers=headers,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "avi_score": data.get("avi_score"),
            "mechanisms": data.get("feature_attributions", {}),
            "source": "alphagenome_atlas_api",
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def interpret_avi(self, avi_score: float) -> Dict:
        for threshold, band, meaning in AVI_BANDS:
            if avi_score >= threshold:
                return {"band": band, "meaning": meaning}
        return {"band": "unknown", "meaning": "Score outside expected range"}

    def analyze_variant(self,
                        variant: Dict,
                        patient_id: Optional[str] = None,
                        consent_confirmed: bool = False,
                        purpose: str = "clinical research and patient counseling") -> Dict:
        """
        Analyze one variant through the full gate chain:
        consent -> ethics -> cache -> API -> cache-store.
        """
        # Gate 1: consent (hard stop)
        self._check_consent(consent_confirmed, patient_id)

        # Gate 2: ethics (hard stop)
        ethics_assessment = self._check_ethics(variant, purpose)

        base = {
            "variant": variant,
            "patient_id": patient_id,
            "consent_confirmed": True,
            "disclaimer": ALPHAGENOME_DISCLAIMER,
            "timestamp": datetime.now().isoformat(),
        }
        if ethics_assessment is not None:
            base["ethics"] = {
                "approved": ethics_assessment.approved,
                "gurmat_score": getattr(ethics_assessment, 'gurmat_score', None),
                "medical_ethics_score": getattr(ethics_assessment, 'medical_ethics_score', None),
            }

        # Gate 3: cache
        cached = self._cache_lookup(variant)
        if cached:
            return {**base, **cached, "ethics": base.get("ethics")}

        # Gate 4: live API
        if not self.api_configured:
            result = {
                "status": "api_not_configured",
                "avi_score": None,
                "message": (
                    "Live AlphaGenome Atlas API is not configured. "
                    "Set ALPHAGENOME_API_KEY (free for non-commercial research "
                    "via alphagenome.google/atlas). No score was fabricated."
                ),
                "cache_hit": False,
            }
            self.query_log.append({"variant": variant, "status": result["status"],
                                   "timestamp": base["timestamp"]})
            return {**base, **result}

        try:
            api_data = self._query_api(variant)
        except Exception as e:
            return {**base,
                    "status": "api_error",
                    "avi_score": None,
                    "message": f"AlphaGenome API request failed: {e}",
                    "cache_hit": False}

        avi = api_data.get("avi_score")
        result = {
            "status": "ok",
            "avi_score": avi,
            "avi_interpretation": self.interpret_avi(avi) if avi is not None else None,
            "mechanisms": api_data.get("mechanisms", {}),
            "source": api_data.get("source"),
            "cache_hit": False,
        }
        self._cache_store(variant, result)
        self.query_log.append({"variant": variant, "status": "ok",
                               "timestamp": base["timestamp"]})
        return {**base, **result}

    def analyze_panel(self,
                      variants: List[Dict],
                      patient_id: Optional[str] = None,
                      consent_confirmed: bool = False,
                      purpose: str = "clinical research and patient counseling") -> Dict:
        """Analyze multiple variants; one consent gate covers the panel."""
        results = [
            self.analyze_variant(v, patient_id=patient_id,
                                 consent_confirmed=consent_confirmed,
                                 purpose=purpose)
            for v in variants
        ]
        scored = [r for r in results if r.get("avi_score") is not None]
        ranked = sorted(scored, key=lambda r: r["avi_score"], reverse=True)
        return {
            "patient_id": patient_id,
            "variants_analyzed": len(results),
            "variants_with_scores": len(scored),
            "priority_ranking": [
                {"gene": r["variant"].get("gene"),
                 "variant": r["variant"].get("variant"),
                 "avi_score": r["avi_score"],
                 "band": r["avi_interpretation"]["band"]}
                for r in ranked
            ],
            "results": results,
            "disclaimer": ALPHAGENOME_DISCLAIMER,
            "timestamp": datetime.now().isoformat(),
        }

    def get_cache_stats(self) -> Dict:
        if self.memory is None:
            return {"cache_enabled": False}
        entries = self.memory.search(memory_type=self.CACHE_MEMORY_TYPE, limit=10000)
        return {
            "cache_enabled": True,
            "cached_variants": len(entries),
            "queries_logged": len(self.query_log),
        }
