
"""
AMRIT ConsanguinityRisk & DrugPredictor
South Asian focused genetic risk assessment and pharmacogenomics
"""
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

class RelationshipType(Enum):
    FIRST_COUSIN = "first_cousin"  # 1/8 shared genes
    DOUBLE_FIRST_COUSIN = "double_first_cousin"  # 1/4 shared genes
    UNCLE_NIECE = "uncle_niece"  # 1/8 shared genes
    SECOND_COUSIN = "second_cousin"  # 1/32 shared genes
    AVUNCULAR = "avuncular"  # 1/8 shared genes
    HALF_SIBLING = "half_sibling"  # 1/8 shared genes

@dataclass
class DiseaseRisk:
    disease_name: str
    carrier_frequency: float  # General population
    consanguinity_multiplier: float
    risk_level: str
    screening_recommended: bool
    management: List[str]

class ConsanguinityRisk:
    """
    Consanguinity risk calculator for South Asian populations
    20+ diseases with relationship-specific risk
    """

    # Coefficient of relationship
    RELATIONSHIP_COEFFICIENTS = {
        RelationshipType.FIRST_COUSIN: 1/8,
        RelationshipType.DOUBLE_FIRST_COUSIN: 1/4,
        RelationshipType.UNCLE_NIECE: 1/8,
        RelationshipType.SECOND_COUSIN: 1/32,
        RelationshipType.AVUNCULAR: 1/8,
        RelationshipType.HALF_SIBLING: 1/8,
    }

    # Disease database (South Asian focused)
    DISEASES = {
        'thalassemia': DiseaseRisk(
            'Beta-Thalassemia', 0.03, 8.0, 'high', True,
            ['HPLC screening', 'Genetic counseling', 'Prenatal diagnosis']
        ),
        'sickle_cell': DiseaseRisk(
            'Sickle Cell Disease', 0.02, 6.0, 'high', True,
            ['Hemoglobin electrophoresis', 'Genetic testing', 'Prenatal screening']
        ),
        'cystic_fibrosis': DiseaseRisk(
            'Cystic Fibrosis', 0.025, 5.0, 'moderate', True,
            ['Sweat chloride test', 'CFTR gene analysis', 'Carrier screening']
        ),
        'tay_sachs': DiseaseRisk(
            'Tay-Sachs Disease', 0.01, 10.0, 'high', True,
            ['Hexosaminidase A assay', 'HEXA gene testing', 'Prenatal diagnosis']
        ),
        'gaucher': DiseaseRisk(
            'Gaucher Disease', 0.008, 8.0, 'moderate', True,
            ['Beta-glucosidase assay', 'GBA gene testing', 'Enzyme replacement']
        ),
        'familial_mediterranean_fever': DiseaseRisk(
            'Familial Mediterranean Fever', 0.01, 6.0, 'moderate', True,
            ['MEFV gene analysis', 'Colchicine prophylaxis', 'Genetic counseling']
        ),
        'congenital_adrenal_hyperplasia': DiseaseRisk(
            'Congenital Adrenal Hyperplasia', 0.005, 7.0, 'high', True,
            ['17-OHP screening', 'CYP21A2 gene analysis', 'Hormone replacement']
        ),
        'spinal_muscular_atrophy': DiseaseRisk(
            'Spinal Muscular Atrophy', 0.01, 8.0, 'high', True,
            ['SMN1 gene deletion test', 'Prenatal diagnosis', 'Gene therapy referral']
        ),
        'duchenne_muscular_dystrophy': DiseaseRisk(
            'Duchenne Muscular Dystrophy', 0.003, 5.0, 'moderate', True,
            ['CK level', 'DMD gene analysis', 'Genetic counseling']
        ),
        'hemophilia': DiseaseRisk(
            'Hemophilia', 0.001, 4.0, 'moderate', True,
            ['Factor VIII/IX assay', 'F8/F9 gene analysis', 'Prenatal diagnosis']
        ),
        'phenylketonuria': DiseaseRisk(
            'Phenylketonuria', 0.01, 6.0, 'moderate', True,
            ['Newborn screening', 'PAH gene analysis', 'Dietary management']
        ),
        'galactosemia': DiseaseRisk(
            'Galactosemia', 0.003, 7.0, 'moderate', True,
            ['GALT enzyme assay', 'GALT gene testing', 'Lactose-free diet']
        ),
        'maple_syrup_urine_disease': DiseaseRisk(
            'Maple Syrup Urine Disease', 0.002, 8.0, 'high', True,
            ['Plasma amino acids', 'BCKD gene analysis', 'Dietary management']
        ),
        'homocystinuria': DiseaseRisk(
            'Homocystinuria', 0.002, 7.0, 'moderate', True,
            ['Plasma homocysteine', 'CBS gene analysis', 'Pyridoxine trial']
        ),
        'wilson_disease': DiseaseRisk(
            'Wilson Disease', 0.003, 6.0, 'moderate', True,
            ['Ceruloplasmin', 'ATP7B gene analysis', 'Chelation therapy']
        ),
        'alpha_1_antitrypsin_deficiency': DiseaseRisk(
            'Alpha-1 Antitrypsin Deficiency', 0.02, 4.0, 'moderate', True,
            ['AAT level', 'SERPINA1 gene analysis', 'Smoking cessation']
        ),
        'hereditary_hemochromatosis': DiseaseRisk(
            'Hereditary Hemochromatosis', 0.005, 5.0, 'moderate', True,
            ['Ferritin/Transferrin saturation', 'HFE gene analysis', 'Phlebotomy']
        ),
        'marfan_syndrome': DiseaseRisk(
            'Marfan Syndrome', 0.002, 4.0, 'moderate', True,
            ['FBN1 gene analysis', 'Echocardiography', 'Aortic monitoring']
        ),
        'neurofibromatosis': DiseaseRisk(
            'Neurofibromatosis Type 1', 0.003, 4.0, 'moderate', True,
            ['NF1 gene analysis', 'Clinical examination', 'Tumor surveillance']
        ),
        'tuberous_sclerosis': DiseaseRisk(
            'Tuberous Sclerosis', 0.001, 5.0, 'moderate', True,
            ['TSC1/TSC2 gene analysis', 'MRI brain/kidney', 'Seizure management']
        ),
    }

    def __init__(self, relationship: RelationshipType = None):
        self.relationship = relationship
        self.coefficient = self.RELATIONSHIP_COEFFICIENTS.get(relationship, 0)

    def calculate_risk(self, disease_name: str) -> Dict:
        """Calculate risk for a specific disease"""
        disease = self.DISEASES.get(disease_name.lower())

        if not disease:
            return {'error': 'Disease not found in database'}

        # Risk calculation
        base_risk = disease.carrier_frequency ** 2  # General population risk
        consanguinity_risk = base_risk * disease.consanguinity_multiplier * self.coefficient * 8

        # Risk ratio
        risk_ratio = consanguinity_risk / base_risk if base_risk > 0 else 0

        return {
            'disease': disease.disease_name,
            'relationship': self.relationship.value if self.relationship else 'unknown',
            'coefficient': self.coefficient,
            'general_population_risk': base_risk,
            'consanguinity_risk': consanguinity_risk,
            'risk_ratio': risk_ratio,
            'risk_level': disease.risk_level,
            'screening_recommended': disease.screening_recommended,
            'management': disease.management,
            'counseling_advice': self._generate_counseling(disease, risk_ratio)
        }

    def _generate_counseling(self, disease: DiseaseRisk, risk_ratio: float) -> str:
        """Generate genetic counseling advice"""
        if risk_ratio > 10:
            return f"""HIGH RISK: Strongly recommend preconception genetic counseling and carrier screening for {disease.disease_name}. Consider prenatal diagnosis if both partners are carriers."""
        elif risk_ratio > 5:
            return f"""MODERATE-HIGH RISK: Recommend carrier screening for {disease.disease_name}. Genetic counseling advised before conception."""
        elif risk_ratio > 2:
            return f"""MODERATE RISK: Consider carrier screening for {disease.disease_name} based on family history."""
        else:
            return f"""LOW RISK: Standard population screening for {disease.disease_name} is sufficient."""

    def full_risk_assessment(self) -> Dict:
        """Full risk assessment for all diseases"""
        results = {}
        high_risk_diseases = []

        for disease_key, disease in self.DISEASES.items():
            risk = self.calculate_risk(disease_key)
            results[disease_key] = risk

            if risk.get('risk_ratio', 0) > 5:
                high_risk_diseases.append(disease_key)

        return {
            'relationship': self.relationship.value if self.relationship else 'unknown',
            'coefficient': self.coefficient,
            'total_diseases_assessed': len(self.DISEASES),
            'high_risk_diseases': high_risk_diseases,
            'disease_risks': results,
            'overall_recommendation': self._overall_recommendation(high_risk_diseases)
        }

    def _overall_recommendation(self, high_risk_diseases: List[str]) -> str:
        """Generate overall recommendation"""
        if len(high_risk_diseases) > 5:
            return """STRONG RECOMMENDATION: Comprehensive genetic counseling and expanded carrier screening strongly advised before conception. Consider all high-risk conditions."""
        elif len(high_risk_diseases) > 2:
            return """RECOMMENDATION: Genetic counseling and targeted carrier screening recommended for identified high-risk conditions."""
        elif len(high_risk_diseases) > 0:
            return """ADVISORY: Consider screening for specific high-risk conditions identified. Standard prenatal care appropriate."""
        else:
            return """Standard population screening and prenatal care recommended. No additional consanguinity-specific risks identified."""


class DrugPredictor:
    """
    Pharmacogenomics-based drug prediction
    13 biomarkers, 10 drug predictions
    """

    # Pharmacogenomic markers
    BIOMARKERS = {
        'CYP2D6': {
            'phenotypes': ['ultrarapid', 'extensive', 'intermediate', 'poor'],
            'drugs_affected': ['codeine', 'tamoxifen', 'tramadol', 'antidepressants']
        },
        'CYP2C19': {
            'phenotypes': ['ultrarapid', 'extensive', 'intermediate', 'poor'],
            'drugs_affected': ['clopidogrel', 'omeprazole', 'diazepam', 'phenytoin']
        },
        'CYP2C9': {
            'phenotypes': ['extensive', 'intermediate', 'poor'],
            'drugs_affected': ['warfarin', 'phenytoin', 'losartan', 'celecoxib']
        },
        'CYP3A4': {
            'phenotypes': ['extensive', 'intermediate', 'poor'],
            'drugs_affected': ['statins', 'calcium_channel_blockers', 'immunosuppressants']
        },
        'TPMT': {
            'phenotypes': ['normal', 'intermediate', 'poor'],
            'drugs_affected': ['azathioprine', '6-mercaptopurine', 'thioguanine']
        },
        'DPYD': {
            'phenotypes': ['normal', 'intermediate', 'poor'],
            'drugs_affected': ['5-fluorouracil', 'capecitabine', 'tegafur']
        },
        'SLCO1B1': {
            'phenotypes': ['normal', 'intermediate', 'poor'],
            'drugs_affected': ['simvastatin', 'atorvastatin', 'pravastatin']
        },
        'VKORC1': {
            'phenotypes': ['high', 'intermediate', 'low'],
            'drugs_affected': ['warfarin']
        },
        'HLA-B*57:01': {
            'phenotypes': ['positive', 'negative'],
            'drugs_affected': ['abacavir']
        },
        'HLA-B*15:02': {
            'phenotypes': ['positive', 'negative'],
            'drugs_affected': ['carbamazepine']
        },
        'HLA-B*58:01': {
            'phenotypes': ['positive', 'negative'],
            'drugs_affected': ['allopurinol']
        },
        'G6PD': {
            'phenotypes': ['normal', 'deficient'],
            'drugs_affected': ['primaquine', 'dapsone', 'nitrofurantoin', 'rasburicase']
        },
        'UGT1A1': {
            'phenotypes': ['normal', 'intermediate', 'poor'],
            'drugs_affected': ['irinotecan', 'atazanavir', 'nilotinib']
        }
    }

    # Drug-specific recommendations
    DRUG_RECOMMENDATIONS = {
        'warfarin': {
            'CYP2C9_poor': 'Reduce dose by 50-80%, monitor INR closely',
            'VKORC1_low': 'Reduce dose by 30-50%',
            'standard': 'Standard dosing with INR monitoring'
        },
        'clopidogrel': {
            'CYP2C19_poor': 'Consider alternative antiplatelet (prasugrel/ticagrelor)',
            'standard': 'Standard clopidogrel dosing'
        },
        'codeine': {
            'CYP2D6_poor': 'Avoid - no analgesic effect; use alternative opioid',
            'CYP2D6_ultrarapid': 'Avoid - increased toxicity risk; use alternative',
            'standard': 'Standard dosing with monitoring'
        },
        'azathioprine': {
            'TPMT_poor': 'Reduce dose by 90% or avoid; high toxicity risk',
            'TPMT_intermediate': 'Reduce dose by 30-50%',
            'standard': 'Standard dosing with CBC monitoring'
        },
        'simvastatin': {
            'SLCO1B1_poor': 'Reduce dose or consider pravastatin; high myopathy risk',
            'standard': 'Standard dosing with CK monitoring'
        },
        'carbamazepine': {
            'HLA-B*15:02_positive': 'CONTRAINDICATED - High SJS/TEN risk in Asian populations',
            'standard': 'Standard dosing with skin reaction monitoring'
        },
        'abacavir': {
            'HLA-B*57:01_positive': 'CONTRAINDICATED - Hypersensitivity reaction risk',
            'standard': 'Standard dosing'
        },
        'allopurinol': {
            'HLA-B*58:01_positive': 'CAUTION - Increased SJS/TEN risk in Han Chinese/Thai',
            'standard': 'Standard dosing with skin monitoring'
        },
        '5-fluorouracil': {
            'DPYD_poor': 'CONTRAINDICATED - Severe toxicity risk; use alternative',
            'DPYD_intermediate': 'Reduce dose by 50%',
            'standard': 'Standard dosing'
        },
        'irinotecan': {
            'UGT1A1_poor': 'Reduce dose by 30%; high neutropenia/diarrhea risk',
            'standard': 'Standard dosing with CBC monitoring'
        }
    }

    def __init__(self, biomarker_data: Dict[str, str] = None):
        self.biomarker_data = biomarker_data or {}

    def predict_drug_response(self, drug_name: str) -> Dict:
        """Predict drug response based on biomarkers"""
        drug_name = drug_name.lower()
        recommendations = self.DRUG_RECOMMENDATIONS.get(drug_name, {})

        if not recommendations:
            return {
                'drug': drug_name,
                'status': 'unknown',
                'recommendation': 'No pharmacogenomic data available for this drug'
            }

        # Check biomarkers for this drug
        relevant_markers = []
        for marker, phenotype in self.biomarker_data.items():
            marker_upper = marker.upper()
            key = f"{marker_upper}_{phenotype}"

            if key in recommendations:
                relevant_markers.append({
                    'marker': marker_upper,
                    'phenotype': phenotype,
                    'recommendation': recommendations[key]
                })

        if relevant_markers:
            return {
                'drug': drug_name,
                'status': 'pharmacogenomic_guidance_available',
                'biomarkers': relevant_markers,
                'primary_recommendation': relevant_markers[0]['recommendation'],
                'action_required': any('CONTRAINDICATED' in r['recommendation'] for r in relevant_markers)
            }

        return {
            'drug': drug_name,
            'status': 'standard_dosing',
            'recommendation': recommendations.get('standard', 'Standard dosing')
        }

    def full_medication_review(self, medications: List[str]) -> Dict:
        """Review all medications for pharmacogenomic interactions"""
        results = {}
        warnings = []
        contraindications = []

        for drug in medications:
            prediction = self.predict_drug_response(drug)
            results[drug] = prediction

            if prediction.get('action_required'):
                contraindications.append(drug)
            elif prediction['status'] == 'pharmacogenomic_guidance_available':
                warnings.append(drug)

        return {
            'total_medications': len(medications),
            'pharmacogenomic_guidance': len([r for r in results.values() if r['status'] == 'pharmacogenomic_guidance_available']),
            'contraindications': contraindications,
            'warnings': warnings,
            'drug_predictions': results,
            'overall_recommendation': self._generate_medication_recommendation(contraindications, warnings)
        }

    def _generate_medication_recommendation(self, contraindications: List[str], warnings: List[str]) -> str:
        """Generate overall medication recommendation"""
        if contraindications:
            return f"""CRITICAL: {len(contraindications)} medication(s) have pharmacogenomic contraindications. Immediate medication review required. Consider alternative therapies."""
        elif warnings:
            return f"""WARNING: {len(warnings)} medication(s) require pharmacogenomic dose adjustment. Consult clinical pharmacist."""
        else:
            return """All medications can be used with standard dosing. Continue current regimen."""
