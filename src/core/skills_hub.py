"""
AMRIT Skills System v6.2
Modular skill system inspired by Hermes Agent
Each skill is a self-contained capability that can be loaded dynamically
"""
import os
import json
import importlib
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Skill:
    """Individual skill definition"""
    skill_id: str
    name: str
    description: str
    version: str
    author: str
    category: str
    entry_point: str  # Function name to call
    parameters: Dict[str, Any]
    required_modules: List[str]
    enabled: bool = True
    usage_count: int = 0
    last_used: Optional[str] = None

class SkillsHub:
    """
    Central hub for managing AMRIT skills
    Skills can be loaded, unloaded, and executed dynamically
    """

    def __init__(self, skills_dir: str = "src/skills"):
        self.skills_dir = skills_dir
        self.skills: Dict[str, Skill] = {}
        self.skill_functions: Dict[str, Callable] = {}
        self.skill_registry = {}
        self._init_default_skills()

    def _init_default_skills(self):
        """Initialize default AMRIT skills"""
        default_skills = {
            'blood_analysis': Skill(
                skill_id='blood_analysis',
                name='Blood Test Analysis',
                description='Analyze blood test results with 4-level detection',
                version='1.0.0',
                author='AMRIT System',
                category='medical',
                entry_point='analyze_blood_panel',
                parameters={
                    'tests': {'type': 'dict', 'required': True, 'description': 'Blood test values'},
                    'population': {'type': 'string', 'required': False, 'default': 'general'}
                },
                required_modules=['src.medical.blood_analyzer']
            ),
            'dna_analysis': Skill(
                skill_id='dna_analysis',
                name='DNA Variant Analysis',
                description='Analyze genetic variants for disease risk',
                version='1.0.0',
                author='AMRIT System',
                category='medical',
                entry_point='analyze_dna',
                parameters={
                    'variants': {'type': 'dict', 'required': True, 'description': 'DNA variants'},
                    'include_recommendations': {'type': 'bool', 'required': False, 'default': True}
                },
                required_modules=['src.medical.health_advisor']
            ),
            'consanguinity_check': Skill(
                skill_id='consanguinity_check',
                name='Consanguinity Risk Check',
                description='Assess genetic risks for consanguineous marriages',
                version='1.0.0',
                author='AMRIT System',
                category='medical',
                entry_point='check_consanguinity',
                parameters={
                    'relationship': {'type': 'string', 'required': True},
                    'disease': {'type': 'string', 'required': False, 'default': 'all'}
                },
                required_modules=['src.medical.consanguinity_drug']
            ),
            'drug_prediction': Skill(
                skill_id='drug_prediction',
                name='Drug Response Prediction',
                description='Predict drug response based on pharmacogenomics',
                version='1.0.0',
                author='AMRIT System',
                category='medical',
                entry_point='predict_drug_response',
                parameters={
                    'drug_name': {'type': 'string', 'required': True},
                    'biomarkers': {'type': 'dict', 'required': False}
                },
                required_modules=['src.medical.consanguinity_drug']
            ),
            'autonomous_research': Skill(
                skill_id='autonomous_research',
                name='Autonomous Research',
                description='Start AI-driven medical research with multi-agent collaboration',
                version='1.0.0',
                author='AMRIT System',
                category='research',
                entry_point='run_research',
                parameters={
                    'topic': {'type': 'string', 'required': True},
                    'duration_hours': {'type': 'int', 'required': False, 'default': 24}
                },
                required_modules=['src.autonomous.unified_agent']
            ),
            'ethics_check': Skill(
                skill_id='ethics_check',
                name='Ethics Assessment',
                description='Check actions against Gurmat and medical ethics',
                version='1.0.0',
                author='AMRIT System',
                category='ethics',
                entry_point='check_ethics',
                parameters={
                    'action': {'type': 'string', 'required': True},
                    'context': {'type': 'dict', 'required': False}
                },
                required_modules=['src.ethics.ethics_filter']
            ),
            'pandemic_prediction': Skill(
                skill_id='pandemic_prediction',
                name='Pandemic Risk Prediction',
                description='Predict pandemic risk with mitigation strategies',
                version='1.0.0',
                author='AMRIT System',
                category='prediction',
                entry_point='predict_pandemic',
                parameters={
                    'factors': {'type': 'dict', 'required': True}
                },
                required_modules=['src.autonomous.unified_agent']
            ),
            'health_advice': Skill(
                skill_id='health_advice',
                name='Personalized Health Advice',
                description='Provide comprehensive health recommendations',
                version='1.0.0',
                author='AMRIT System',
                category='medical',
                entry_point='get_health_advice',
                parameters={
                    'patient_data': {'type': 'dict', 'required': True}
                },
                required_modules=['src.medical.health_advisor']
            ),
            'team_configuration': Skill(
                skill_id='team_configuration',
                name='Agent Team Configuration',
                description='Configure optimal multi-agent team for tasks',
                version='1.0.0',
                author='AMRIT System',
                category='agents',
                entry_point='configure_team',
                parameters={
                    'task_type': {'type': 'string', 'required': True},
                    'complexity': {'type': 'string', 'required': False, 'default': 'medium'}
                },
                required_modules=['src.agents.harness_teams']
            ),
            'paper_generation': Skill(
                skill_id='paper_generation',
                name='Research Paper Generation',
                description='Auto-generate research papers in multiple formats',
                version='1.0.0',
                author='AMRIT System',
                category='research',
                entry_point='generate_paper',
                parameters={
                    'topic': {'type': 'string', 'required': True},
                    'format': {'type': 'string', 'required': False, 'default': 'APA'}
                },
                required_modules=['src.core.paper_writer']
            ),
            'knowledge_query': Skill(
                skill_id='knowledge_query',
                name='Knowledge Graph Query',
                description='Query medical knowledge graph for relationships',
                version='1.0.0',
                author='AMRIT System',
                category='knowledge',
                entry_point='query_knowledge',
                parameters={
                    'query': {'type': 'string', 'required': True},
                    'query_type': {'type': 'string', 'required': False, 'default': 'path'}
                },
                required_modules=['src.knowledge.knowledge_graph']
            ),
            'statistical_analysis': Skill(
                skill_id='statistical_analysis',
                name='Statistical Analysis',
                description='Run Monte Carlo, Bayesian, and other statistical tests',
                version='1.0.0',
                author='AMRIT System',
                category='statistics',
                entry_point='run_statistics',
                parameters={
                    'test_type': {'type': 'string', 'required': True},
                    'data': {'type': 'dict', 'required': True}
                },
                required_modules=['src.core.statistical_engine']
            )
        }

        for skill_id, skill in default_skills.items():
            self.register_skill(skill)

    def register_skill(self, skill: Skill) -> bool:
        """Register a new skill"""
        try:
            # Check if required modules are available
            for module_path in skill.required_modules:
                try:
                    importlib.import_module(module_path)
                except ImportError:
                    print("Warning: Module %s not available for skill %s" % (module_path, skill.skill_id))

            self.skills[skill.skill_id] = skill
            return True
        except Exception as e:
            print("Error registering skill %s: %s" % (skill.skill_id, str(e)))
            return False

    def execute_skill(self, skill_id: str, params: Dict) -> Dict:
        """Execute a skill with given parameters"""
        if skill_id not in self.skills:
            return {'error': 'Skill not found: %s' % skill_id}

        skill = self.skills[skill_id]

        if not skill.enabled:
            return {'error': 'Skill %s is disabled' % skill_id}

        # Validate parameters
        validation = self._validate_params(skill, params)
        if not validation['valid']:
            return {'error': 'Parameter validation failed', 'details': validation['errors']}

        # Update usage stats
        skill.usage_count += 1
        skill.last_used = datetime.now().isoformat()

        # Execute (simplified - in real implementation, call actual function)
        return {
            'status': 'success',
            'skill': skill_id,
            'result': 'Executed %s with params: %s' % (skill.name, str(params)),
            'timestamp': datetime.now().isoformat()
        }

    def _validate_params(self, skill: Skill, params: Dict) -> Dict:
        """Validate parameters against skill definition"""
        errors = []

        for param_name, param_def in skill.parameters.items():
            if param_def.get('required', False) and param_name not in params:
                errors.append('Missing required parameter: %s' % param_name)

            if param_name in params:
                param_type = param_def.get('type', 'string')
                value = params[param_name]

                if param_type == 'int' and not isinstance(value, int):
                    errors.append('Parameter %s should be integer' % param_name)
                elif param_type == 'bool' and not isinstance(value, bool):
                    errors.append('Parameter %s should be boolean' % param_name)
                elif param_type == 'dict' and not isinstance(value, dict):
                    errors.append('Parameter %s should be dictionary' % param_name)

        return {'valid': len(errors) == 0, 'errors': errors}

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get skill by ID"""
        return self.skills.get(skill_id)

    def list_skills(self, category: str = None, enabled_only: bool = True) -> List[Dict]:
        """List all skills with optional filtering"""
        results = []

        for skill_id, skill in self.skills.items():
            if category and skill.category != category:
                continue
            if enabled_only and not skill.enabled:
                continue

            results.append({
                'skill_id': skill.skill_id,
                'name': skill.name,
                'description': skill.description,
                'version': skill.version,
                'category': skill.category,
                'enabled': skill.enabled,
                'usage_count': skill.usage_count,
                'last_used': skill.last_used
            })

        return results

    def disable_skill(self, skill_id: str) -> bool:
        """Disable a skill"""
        if skill_id in self.skills:
            self.skills[skill_id].enabled = False
            return True
        return False

    def enable_skill(self, skill_id: str) -> bool:
        """Enable a skill"""
        if skill_id in self.skills:
            self.skills[skill_id].enabled = True
            return True
        return False

    def get_skill_stats(self) -> Dict:
        """Get skills hub statistics"""
        categories = {}
        total_usage = 0

        for skill in self.skills.values():
            cat = skill.category
            categories[cat] = categories.get(cat, 0) + 1
            total_usage += skill.usage_count

        return {
            'total_skills': len(self.skills),
            'enabled_skills': sum(1 for s in self.skills.values() if s.enabled),
            'disabled_skills': sum(1 for s in self.skills.values() if not s.enabled),
            'categories': categories,
            'total_usage': total_usage,
            'most_used': sorted(
                [(s.skill_id, s.usage_count) for s in self.skills.values()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }

    def discover_skills(self, query: str) -> List[Dict]:
        """Discover skills matching query"""
        query_lower = query.lower()
        matches = []

        for skill in self.skills.values():
            score = 0
            if query_lower in skill.name.lower():
                score += 3
            if query_lower in skill.description.lower():
                score += 2
            if query_lower in skill.category.lower():
                score += 1

            if score > 0:
                matches.append({
                    'skill': skill.skill_id,
                    'score': score,
                    'name': skill.name,
                    'description': skill.description
                })

        return sorted(matches, key=lambda x: x['score'], reverse=True)

    def auto_select_skill(self, query: str) -> Optional[str]:
        """Auto-select best skill for query"""
        matches = self.discover_skills(query)

        if matches:
            best_match = matches[0]
            skill = self.skills.get(best_match['skill'])
            if skill and skill.enabled:
                return best_match['skill']

        return None


class SkillComposer:
    """
    Compose multiple skills into workflows
    Inspired by Hermes skill composition
    """

    def __init__(self, skills_hub: SkillsHub):
        self.skills_hub = skills_hub
        self.workflows = {}

    def create_workflow(self, name: str, steps: List[Dict]) -> str:
        """Create a new workflow from skill steps"""
        workflow_id = "workflow_%s" % name.lower().replace(' ', '_')

        self.workflows[workflow_id] = {
            'name': name,
            'steps': steps,
            'created_at': datetime.now().isoformat()
        }

        return workflow_id

    def execute_workflow(self, workflow_id: str, initial_params: Dict) -> List[Dict]:
        """Execute a workflow step by step"""
        if workflow_id not in self.workflows:
            return [{'error': 'Workflow not found'}]

        workflow = self.workflows[workflow_id]
        results = []
        current_params = initial_params.copy()

        for step in workflow['steps']:
            skill_id = step['skill']
            param_mapping = step.get('param_mapping', {})

            # Map parameters
            step_params = {}
            for target_param, source in param_mapping.items():
                if source in current_params:
                    step_params[target_param] = current_params[source]

            # Execute skill
            result = self.skills_hub.execute_skill(skill_id, step_params)
            results.append(result)

            # Update params for next step
            if 'output_mapping' in step:
                for output_key, target_key in step['output_mapping'].items():
                    if output_key in result:
                        current_params[target_key] = result[output_key]

        return results


# Pre-defined workflows
PREDEFINED_WORKFLOWS = {
    'full_health_check': {
        'name': 'Complete Health Assessment',
        'steps': [
            {'skill': 'blood_analysis', 'param_mapping': {'tests': 'blood_tests'}},
            {'skill': 'dna_analysis', 'param_mapping': {'variants': 'dna_variants'}},
            {'skill': 'health_advice', 'param_mapping': {'patient_data': 'combined_data'}}
        ]
    },
    'research_pipeline': {
        'name': 'Autonomous Research Pipeline',
        'steps': [
            {'skill': 'autonomous_research', 'param_mapping': {'topic': 'research_topic'}},
            {'skill': 'ethics_check', 'param_mapping': {'action': 'research_proposal'}},
            {'skill': 'paper_generation', 'param_mapping': {'topic': 'research_topic'}}
        ]
    },
    'drug_safety_check': {
        'name': 'Drug Safety Assessment',
        'steps': [
            {'skill': 'drug_prediction', 'param_mapping': {'drug_name': 'drug', 'biomarkers': 'genetic_data'}},
            {'skill': 'ethics_check', 'param_mapping': {'action': 'prescription'}},
            {'skill': 'health_advice', 'param_mapping': {'patient_data': 'patient_profile'}}
        ]
    }
}
