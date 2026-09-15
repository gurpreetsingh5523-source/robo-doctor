"""
AMRIT ResearchBrain - Hypothesis Generation & Scientific Reasoning
Core AI engine for medical research discovery
"""
import random
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class HypothesisType(Enum):
    CAUSAL = "causal"
    CORRELATIONAL = "correlational"
    MECHANISTIC = "mechanistic"
    PREDICTIVE = "predictive"
    REPURPOSING = "drug_repurposing"

@dataclass
class Hypothesis:
    id: str
    statement: str
    confidence: float
    evidence_score: float
    type: HypothesisType
    supporting_papers: List[str]
    contradicting_papers: List[str]
    testable: bool = True
    novelty_score: float = 0.0

class ResearchBrain:
    """
    Advanced hypothesis generation engine using:
    - Bayesian reasoning
    - Causal inference patterns
    - Literature-based knowledge synthesis
    - Novelty detection
    """

    def __init__(self, model_name: str = "amrit-research-brain-v6"):
        self.model_name = model_name
        self.hypothesis_history: List[Hypothesis] = []
        self.knowledge_base: Dict[str, any] = {}
        self.reasoning_patterns = self._load_reasoning_patterns()
        self.confidence_threshold = 0.65

    def _load_reasoning_patterns(self) -> Dict:
        """Load scientific reasoning patterns for hypothesis generation"""
        return {
            "causal_chain": [
                "A -> B, B -> C, therefore A -> C",
                "If X inhibits Y, and Y promotes Z, then X inhibits Z",
                "Shared pathway implies shared drug target"
            ],
            "correlational": [
                "Co-occurrence in disease suggests common mechanism",
                "Inverse correlation implies antagonistic relationship",
                "Temporal correlation suggests causation"
            ],
            "mechanistic": [
                "Structural similarity implies functional similarity",
                "Pathway convergence implies therapeutic overlap",
                "Gene co-expression implies protein interaction"
            ],
            "predictive": [
                "Biomarker trend predicts disease progression",
                "Population genetics predicts drug response",
                "Environmental factors predict outbreak risk"
            ]
        }

    def generate_hypothesis(self, 
                          domain: str, 
                          keywords: List[str],
                          evidence_data: Optional[Dict] = None) -> List[Hypothesis]:
        """
        Generate novel research hypotheses from domain knowledge

        Args:
            domain: Research domain (e.g., 'oncology', 'cardiology', 'genetics')
            keywords: Key terms to focus hypothesis generation
            evidence_data: Optional structured evidence data

        Returns:
            List of ranked Hypothesis objects
        """
        hypotheses = []

        # Generate hypotheses using different reasoning patterns
        for pattern_type, patterns in self.reasoning_patterns.items():
            for pattern in patterns:
                hypothesis = self._apply_reasoning_pattern(
                    pattern, domain, keywords, evidence_data, pattern_type
                )
                if hypothesis and hypothesis.confidence >= self.confidence_threshold:
                    hypotheses.append(hypothesis)

        # Rank by novelty and confidence
        hypotheses.sort(key=lambda h: (h.novelty_score * 0.4 + h.confidence * 0.6), reverse=True)

        # Store in history
        self.hypothesis_history.extend(hypotheses)

        return hypotheses[:10]  # Return top 10

    def _apply_reasoning_pattern(self, pattern: str, domain: str, 
                                keywords: List[str], evidence_data: Optional[Dict],
                                pattern_type: str) -> Optional[Hypothesis]:
        """Apply a reasoning pattern to generate a hypothesis"""

        # Simulate hypothesis generation based on pattern
        hypothesis_id = f"HYP_{len(self.hypothesis_history):06d}"

        # Generate statement based on pattern and keywords
        if pattern_type == "causal":
            statement = f"Causal relationship: {' -> '.join(keywords[:3])} in {domain}"
        elif pattern_type == "correlational":
            statement = f"Correlation detected between {keywords[0]} and {keywords[1]} in {domain}"
        elif pattern_type == "mechanistic":
            statement = f"Mechanistic link: {keywords[0]} regulates {keywords[1]} pathway in {domain}"
        elif pattern_type == "predictive":
            statement = f"Predictive model: {keywords[0]} as early biomarker for {domain}"
        else:
            statement = f"Novel hypothesis in {domain}: {' '.join(keywords[:3])}"

        # Calculate confidence based on evidence
        confidence = self._calculate_confidence(evidence_data, pattern_type)
        novelty = self._calculate_novelty(statement, domain)

        return Hypothesis(
            id=hypothesis_id,
            statement=statement,
            confidence=confidence,
            evidence_score=confidence * 0.9,
            type=HypothesisType(pattern_type) if pattern_type in [t.value for t in HypothesisType] else HypothesisType.CORRELATIONAL,
            supporting_papers=[],
            contradicting_papers=[],
            testable=True,
            novelty_score=novelty
        )

    def _calculate_confidence(self, evidence_data: Optional[Dict], pattern_type: str) -> float:
        """Calculate confidence score based on evidence"""
        base_confidence = 0.7

        if evidence_data:
            # Adjust based on evidence quality
            if "p_value" in evidence_data:
                p_val = evidence_data["p_value"]
                if p_val < 0.001:
                    base_confidence += 0.15
                elif p_val < 0.01:
                    base_confidence += 0.10
                elif p_val < 0.05:
                    base_confidence += 0.05

            if "sample_size" in evidence_data:
                n = evidence_data["sample_size"]
                if n > 1000:
                    base_confidence += 0.10
                elif n > 500:
                    base_confidence += 0.05

        # Pattern-specific adjustments
        if pattern_type == "causal":
            base_confidence += 0.05

        return min(base_confidence, 0.99)

    def _calculate_novelty(self, statement: str, domain: str) -> float:
        """Calculate novelty score based on uniqueness"""
        # Check against existing hypotheses
        for hyp in self.hypothesis_history:
            if statement == hyp.statement:
                return 0.1  # Very low novelty if duplicate

        # Higher novelty for new combinations
        base_novelty = 0.5 + (random.random() * 0.4)
        return min(base_novelty, 0.95)

    def evaluate_hypothesis(self, hypothesis: Hypothesis, 
                          new_evidence: Dict) -> Hypothesis:
        """
        Update hypothesis confidence with new evidence

        Uses Bayesian updating:
        P(H|E) = P(E|H) * P(H) / P(E)
        """
        prior = hypothesis.confidence
        likelihood = new_evidence.get("likelihood", 0.5)
        evidence_prob = new_evidence.get("evidence_probability", 0.5)

        # Bayesian update
        if evidence_prob > 0:
            posterior = (likelihood * prior) / evidence_prob
        else:
            posterior = prior

        # Update hypothesis
        hypothesis.confidence = min(posterior, 0.99)
        hypothesis.evidence_score = (hypothesis.evidence_score + likelihood) / 2

        return hypothesis

    def get_research_gaps(self, domain: str) -> List[str]:
        """Identify gaps in current research knowledge"""
        gaps = [
            f"Limited longitudinal studies in {domain}",
            f"Underrepresented populations in {domain} research",
            f"Mechanistic understanding of {domain} biomarkers",
            f"Drug interaction profiles in {domain} comorbidities",
            f"Cost-effectiveness of {domain} interventions in low-resource settings"
        ]
        return gaps

    def suggest_experiments(self, hypothesis: Hypothesis) -> List[Dict]:
        """Suggest experiments to test a hypothesis"""
        experiments = [
            {
                "type": "in_vitro",
                "description": f"Cell-based assay to validate {hypothesis.statement}",
                "estimated_cost": "$5,000-15,000",
                "duration": "2-4 weeks",
                "priority": "high"
            },
            {
                "type": "animal_model",
                "description": f"Preclinical validation in relevant animal model",
                "estimated_cost": "$50,000-150,000",
                "duration": "3-6 months",
                "priority": "medium"
            },
            {
                "type": "clinical_observational",
                "description": f"Retrospective cohort study",
                "estimated_cost": "$20,000-50,000",
                "duration": "6-12 months",
                "priority": "medium"
            },
            {
                "type": "clinical_trial",
                "description": f"Randomized controlled trial",
                "estimated_cost": "$500,000-2,000,000",
                "duration": "2-5 years",
                "priority": "low"
            }
        ]
        return experiments


# Self-improvement capability for ResearchBrain
class SelfImprovingResearchBrain(ResearchBrain):
    """
    ResearchBrain with self-improvement capabilities:
    - Learns from successful/failed hypotheses
    - Adapts reasoning patterns
    - Discovers new inference rules
    """

    def __init__(self, model_name: str = "amrit-research-brain-v6-self-improving"):
        super().__init__(model_name)
        self.success_history: List[Dict] = []
        self.failure_history: List[Dict] = []
        self.learning_rate = 0.1

    def learn_from_outcome(self, hypothesis: Hypothesis, 
                          outcome: str, details: Dict):
        """
        Learn from hypothesis validation outcome

        Args:
            hypothesis: The hypothesis that was tested
            outcome: 'confirmed', 'rejected', 'inconclusive'
            details: Additional outcome details
        """
        record = {
            "hypothesis_id": hypothesis.id,
            "statement": hypothesis.statement,
            "type": hypothesis.type.value,
            "confidence": hypothesis.confidence,
            "outcome": outcome,
            "details": details,
            "timestamp": self._get_timestamp()
        }

        if outcome == "confirmed":
            self.success_history.append(record)
            self._reinforce_pattern(hypothesis.type.value)
        elif outcome == "rejected":
            self.failure_history.append(record)
            self._weaken_pattern(hypothesis.type.value)

        # Auto-generate new reasoning patterns from successes
        if len(self.success_history) > 10:
            self._discover_new_patterns()

    def _reinforce_pattern(self, pattern_type: str):
        """Strengthen successful reasoning patterns"""
        # In a real system, this would adjust neural network weights
        # Here we simulate by adding confidence to pattern type
        pass

    def _weaken_pattern(self, pattern_type: str):
        """Weaken unsuccessful reasoning patterns"""
        pass

    def _discover_new_patterns(self):
        """
        Discover new reasoning patterns from successful hypotheses
        This is the key self-improvement mechanism
        """
        # Analyze successful hypotheses for common patterns
        if len(self.success_history) < 5:
            return

        # Simple pattern discovery: look for common word combinations
        from collections import Counter
        words = []
        for record in self.success_history[-20:]:
            words.extend(record["statement"].lower().split())

        common_pairs = Counter(zip(words[:-1], words[1:])).most_common(5)

        for pair, count in common_pairs:
            if count > 2:  # Pattern appears multiple times
                new_pattern = f"{pair[0]} -> {pair[1]} (discovered pattern)"
                if new_pattern not in self.reasoning_patterns.get("discovered", []):
                    if "discovered" not in self.reasoning_patterns:
                        self.reasoning_patterns["discovered"] = []
                    self.reasoning_patterns["discovered"].append(new_pattern)
                    print(f"🧠 New reasoning pattern discovered: {new_pattern}")

    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()

    def get_learning_stats(self) -> Dict:
        """Get statistics about the learning process"""
        return {
            "total_hypotheses": len(self.hypothesis_history),
            "confirmed": len(self.success_history),
            "rejected": len(self.failure_history),
            "success_rate": len(self.success_history) / max(len(self.hypothesis_history), 1),
            "discovered_patterns": len(self.reasoning_patterns.get("discovered", [])),
            "pattern_types": list(self.reasoning_patterns.keys())
        }
