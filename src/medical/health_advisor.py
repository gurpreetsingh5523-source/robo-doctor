
"""
AMRIT Personalized Health Advisor v6.0
DNA Analysis + Blood Analysis + Environment + Recommendations
"""
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class RiskCategory(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class HealthRecommendation:
    category: str
    recommendation: str
    priority: str
    evidence_level: str
    action_items: List[str]

class PersonalizedHealthAdvisor:
    """
    Comprehensive personalized health advisor
    Integrates DNA, blood, and environmental data
    """

    # DNA variant database
    DNA_VARIANTS = {
        'APOE4': {
            'gene': 'APOE',
            'variant': 'rs429358',
            'risk_disease': "Alzheimer's Disease",
            'risk_multiplier': {'0_copies': 1.0, '1_copy': 3.0, '2_copies': 15.0},
            'recommendations': {
                'diet': ['Mediterranean diet', 'Omega-3 fatty acids', 'Limit saturated fat'],
                'lifestyle': ['Regular exercise', 'Cognitive training', 'Social engagement'],
                'supplements': ['DHA', 'Vitamin E', 'Curcumin'],
                'screening': ['Annual cognitive assessment', 'MRI at 50+']
            }
        },
        'MTHFR_C677T': {
            'gene': 'MTHFR',
            'variant': 'rs1801133',
            'risk_disease': 'Cardiovascular Disease, Neural Tube Defects',
            'risk_multiplier': {'CC': 1.0, 'CT': 1.5, 'TT': 2.0},
            'recommendations': {
                'diet': ['Folate-rich foods', 'Leafy greens', 'Legumes'],
                'lifestyle': ['Limit alcohol', 'Avoid smoking'],
                'supplements': ['Methylfolate (5-MTHF)', 'B12', 'B6'],
                'screening': ['Homocysteine levels', 'Cardiovascular risk assessment']
            }
        },
        'FTO': {
            'gene': 'FTO',
            'variant': 'rs9939609',
            'risk_disease': 'Obesity, Type 2 Diabetes',
            'risk_multiplier': {'TT': 1.7, 'AT': 1.3, 'AA': 1.0},
            'recommendations': {
                'diet': ['Portion control', 'High protein breakfast', 'Low glycemic index foods'],
                'lifestyle': ['60 min daily exercise', 'Sleep 7-8 hours', 'Stress management'],
                'supplements': ['Chromium', 'Green tea extract'],
                'screening': ['BMI monitoring', 'Glucose tolerance test', 'HbA1c']
            }
        },
        'LCT': {
            'gene': 'LCT',
            'variant': 'rs4988235',
            'risk_disease': 'Lactose Intolerance',
            'risk_multiplier': {'CC': 1.0, 'CT': 0.5, 'TT': 0.0},
            'recommendations': {
                'diet': ['Lactose-free dairy', 'Fermented dairy', 'Plant-based alternatives'],
                'lifestyle': ['Read food labels', 'Dining awareness'],
                'supplements': ['Calcium', 'Vitamin D', 'Probiotics'],
                'screening': ['Lactose tolerance test']
            }
        },
        'ALDH2': {
            'gene': 'ALDH2',
            'variant': 'rs671',
            'risk_disease': 'Alcohol Flush, Esophageal Cancer',
            'risk_multiplier': {'GG': 1.0, 'AG': 3.0, 'AA': 10.0},
            'recommendations': {
                'diet': ['Alcohol avoidance', 'Antioxidant-rich foods'],
                'lifestyle': ['Complete alcohol abstinence', 'Cancer screening'],
                'supplements': ['NAC', 'Vitamin C', 'Selenium'],
                'screening': ['Esophageal endoscopy', 'Regular cancer screening']
            }
        },
        'ACTN3': {
            'gene': 'ACTN3',
            'variant': 'rs1815739',
            'risk_disease': 'Muscle Performance',
            'risk_multiplier': {'RR': 1.0, 'RX': 0.8, 'XX': 0.6},
            'recommendations': {
                'diet': ['High protein', 'Creatine supplementation'],
                'lifestyle': ['Endurance training for XX', 'Power training for RR'],
                'supplements': ['Creatine', 'Beta-alanine', 'Protein powder'],
                'screening': ['Muscle performance testing']
            }
        },
        'CYP1A2': {
            'gene': 'CYP1A2',
            'variant': 'rs762551',
            'risk_disease': 'Caffeine Metabolism, Drug Response',
            'risk_multiplier': {'AA': 1.0, 'AC': 0.7, 'CC': 0.5},
            'recommendations': {
                'diet': ['Limit caffeine for slow metabolizers', 'Timing of medication'],
                'lifestyle': ['Morning exercise for slow metabolizers'],
                'supplements': ['Adjust caffeine intake based on genotype'],
                'screening': ['Caffeine metabolism test']
            }
        },
        'HFE': {
            'gene': 'HFE',
            'variant': 'rs1800562',
            'risk_disease': 'Hereditary Hemochromatosis',
            'risk_multiplier': {'CC': 1.0, 'CG': 10.0, 'GG': 100.0},
            'recommendations': {
                'diet': ['Avoid iron supplements', 'Limit red meat', 'Vitamin C with meals'],
                'lifestyle': ['Regular blood donation', 'Avoid alcohol'],
                'supplements': ['Avoid iron', 'Tea with meals to reduce absorption'],
                'screening': ['Ferritin levels', 'Transferrin saturation', 'Liver function']
            }
        },
        'BRCA1': {
            'gene': 'BRCA1',
            'variant': 'rs80357906',
            'risk_disease': 'Breast/Ovarian Cancer',
            'risk_multiplier': {'negative': 1.0, 'positive': 12.0},
            'recommendations': {
                'diet': ['Mediterranean diet', 'Cruciferous vegetables', 'Limit alcohol'],
                'lifestyle': ['Maintain healthy weight', 'Regular exercise', 'Breastfeeding if applicable'],
                'supplements': ['Vitamin D', 'Calcium', 'Omega-3'],
                'screening': ['Mammography starting at 25', 'MRI alternating', 'CA-125', 'Transvaginal ultrasound']
            }
        },
        'BRCA2': {
            'gene': 'BRCA2',
            'variant': 'rs80359706',
            'risk_disease': 'Breast/Prostate/Pancreatic Cancer',
            'risk_multiplier': {'negative': 1.0, 'positive': 10.0},
            'recommendations': {
                'diet': ['High fiber', 'Limit red meat', 'Antioxidant-rich foods'],
                'lifestyle': ['Regular exercise', 'Maintain healthy weight', 'No smoking'],
                'supplements': ['Vitamin D', 'Selenium', 'Lycopene'],
                'screening': ['Mammography', 'Prostate screening', 'Pancreatic screening if family history']
            }
        }
    }

    # Environmental factors
    ENVIRONMENTAL_FACTORS = {
        'PM2.5': {
            'safe_level': 12.0,  # µg/m³
            'unit': 'µg/m³',
            'health_effects': ['Respiratory disease', 'Cardiovascular disease', 'Lung cancer'],
            'mitigation': ['Air purifier', 'Mask outdoors', 'Indoor plants', 'Avoid outdoor exercise on high pollution days']
        },
        'arsenic': {
            'safe_level': 10.0,  # µg/L
            'unit': 'µg/L',
            'health_effects': ['Skin lesions', 'Cancer', 'Cardiovascular disease', 'Diabetes'],
            'mitigation': ['Water filtration', 'Reverse osmosis', 'Regular water testing', 'Dietary selenium']
        },
        'lead': {
            'safe_level': 5.0,  # µg/dL
            'unit': 'µg/dL',
            'health_effects': ['Neurodevelopmental delay', 'Hypertension', 'Kidney damage'],
            'mitigation': ['Lead abatement', 'Calcium/iron rich diet', 'Chelation if severe', 'Regular screening']
        },
        'ozone': {
            'safe_level': 70.0,  # ppb
            'unit': 'ppb',
            'health_effects': ['Asthma exacerbation', 'Lung function decline'],
            'mitigation': ['Limit outdoor activity', 'Air conditioning', 'Check AQI daily']
        }
    }

    def __init__(self, alphagenome_client=None):
        self.patient_data = {}
        self.recommendations_history = []
        # Optional AlphaGenome Atlas integration (v6.2).
        # When provided, DNA analysis can be enriched with AVI impact scores.
        self.alphagenome = alphagenome_client

    def analyze_variants_with_alphagenome(self, variants: List[Dict],
                                          patient_id: str = None,
                                          consent_confirmed: bool = False) -> Dict:
        """
        Enrich variant analysis with AlphaGenome Atlas AVI scores.
        Requires the alphagenome_client to be attached and explicit consent.
        Combines AMRIT's curated DNA_VARIANTS knowledge with Atlas predictions.
        """
        if self.alphagenome is None:
            return {
                'status': 'alphagenome_not_attached',
                'message': 'Attach an AlphaGenomeClient to PersonalizedHealthAdvisor '
                           'to enable Atlas enrichment.',
            }
        panel = self.alphagenome.analyze_panel(
            variants, patient_id=patient_id, consent_confirmed=consent_confirmed)
        # Cross-reference with AMRIT's curated knowledge where genes overlap
        for r in panel.get('results', []):
            gene = r.get('variant', {}).get('gene')
            for name, info in self.DNA_VARIANTS.items():
                if info.get('gene') == gene:
                    r['amrit_curated'] = {
                        'variant_key': name,
                        'risk_disease': info.get('risk_disease'),
                        'recommendations': info.get('recommendations'),
                    }
        return panel

    def analyze_dna(self, dna_variants: Dict[str, str]) -> Dict:
        """Analyze DNA variants and generate risk profile"""
        results = {}
        overall_risk = 0

        for variant, genotype in dna_variants.items():
            if variant in self.DNA_VARIANTS:
                variant_info = self.DNA_VARIANTS[variant]

                # Calculate risk
                risk_mult = variant_info['risk_multiplier'].get(genotype, 1.0)

                # Determine risk category
                if risk_mult >= 10:
                    risk_cat = RiskCategory.VERY_HIGH
                elif risk_mult >= 3:
                    risk_cat = RiskCategory.HIGH
                elif risk_mult >= 1.5:
                    risk_cat = RiskCategory.MODERATE
                else:
                    risk_cat = RiskCategory.LOW

                results[variant] = {
                    'gene': variant_info['gene'],
                    'variant': variant_info['variant'],
                    'genotype': genotype,
                    'risk_disease': variant_info['risk_disease'],
                    'risk_multiplier': risk_mult,
                    'risk_category': risk_cat.value,
                    'recommendations': variant_info['recommendations']
                }

                overall_risk += risk_mult

        return {
            'variants_analyzed': len(results),
            'variant_results': results,
            'overall_risk_score': overall_risk / max(len(results), 1),
            'highest_risk_variants': self._get_highest_risk(results)
        }

    def _get_highest_risk(self, results: Dict) -> List[str]:
        """Get variants with highest risk"""
        sorted_variants = sorted(
            results.items(),
            key=lambda x: x[1]['risk_multiplier'],
            reverse=True
        )
        return [v[0] for v in sorted_variants[:3]]

    def analyze_environment(self, environmental_data: Dict[str, float]) -> Dict:
        """Analyze environmental exposures"""
        results = {}

        for factor, level in environmental_data.items():
            if factor in self.ENVIRONMENTAL_FACTORS:
                factor_info = self.ENVIRONMENTAL_FACTORS[factor]

                # Calculate risk ratio
                risk_ratio = level / factor_info['safe_level']

                if risk_ratio > 3:
                    risk_level = 'critical'
                elif risk_ratio > 1.5:
                    risk_level = 'high'
                elif risk_ratio > 1:
                    risk_level = 'moderate'
                else:
                    risk_level = 'low'

                results[factor] = {
                    'level': level,
                    'unit': factor_info['unit'],
                    'safe_level': factor_info['safe_level'],
                    'risk_ratio': risk_ratio,
                    'risk_level': risk_level,
                    'health_effects': factor_info['health_effects'],
                    'mitigation': factor_info['mitigation']
                }

        return {
            'factors_analyzed': len(results),
            'exposure_results': results,
            'critical_exposures': [k for k, v in results.items() if v['risk_level'] == 'critical'],
            'high_exposures': [k for k, v in results.items() if v['risk_level'] == 'high']
        }

    def generate_recommendations(self, dna_results: Dict, 
                               blood_results: Dict,
                               environmental_results: Dict) -> Dict:
        """Generate comprehensive personalized recommendations"""
        recommendations = {
            'diet': [],
            'lifestyle': [],
            'supplements': [],
            'exercise': [],
            'screening': [],
            'mitigation': []
        }

        # DNA-based recommendations
        for variant, result in dna_results.get('variant_results', {}).items():
            recs = result.get('recommendations', {})
            recommendations['diet'].extend(recs.get('diet', []))
            recommendations['lifestyle'].extend(recs.get('lifestyle', []))
            recommendations['supplements'].extend(recs.get('supplements', []))
            recommendations['screening'].extend(recs.get('screening', []))

        # Blood-based recommendations
        for test, result in blood_results.get('analyzed', {}).items():
            if result.get('risk_level') in ['high', 'critical']:
                recommendations['diet'].extend(result.get('diet_recommendations', []))
                recommendations['lifestyle'].extend(result.get('lifestyle_recommendations', []))
                recommendations['supplements'].extend(result.get('supplement_recommendations', []))

        # Environmental recommendations
        for factor, result in environmental_results.get('exposure_results', {}).items():
            recommendations['mitigation'].extend(result.get('mitigation', []))

        # Deduplicate
        for category in recommendations:
            recommendations[category] = list(set(recommendations[category]))

        # Add exercise recommendations based on DNA
        if 'ACTN3' in dna_results.get('variant_results', {}):
            genotype = dna_results['variant_results']['ACTN3']['genotype']
            if genotype == 'RR':
                recommendations['exercise'].append('Power/sprint training optimal')
            elif genotype == 'XX':
                recommendations['exercise'].append('Endurance training optimal')
            else:
                recommendations['exercise'].append('Mixed training program')

        # Add general recommendations
        recommendations['exercise'].extend([
            '150 minutes moderate aerobic activity per week',
            '2 days strength training per week',
            'Daily flexibility exercises'
        ])

        return {
            'recommendations': recommendations,
            'priority_actions': self._prioritize_actions(recommendations),
            'follow_up_schedule': self._generate_follow_up(dna_results, blood_results)
        }

    def _prioritize_actions(self, recommendations: Dict) -> List[str]:
        """Prioritize actions based on urgency"""
        priorities = []

        # Critical items first
        if recommendations['mitigation']:
            priorities.append(f"URGENT: Address environmental exposures: {', '.join(recommendations['mitigation'][:3])}")

        if recommendations['screening']:
            priorities.append(f"Schedule screenings: {', '.join(recommendations['screening'][:3])}")

        if recommendations['supplements']:
            priorities.append(f"Start supplements: {', '.join(recommendations['supplements'][:3])}")

        if recommendations['diet']:
            priorities.append(f"Dietary changes: {', '.join(recommendations['diet'][:3])}")

        if recommendations['lifestyle']:
            priorities.append(f"Lifestyle modifications: {', '.join(recommendations['lifestyle'][:3])}")

        return priorities

    def _generate_follow_up(self, dna_results: Dict, blood_results: Dict) -> Dict:
        """Generate follow-up schedule"""
        schedule = {
            'immediate': [],
            '3_months': [],
            '6_months': [],
            '1_year': []
        }

        # Immediate actions
        if dna_results.get('highest_risk_variants'):
            schedule['immediate'].append('Genetic counseling consultation')

        # 3-month follow-up
        schedule['3_months'].append('Repeat blood panel')
        schedule['3_months'].append('Lifestyle adherence check')

        # 6-month follow-up
        schedule['6_months'].append('Comprehensive health review')
        schedule['6_months'].append('Environmental re-assessment')

        # 1-year follow-up
        schedule['1_year'].append('Annual physical examination')
        schedule['1_year'].append('Genetic risk re-evaluation')
        schedule['1_year'].append('Long-term outcome assessment')

        return schedule

    def full_health_assessment(self, patient_data: Dict) -> Dict:
        """Run complete health assessment"""
        dna_results = self.analyze_dna(patient_data.get('dna_variants', {}))
        env_results = self.analyze_environment(patient_data.get('environmental', {}))

        # Blood analysis would be done via BloodAnalyzer
        blood_results = patient_data.get('blood_results', {})

        recommendations = self.generate_recommendations(dna_results, blood_results, env_results)

        return {
            'patient_id': patient_data.get('id', 'unknown'),
            'assessment_date': datetime.now().isoformat(),
            'dna_analysis': dna_results,
            'blood_analysis': blood_results,
            'environmental_analysis': env_results,
            'recommendations': recommendations,
            'overall_health_score': self._calculate_health_score(dna_results, blood_results, env_results)
        }

    def _calculate_health_score(self, dna: Dict, blood: Dict, env: Dict) -> float:
        """Calculate overall health score"""
        score = 100.0

        # DNA risk deduction
        dna_risk = dna.get('overall_risk_score', 1.0)
        score -= (dna_risk - 1.0) * 5

        # Environmental deduction
        for factor, result in env.get('exposure_results', {}).items():
            if result['risk_level'] == 'critical':
                score -= 20
            elif result['risk_level'] == 'high':
                score -= 10
            elif result['risk_level'] == 'moderate':
                score -= 5

        # Blood test deduction
        for test, result in blood.get('analyzed', {}).items():
            if result.get('risk_level') == 'critical':
                score -= 15
            elif result.get('risk_level') == 'high':
                score -= 10

        return max(0, min(100, score))
