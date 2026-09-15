
"""
AMRIT EthicsFilter - Gurmat + Medical Ethics Framework
Ensures all research and recommendations follow ethical principles
"""
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class EthicsPrinciple(Enum):
    SARBAT_DA_BHALA = "sarbat_da_bhala"  # Welfare of all
    SEVA = "seva"  # Selfless service
    DAYA = "daya"  # Compassion
    SAT = "sat"  # Truth
    KIRAT_KARO = "kirat_karo"  # Honest labor
    AUTONOMY = "autonomy"  # Respect for persons
    BENEFICENCE = "beneficence"  # Do good
    NON_MALEFICENCE = "non_maleficence"  # Do no harm
    JUSTICE = "justice"  # Fairness
    DIGNITY = "dignity"  # Human worth

class EthicsViolationType(Enum):
    EUGENICS = "eugenics"
    DISCRIMINATION = "discrimination"
    GENDER_SELECTION = "gender_selection"
    EXPLOITATION = "exploitation"
    CONSENT_VIOLATION = "consent_violation"
    PRIVACY_VIOLATION = "privacy_violation"
    CONFLICT_OF_INTEREST = "conflict_of_interest"
    ANIMAL_WELFARE = "animal_welfare"
    ENVIRONMENTAL_HARM = "environmental_harm"
    DATA_FABRICATION = "data_fabrication"

@dataclass
class EthicsAssessment:
    action: str
    approved: bool
    violations: List[EthicsViolationType]
    concerns: List[str]
    recommendations: List[str]
    gurmat_score: float  # 0-1
    medical_ethics_score: float  # 0-1
    overall_score: float  # 0-1

class EthicsFilter:
    """
    Comprehensive ethics filter for AMRIT Research OS
    Combines Gurmat Sikh ethics with standard medical ethics
    """

    # Prohibited actions
    PROHIBITED_ACTIONS = [
        'eugenics',
        'racial discrimination',
        'ethnic discrimination',
        'gender selection for non-medical reasons',
        'exploitation of vulnerable populations',
        'research without informed consent',
        'data fabrication',
        'plagiarism',
        'conflict of interest non-disclosure',
        'unnecessary animal testing',
        'environmental destruction',
        'profiteering from essential medicines',
        'withholding treatment for financial reasons',
        'discrimination based on caste',
        'discrimination based on religion',
        'discrimination based on socioeconomic status',
        'forced sterilization',
        'human cloning for reproduction',
        'sale of organs',
        'coercive recruitment for research'
    ]

    # Gurmat principles mapping
    GURMAT_PRINCIPLES = {
        EthicsPrinciple.SARBAT_DA_BHALA: [
            'welfare of all humanity',
            'universal benefit',
            'no discrimination',
            'service to poor',
            'service to underserved'
        ],
        EthicsPrinciple.SEVA: [
            'selfless service',
            'voluntary work',
            'community service',
            'helping others without expectation'
        ],
        EthicsPrinciple.DAYA: [
            'compassion',
            'kindness',
            'empathy',
            'care for suffering',
            'patient-centered care'
        ],
        EthicsPrinciple.SAT: [
            'truth',
            'honesty',
            'transparency',
            'data integrity',
            'accurate reporting'
        ],
        EthicsPrinciple.KIRAT_KARO: [
            'honest labor',
            'fair compensation',
            'no exploitation',
            'ethical business practices'
        ]
    }

    # Medical ethics principles
    MEDICAL_ETHICS_PRINCIPLES = {
        EthicsPrinciple.AUTONOMY: [
            'informed consent',
            'patient choice',
            'right to refuse',
            'privacy',
            'confidentiality'
        ],
        EthicsPrinciple.BENEFICENCE: [
            'do good',
            'maximize benefit',
            'best interest',
            'positive outcomes'
        ],
        EthicsPrinciple.NON_MALEFICENCE: [
            'do no harm',
            'minimize risk',
            'avoid suffering',
            'primum non nocere'
        ],
        EthicsPrinciple.JUSTICE: [
            'fairness',
            'equitable distribution',
            'no discrimination',
            'access to care'
        ],
        EthicsPrinciple.DIGNITY: [
            'human worth',
            'respect',
            'cultural sensitivity',
            'patient dignity'
        ]
    }

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.violation_history = []

    def assess(self, action_description: str, 
               context: Dict = None) -> EthicsAssessment:
        """
        Assess an action for ethical compliance
        """
        context = context or {}
        violations = []
        concerns = []
        recommendations = []

        action_lower = action_description.lower()

        # Check prohibited actions
        for prohibited in self.PROHIBITED_ACTIONS:
            if prohibited in action_lower:
                violations.append(self._classify_violation(prohibited))
                concerns.append(f"Prohibited action detected: {prohibited}")

        # Check Gurmat principles
        gurmat_score = self._assess_gurmat_principles(action_description, context)

        # Check medical ethics
        medical_score = self._assess_medical_ethics(action_description, context)

        # Overall score
        overall_score = (gurmat_score * 0.5 + medical_score * 0.5)

        # Determine approval
        approved = (overall_score >= 0.7 and len(violations) == 0)

        if not approved:
            recommendations.extend(self._generate_recommendations(violations, concerns))

        assessment = EthicsAssessment(
            action=action_description,
            approved=approved,
            violations=violations,
            concerns=concerns,
            recommendations=recommendations,
            gurmat_score=gurmat_score,
            medical_ethics_score=medical_score,
            overall_score=overall_score
        )

        if not approved:
            self.violation_history.append(assessment)

        return assessment

    def _classify_violation(self, prohibited_action: str) -> EthicsViolationType:
        """Classify violation type"""
        if 'eugenics' in prohibited_action:
            return EthicsViolationType.EUGENICS
        elif 'discrimination' in prohibited_action or 'caste' in prohibited_action:
            return EthicsViolationType.DISCIMINATION
        elif 'gender selection' in prohibited_action:
            return EthicsViolationType.GENDER_SELECTION
        elif 'exploitation' in prohibited_action:
            return EthicsViolationType.EXPLOITATION
        elif 'consent' in prohibited_action:
            return EthicsViolationType.CONSENT_VIOLATION
        elif 'privacy' in prohibited_action:
            return EthicsViolationType.PRIVACY_VIOLATION
        elif 'conflict' in prohibited_action:
            return EthicsViolationType.CONFLICT_OF_INTEREST
        elif 'animal' in prohibited_action:
            return EthicsViolationType.ANIMAL_WELFARE
        elif 'environment' in prohibited_action:
            return EthicsViolationType.ENVIRONMENTAL_HARM
        elif 'fabrication' in prohibited_action or 'plagiarism' in prohibited_action:
            return EthicsViolationType.DATA_FABRICATION
        else:
            return EthicsViolationType.EXPLOITATION

    def _assess_gurmat_principles(self, action: str, context: Dict) -> float:
        """Assess compliance with Gurmat principles"""
        score = 1.0
        action_lower = action.lower()

        # Check Sarbat Da Bhala
        if any(word in action_lower for word in ['discriminate', 'exclude', 'harm poor']):
            score -= 0.3

        # Check Seva
        if any(word in action_lower for word in ['profit', 'exploit', 'charge excessive']):
            score -= 0.2

        # Check Daya
        if any(word in action_lower for word in ['suffer', 'pain', 'distress']):
            if 'minimize' not in action_lower and 'relieve' not in action_lower:
                score -= 0.2

        # Check Sat
        if any(word in action_lower for word in ['fake', 'fabricate', 'lie', 'hide']):
            score -= 0.4

        # Check Kirat Karo
        if any(word in action_lower for word in ['steal', 'cheat', 'unfair']):
            score -= 0.3

        return max(0, score)

    def _assess_medical_ethics(self, action: str, context: Dict) -> float:
        """Assess compliance with medical ethics"""
        score = 1.0
        action_lower = action.lower()

        # Check Autonomy
        if 'without consent' in action_lower or 'forced' in action_lower:
            score -= 0.4

        # Check Beneficence
        if 'no benefit' in action_lower or 'harm exceeds benefit' in action_lower:
            score -= 0.3

        # Check Non-maleficence
        if 'harm' in action_lower and 'minimize' not in action_lower:
            score -= 0.2

        # Check Justice
        if 'unfair' in action_lower or 'inequitable' in action_lower:
            score -= 0.3

        # Check Dignity
        if 'dehumanize' in action_lower or 'humiliate' in action_lower:
            score -= 0.4

        return max(0, score)

    def _generate_recommendations(self, violations: List[EthicsViolationType], 
                                 concerns: List[str]) -> List[str]:
        """Generate recommendations for violations"""
        recommendations = []

        for violation in violations:
            if violation == EthicsViolationType.EUGENICS:
                recommendations.append("Remove all eugenics-related content immediately")
                recommendations.append("Consult bioethics committee")
            elif violation == EthicsViolationType.DISCIMINATION:
                recommendations.append("Ensure equal treatment regardless of background")
                recommendations.append("Review inclusion criteria for bias")
            elif violation == EthicsViolationType.GENDER_SELECTION:
                recommendations.append("Limit gender selection to medical necessity only")
            elif violation == EthicsViolationType.EXPLOITATION:
                recommendations.append("Ensure fair compensation and informed consent")
                recommendations.append("Protect vulnerable populations")
            elif violation == EthicsViolationType.CONSENT_VIOLATION:
                recommendations.append("Obtain proper informed consent")
                recommendations.append("Ensure understanding of risks and benefits")
            elif violation == EthicsViolationType.DATA_FABRICATION:
                recommendations.append("Maintain data integrity at all costs")
                recommendations.append("Implement audit trails")

        return recommendations

    def assess_research_proposal(self, proposal: Dict) -> EthicsAssessment:
        """Assess a research proposal for ethical compliance"""
        description = proposal.get('title', '') + ' ' + proposal.get('description', '')

        # Additional checks for research
        context = {
            'has_informed_consent': proposal.get('informed_consent', False),
            'has_irb_approval': proposal.get('irb_approval', False),
            'vulnerable_populations': proposal.get('vulnerable_populations', []),
            'data_sharing': proposal.get('data_sharing', False),
            'benefit_sharing': proposal.get('benefit_sharing', False)
        }

        assessment = self.assess(description, context)

        # Additional research-specific concerns
        if not context['has_informed_consent']:
            assessment.concerns.append("Informed consent not documented")
            assessment.approved = False

        if not context['has_irb_approval']:
            assessment.concerns.append("IRB/ethics committee approval not documented")
            assessment.approved = False

        if context['vulnerable_populations'] and not context['benefit_sharing']:
            assessment.concerns.append("Benefit sharing plan required for vulnerable populations")

        return assessment

    def get_ethics_summary(self) -> Dict:
        """Get summary of ethics assessments"""
        total_assessed = len(self.violation_history)

        violation_counts = {}
        for assessment in self.violation_history:
            for v in assessment.violations:
                violation_counts[v.value] = violation_counts.get(v.value, 0) + 1

        return {
            'total_violations_detected': total_assessed,
            'violation_breakdown': violation_counts,
            'strict_mode': self.strict_mode,
            'principles_monitored': len(self.GURMAT_PRINCIPLES) + len(self.MEDICAL_ETHICS_PRINCIPLES)
        }
