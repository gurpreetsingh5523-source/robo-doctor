
"""
AMRIT BloodAnalyzer - 30+ Blood Tests with 4-Level Detection
Comprehensive blood analysis for health screening
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class RiskLevel(Enum):
    NORMAL = "normal"
    BORDERLINE = "borderline"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class BloodTestResult:
    test_name: str
    value: float
    unit: str
    reference_range: Tuple[float, float]
    risk_level: RiskLevel
    interpretation: str
    recommendations: List[str]
    population_adjusted: bool = False

class BloodAnalyzer:
    """
    Comprehensive blood test analyzer
    Covers 30+ tests with population-specific reference ranges
    """

    # Reference ranges (can be adjusted by population)
    REFERENCE_RANGES = {
        'glucose_fasting': (70, 100, 'mg/dL'),
        'glucose_postprandial': (70, 140, 'mg/dL'),
        'hba1c': (4.0, 5.7, '%'),
        'total_cholesterol': (0, 200, 'mg/dL'),
        'ldl_cholesterol': (0, 100, 'mg/dL'),
        'hdl_cholesterol': (40, 100, 'mg/dL'),
        'triglycerides': (0, 150, 'mg/dL'),
        'hemoglobin': (12.0, 16.0, 'g/dL'),
        'hematocrit': (36.0, 46.0, '%'),
        'wbc_count': (4.5, 11.0, 'x10^9/L'),
        'rbc_count': (4.0, 5.5, 'x10^12/L'),
        'platelet_count': (150, 450, 'x10^9/L'),
        'creatinine': (0.6, 1.3, 'mg/dL'),
        'bun': (7, 20, 'mg/dL'),
        'sodium': (135, 145, 'mEq/L'),
        'potassium': (3.5, 5.0, 'mEq/L'),
        'chloride': (98, 106, 'mEq/L'),
        'calcium': (8.5, 10.5, 'mg/dL'),
        'magnesium': (1.7, 2.2, 'mg/dL'),
        'phosphorus': (2.5, 4.5, 'mg/dL'),
        'uric_acid': (3.5, 7.2, 'mg/dL'),
        'bilirubin_total': (0.1, 1.2, 'mg/dL'),
        'alt': (7, 56, 'U/L'),
        'ast': (10, 40, 'U/L'),
        'alkaline_phosphatase': (44, 147, 'U/L'),
        'total_protein': (6.0, 8.3, 'g/dL'),
        'albumin': (3.5, 5.0, 'g/dL'),
        'globulin': (2.0, 3.5, 'g/dL'),
        'vitamin_d': (30, 100, 'ng/mL'),
        'vitamin_b12': (200, 900, 'pg/mL'),
        'ferritin': (15, 150, 'ng/mL'),
        'iron': (60, 170, 'mcg/dL'),
        'tsh': (0.4, 4.0, 'mIU/L'),
        't3': (80, 200, 'ng/dL'),
        't4': (5.0, 12.0, 'mcg/dL'),
        'crp': (0, 3.0, 'mg/L'),
        'esr': (0, 20, 'mm/hr'),
        'homocysteine': (5, 15, 'mc mol/L'),
    }

    # Population-specific adjustments
    POPULATION_ADJUSTMENTS = {
        'south_asian': {
            'hba1c': (4.0, 5.6, '%'),  # Lower threshold for diabetes
            'vitamin_d': (20, 100, 'ng/mL'),  # Lower normal due to melanin
            'ldl_cholesterol': (0, 90, 'mg/dL'),  # Stricter for heart disease risk
        },
        'african': {
            'creatinine': (0.7, 1.4, 'mg/dL'),  # Higher muscle mass
            'wbc_count': (3.5, 10.0, 'x10^9/L'),  # Lower normal
        },
        'east_asian': {
            'alt': (5, 40, 'U/L'),  # Lower normal
            'hba1c': (4.0, 5.6, '%'),
        },
        'caucasian': {
            'vitamin_d': (30, 100, 'ng/mL'),
        },
        'hispanic': {
            'hba1c': (4.0, 5.6, '%'),
        },
        'middle_eastern': {
            'hba1c': (4.0, 5.6, '%'),
        }
    }

    def __init__(self, population: str = 'general'):
        self.population = population.lower()
        self.adjustments = self.POPULATION_ADJUSTMENTS.get(self.population, {})

    def analyze_test(self, test_name: str, value: float) -> BloodTestResult:
        """Analyze a single blood test"""
        test_name = test_name.lower().replace(' ', '_')

        # Get reference range
        if test_name in self.adjustments:
            ref_low, ref_high, unit = self.adjustments[test_name]
            population_adjusted = True
        elif test_name in self.REFERENCE_RANGES:
            ref_low, ref_high, unit = self.REFERENCE_RANGES[test_name]
            population_adjusted = False
        else:
            return BloodTestResult(
                test_name=test_name,
                value=value,
                unit='unknown',
                reference_range=(0, 0),
                risk_level=RiskLevel.NORMAL,
                interpretation="Unknown test - cannot analyze",
                recommendations=["Consult laboratory for reference range"],
                population_adjusted=False
            )

        # Determine risk level
        risk_level, interpretation, recommendations = self._assess_risk(
            test_name, value, ref_low, ref_high
        )

        return BloodTestResult(
            test_name=test_name,
            value=value,
            unit=unit,
            reference_range=(ref_low, ref_high),
            risk_level=risk_level,
            interpretation=interpretation,
            recommendations=recommendations,
            population_adjusted=population_adjusted
        )

    def _assess_risk(self, test_name: str, value: float, 
                    ref_low: float, ref_high: float) -> Tuple[RiskLevel, str, List[str]]:
        """Assess risk level for a test value"""

        # Calculate how far from normal
        range_size = ref_high - ref_low

        if range_size == 0:
            return RiskLevel.NORMAL, "Reference range not available", ["Consult physician"]

        # Determine if value is low or high
        if value < ref_low:
            deviation = (ref_low - value) / range_size

            if deviation < 0.5:
                risk = RiskLevel.BORDERLINE
                interpretation = f"Slightly low {test_name}"
                recommendations = ["Monitor closely", "Dietary modification", "Recheck in 3 months"]
            elif deviation < 1.0:
                risk = RiskLevel.HIGH
                interpretation = f"Low {test_name} - requires attention"
                recommendations = ["Consult physician", "Supplement if indicated", "Investigate cause"]
            else:
                risk = RiskLevel.CRITICAL
                interpretation = f"Critically low {test_name}"
                recommendations = ["URGENT: Consult physician immediately", "Possible deficiency or disease", "Further testing required"]

        elif value > ref_high:
            deviation = (value - ref_high) / range_size

            if deviation < 0.5:
                risk = RiskLevel.BORDERLINE
                interpretation = f"Slightly elevated {test_name}"
                recommendations = ["Lifestyle modification", "Recheck in 3 months", "Dietary changes"]
            elif deviation < 1.0:
                risk = RiskLevel.HIGH
                interpretation = f"Elevated {test_name} - requires attention"
                recommendations = ["Consult physician", "Medication review", "Lifestyle intervention"]
            else:
                risk = RiskLevel.CRITICAL
                interpretation = f"Critically elevated {test_name}"
                recommendations = ["URGENT: Consult physician immediately", "Possible organ dysfunction", "Emergency evaluation"]

        else:
            risk = RiskLevel.NORMAL
            interpretation = f"{test_name} within normal range"
            recommendations = ["Continue current management", "Routine monitoring"]

        return risk, interpretation, recommendations

    def analyze_panel(self, test_results: Dict[str, float]) -> Dict[str, BloodTestResult]:
        """Analyze a full blood panel"""
        results = {}
        for test_name, value in test_results.items():
            results[test_name] = self.analyze_test(test_name, value)
        return results

    def get_health_summary(self, test_results: Dict[str, float]) -> Dict:
        """Get overall health summary from blood panel"""
        analyzed = self.analyze_panel(test_results)

        risk_counts = {level: 0 for level in RiskLevel}
        critical_tests = []
        high_tests = []
        borderline_tests = []

        for test_name, result in analyzed.items():
            risk_counts[result.risk_level] += 1

            if result.risk_level == RiskLevel.CRITICAL:
                critical_tests.append(test_name)
            elif result.risk_level == RiskLevel.HIGH:
                high_tests.append(test_name)
            elif result.risk_level == RiskLevel.BORDERLINE:
                borderline_tests.append(test_name)

        overall_risk = RiskLevel.NORMAL
        if risk_counts[RiskLevel.CRITICAL] > 0:
            overall_risk = RiskLevel.CRITICAL
        elif risk_counts[RiskLevel.HIGH] > 2:
            overall_risk = RiskLevel.HIGH
        elif risk_counts[RiskLevel.HIGH] > 0 or risk_counts[RiskLevel.BORDERLINE] > 3:
            overall_risk = RiskLevel.BORDERLINE

        return {
            'overall_risk': overall_risk.value,
            'risk_distribution': {k.value: v for k, v in risk_counts.items()},
            'critical_tests': critical_tests,
            'high_tests': high_tests,
            'borderline_tests': borderline_tests,
            'total_tests': len(analyzed),
            'recommendations': self._generate_panel_recommendations(analyzed)
        }

    def _generate_panel_recommendations(self, analyzed: Dict) -> List[str]:
        """Generate recommendations based on full panel"""
        recommendations = []

        # Check for common patterns
        has_diabetes_risk = False
        has_cardiac_risk = False
        has_anemia = False
        has_inflammation = False

        for test_name, result in analyzed.items():
            if test_name in ['glucose_fasting', 'hba1c'] and result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                has_diabetes_risk = True
            if test_name in ['ldl_cholesterol', 'total_cholesterol'] and result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                has_cardiac_risk = True
            if test_name in ['hemoglobin', 'ferritin', 'iron'] and result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                has_anemia = True
            if test_name in ['crp', 'esr'] and result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                has_inflammation = True

        if has_diabetes_risk:
            recommendations.append("Diabetes screening recommended - consider HbA1c and OGTT")
        if has_cardiac_risk:
            recommendations.append("Cardiovascular risk assessment - consider lipid panel and ECG")
        if has_anemia:
            recommendations.append("Anemia workup - check B12, folate, and iron studies")
        if has_inflammation:
            recommendations.append("Inflammatory workup - investigate infection or autoimmune condition")

        if not recommendations:
            recommendations.append("Continue healthy lifestyle and routine monitoring")

        return recommendations
