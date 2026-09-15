"""
AMRIT Auto-UI Generator v6.2
Automatically generates HTML/CSS/JS panels for each module
Inspired by AI Website Cloner - adaptive UI generation
"""
import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class UIPanel:
    panel_id: str
    module_name: str
    title: str
    description: str
    html: str
    css: str
    js: str
    components: List[Dict]
    generated_at: str

class AutoUIGenerator:
    """
    Generates adaptive UI panels for AMRIT modules
    Each module gets its own visual interface
    """

    def __init__(self, output_dir: str = "src/dashboard/static/panels"):
        self.output_dir = output_dir
        self.panels: Dict[str, UIPanel] = {}
        self.component_library = self._build_component_library()
        os.makedirs(output_dir, exist_ok=True)

    def _build_component_library(self) -> Dict:
        """Build reusable UI component library"""
        return {
            'input_text': {
                'template': '<div class="form-group"><label>{label}</label><input type="text" name="{name}" placeholder="{placeholder}" class="form-control"></div>',
                'params': ['label', 'name', 'placeholder']
            },
            'input_number': {
                'template': '<div class="form-group"><label>{label}</label><input type="number" name="{name}" min="{min}" max="{max}" step="{step}" class="form-control"></div>',
                'params': ['label', 'name', 'min', 'max', 'step']
            },
            'select': {
                'template': '<div class="form-group"><label>{label}</label><select name="{name}" class="form-control">{options}</select></div>',
                'params': ['label', 'name', 'options']
            },
            'button': {
                'template': '<button type="button" onclick="{onclick}" class="btn btn-primary">{label}</button>',
                'params': ['label', 'onclick']
            },
            'card': {
                'template': '<div class="card"><div class="card-header">{title}</div><div class="card-body">{content}</div></div>',
                'params': ['title', 'content']
            },
            'chart_placeholder': {
                'template': '<div class="chart-container" id="{id}"><canvas id="{canvas_id}"></canvas></div>',
                'params': ['id', 'canvas_id']
            },
            'result_display': {
                'template': '<div class="result-panel" id="{id}"><div class="loading">Processing...</div></div>',
                'params': ['id']
            },
            'table': {
                'template': '<table class="data-table" id="{id}"><thead>{header}</thead><tbody>{body}</tbody></table>',
                'params': ['id', 'header', 'body']
            },
            'alert': {
                'template': '<div class="alert alert-{type}" id="{id}">{message}</div>',
                'params': ['id', 'type', 'message']
            },
            'progress_bar': {
                'template': '<div class="progress"><div class="progress-bar" id="{id}" style="width: 0%"></div></div>',
                'params': ['id']
            }
        }

    def generate_panel(self, module_name: str, module_config: Dict) -> UIPanel:
        """Generate complete UI panel for a module"""

        panel_id = "panel_%s_%s" % (module_name.lower(), datetime.now().strftime('%Y%m%d'))

        # Generate components based on module config
        components = self._generate_components(module_config)

        # Generate HTML
        html = self._generate_html(panel_id, module_config, components)

        # Generate CSS
        css = self._generate_css(panel_id, module_config)

        # Generate JS
        js = self._generate_js(panel_id, module_name, module_config)

        panel = UIPanel(
            panel_id=panel_id,
            module_name=module_name,
            title=module_config.get('title', module_name),
            description=module_config.get('description', ''),
            html=html,
            css=css,
            js=js,
            components=components,
            generated_at=datetime.now().isoformat()
        )

        self.panels[panel_id] = panel
        self._save_panel(panel)

        return panel

    def _generate_components(self, config: Dict) -> List[Dict]:
        """Generate UI components from module configuration"""
        components = []

        # Input fields
        for field in config.get('input_fields', []):
            comp_type = field.get('type', 'text')
            if comp_type == 'number':
                components.append({
                    'type': 'input_number',
                    'params': {
                        'label': field.get('label', 'Value'),
                        'name': field.get('name', 'input'),
                        'min': field.get('min', 0),
                        'max': field.get('max', 1000),
                        'step': field.get('step', 1)
                    }
                })
            elif comp_type == 'select':
                options = ''.join(['<option value="%s">%s</option>' % (v, v) for v in field.get('options', [])])
                components.append({
                    'type': 'select',
                    'params': {
                        'label': field.get('label', 'Select'),
                        'name': field.get('name', 'select'),
                        'options': options
                    }
                })
            else:
                components.append({
                    'type': 'input_text',
                    'params': {
                        'label': field.get('label', 'Input'),
                        'name': field.get('name', 'input'),
                        'placeholder': field.get('placeholder', 'Enter value...')
                    }
                })

        # Action button
        components.append({
            'type': 'button',
            'params': {
                'label': config.get('action_label', 'Analyze'),
                'onclick': 'submit_%s()' % config.get('module_id', 'module')
            }
        })

        # Result display
        components.append({
            'type': 'result_display',
            'params': {
                'id': 'result_%s' % config.get('module_id', 'module')
            }
        })

        # Chart if needed
        if config.get('has_chart', False):
            components.append({
                'type': 'chart_placeholder',
                'params': {
                    'id': 'chart_container',
                    'canvas_id': 'chart_canvas'
                }
            })

        return components

    def _generate_html(self, panel_id: str, config: Dict, components: List[Dict]) -> str:
        """Generate HTML structure"""

        html_parts = ['<div class="panel" id="%s">' % panel_id]
        html_parts.append('  <div class="panel-header">')
        html_parts.append('    <h2>%s</h2>' % config.get('title', 'Panel'))
        html_parts.append('    <p>%s</p>' % config.get('description', ''))
        html_parts.append('  </div>')
        html_parts.append('  <div class="panel-body">')
        html_parts.append('    <form id="form_%s" onsubmit="return false;">' % panel_id)

        # Add components
        for comp in components:
            comp_def = self.component_library.get(comp['type'])
            if comp_def:
                template = comp_def['template']
                html_parts.append('    ' + template.format(**comp['params']))

        html_parts.append('    </form>')
        html_parts.append('  </div>')
        html_parts.append('</div>')

        return '\n'.join(html_parts)

    def _generate_css(self, panel_id: str, config: Dict) -> str:
        """Generate CSS styles"""

        primary_color = config.get('primary_color', '#667eea')
        secondary_color = config.get('secondary_color', '#764ba2')

        css = """
#%(panel_id)s {
    background: white;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    padding: 30px;
    margin: 20px;
    max-width: 600px;
    transition: transform 0.3s, box-shadow 0.3s;
}

#%(panel_id)s:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.15);
}

#%(panel_id)s .panel-header {
    border-bottom: 2px solid %(primary_color)s;
    padding-bottom: 15px;
    margin-bottom: 20px;
}

#%(panel_id)s .panel-header h2 {
    color: %(primary_color)s;
    margin: 0;
    font-size: 24px;
}

#%(panel_id)s .panel-header p {
    color: #666;
    margin: 5px 0 0 0;
    font-size: 14px;
}

#%(panel_id)s .form-group {
    margin-bottom: 20px;
}

#%(panel_id)s label {
    display: block;
    margin-bottom: 8px;
    color: #333;
    font-weight: 600;
    font-size: 14px;
}

#%(panel_id)s .form-control {
    width: 100%%;
    padding: 12px 15px;
    border: 2px solid #e5e7eb;
    border-radius: 10px;
    font-size: 15px;
    transition: border-color 0.3s, box-shadow 0.3s;
    box-sizing: border-box;
}

#%(panel_id)s .form-control:focus {
    border-color: %(primary_color)s;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    outline: none;
}

#%(panel_id)s .btn-primary {
    background: linear-gradient(135deg, %(primary_color)s, %(secondary_color)s);
    color: white;
    border: none;
    padding: 14px 30px;
    border-radius: 10px;
    font-size: 16px;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    width: 100%%;
}

#%(panel_id)s .btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
}

#%(panel_id)s .result-panel {
    margin-top: 20px;
    padding: 20px;
    background: #f9fafb;
    border-radius: 10px;
    border-left: 4px solid %(primary_color)s;
    display: none;
}

#%(panel_id)s .result-panel.active {
    display: block;
    animation: fadeIn 0.5s ease;
}

#%(panel_id)s .alert {
    padding: 12px 15px;
    border-radius: 8px;
    margin-bottom: 15px;
}

#%(panel_id)s .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
#%(panel_id)s .alert-warning { background: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
#%(panel_id)s .alert-danger { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
#%(panel_id)s .alert-info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }

#%(panel_id)s .chart-container {
    margin-top: 20px;
    height: 300px;
    position: relative;
}

#%(panel_id)s .data-table {
    width: 100%%;
    border-collapse: collapse;
    margin-top: 15px;
}

#%(panel_id)s .data-table th,
#%(panel_id)s .data-table td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #e5e7eb;
}

#%(panel_id)s .data-table th {
    background: #f9fafb;
    font-weight: 600;
    color: #374151;
}

#%(panel_id)s .progress {
    height: 8px;
    background: #e5e7eb;
    border-radius: 4px;
    overflow: hidden;
    margin-top: 10px;
}

#%(panel_id)s .progress-bar {
    height: 100%%;
    background: linear-gradient(90deg, %(primary_color)s, %(secondary_color)s);
    border-radius: 4px;
    transition: width 0.5s ease;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
""" % {
    'panel_id': panel_id,
    'primary_color': primary_color,
    'secondary_color': secondary_color
}

        return css

    def _generate_js(self, panel_id: str, module_name: str, config: Dict) -> str:
        """Generate JavaScript for interactivity"""

        api_endpoint = config.get('api_endpoint', '/api/%s/analyze' % module_name.lower())

        js = """
function submit_%(module_name)s() {
    const form = document.getElementById('form_%(panel_id)s');
    const formData = new FormData(form);
    const data = {};

    formData.forEach((value, key) => {
        data[key] = value;
    });

    // Show loading
    const resultPanel = document.getElementById('result_%(panel_id)s');
    resultPanel.innerHTML = '<div class="loading">🕉️ AMRIT is analyzing...</div>';
    resultPanel.classList.add('active');

    // Call API
    fetch('%(api_endpoint)s', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        displayResult_%(module_name)s(result, resultPanel);
    })
    .catch(error => {
        resultPanel.innerHTML = '<div class="alert alert-danger">Error: ' + error.message + '</div>';
    });
}

function displayResult_%(module_name)s(result, panel) {
    let html = '';

    if (result.status === 'success' || result.overall_status) {
        html += '<div class="alert alert-success">✅ Analysis Complete</div>';

        // Display results based on structure
        if (result.results) {
            html += '<h4>Results:</h4>';
            html += '<table class="data-table">';
            html += '<tr><th>Test</th><th>Value</th><th>Status</th></tr>';

            for (const [key, value] of Object.entries(result.results)) {
                const status = value.status || value.risk_level || 'unknown';
                const statusClass = status === 'normal' || status === 'low' ? 'alert-success' : 
                                   status === 'borderline' || status === 'moderate' ? 'alert-warning' : 'alert-danger';
                html += '<tr><td>' + key + '</td><td>' + (value.value || JSON.stringify(value)) + '</td><td><span class="alert ' + statusClass + '">' + status + '</span></td></tr>';
            }
            html += '</table>';
        }

        if (result.recommendations) {
            html += '<h4>Recommendations:</h4><ul>';
            result.recommendations.forEach(rec => {
                html += '<li>' + rec + '</li>';
            });
            html += '</ul>';
        }

        if (result.overall_risk) {
            html += '<div class="alert alert-info">Overall Risk: <strong>' + result.overall_risk + '</strong></div>';
        }
    } else {
        html += '<div class="alert alert-danger">❌ Analysis Failed</div>';
        html += '<p>' + (result.error || 'Unknown error') + '</p>';
    }

    panel.innerHTML = html;
}

// Auto-refresh capability
function autoRefresh_%(module_name)s(intervalMinutes) {
    setInterval(() => {
        console.log('🕉️ Auto-refreshing %(module_name)s panel');
        // Refresh logic here
    }, intervalMinutes * 60 * 1000);
}

// Export for global access
window.submit_%(module_name)s = submit_%(module_name)s;
window.displayResult_%(module_name)s = displayResult_%(module_name)s;
""" % {
    'module_name': module_name.lower().replace(' ', '_'),
    'panel_id': panel_id,
    'api_endpoint': api_endpoint
}

        return js

    def _save_panel(self, panel: UIPanel):
        """Save panel to file"""
        # Save HTML
        html_path = os.path.join(self.output_dir, "%s.html" % panel.panel_id)
        with open(html_path, 'w') as f:
            f.write('<style>\n%s\n</style>\n' % panel.css)
            f.write(panel.html)
            f.write('<script>\n%s\n</script>' % panel.js)

        # Save metadata
        meta_path = os.path.join(self.output_dir, "%s.json" % panel.panel_id)
        with open(meta_path, 'w') as f:
            json.dump({
                'panel_id': panel.panel_id,
                'module_name': panel.module_name,
                'title': panel.title,
                'description': panel.description,
                'components': panel.components,
                'generated_at': panel.generated_at
            }, f, indent=2)

    def get_panel(self, panel_id: str) -> Optional[UIPanel]:
        """Get generated panel by ID"""
        return self.panels.get(panel_id)

    def list_panels(self) -> List[Dict]:
        """List all generated panels"""
        return [
            {
                'panel_id': p.panel_id,
                'module_name': p.module_name,
                'title': p.title,
                'generated_at': p.generated_at
            }
            for p in self.panels.values()
        ]


# Pre-configured module UI definitions
MODULE_UI_CONFIGS = {
    'blood_analyzer': {
        'title': '🩸 Blood Test Analyzer',
        'description': 'Analyze 30+ blood tests with 4-level risk detection and population-specific ranges',
        'module_id': 'blood',
        'primary_color': '#e74c3c',
        'secondary_color': '#c0392b',
        'api_endpoint': '/api/blood/analyze',
        'input_fields': [
            {'label': 'Patient ID', 'name': 'patient_id', 'type': 'text', 'placeholder': 'P001'},
            {'label': 'Glucose Fasting', 'name': 'glucose_fasting', 'type': 'number', 'min': 0, 'max': 500, 'step': 1},
            {'label': 'HbA1c', 'name': 'hba1c', 'type': 'number', 'min': 0, 'max': 20, 'step': 0.1},
            {'label': 'LDL Cholesterol', 'name': 'ldl_cholesterol', 'type': 'number', 'min': 0, 'max': 300, 'step': 1},
            {'label': 'Population', 'name': 'population', 'type': 'select', 'options': ['general', 'south_asian', 'african', 'east_asian']}
        ],
        'action_label': 'Analyze Blood Panel',
        'has_chart': True
    },
    'dna_analyzer': {
        'title': '🧬 DNA Variant Analysis',
        'description': 'Analyze genetic variants for disease risk and personalized recommendations',
        'module_id': 'dna',
        'primary_color': '#9b59b6',
        'secondary_color': '#8e44ad',
        'api_endpoint': '/api/dna/analyze',
        'input_fields': [
            {'label': 'Patient ID', 'name': 'patient_id', 'type': 'text', 'placeholder': 'P001'},
            {'label': 'APOE4', 'name': 'APOE4', 'type': 'select', 'options': ['0_copies', '1_copy', '2_copies']},
            {'label': 'MTHFR C677T', 'name': 'MTHFR_C677T', 'type': 'select', 'options': ['CC', 'CT', 'TT']},
            {'label': 'FTO', 'name': 'FTO', 'type': 'select', 'options': ['AA', 'AT', 'TT']}
        ],
        'action_label': 'Analyze DNA',
        'has_chart': False
    },
    'consanguinity': {
        'title': '👨‍👩‍👧‍👦 Consanguinity Risk',
        'description': 'Assess genetic risks for consanguineous marriages (South Asian focus)',
        'module_id': 'consanguinity',
        'primary_color': '#f39c12',
        'secondary_color': '#e67e22',
        'api_endpoint': '/api/consanguinity/analyze',
        'input_fields': [
            {'label': 'Relationship Type', 'name': 'relationship', 'type': 'select', 'options': ['first_cousin', 'double_first_cousin', 'uncle_niece', 'second_cousin', 'avuncular']},
            {'label': 'Disease to Check', 'name': 'disease', 'type': 'select', 'options': ['thalassemia', 'sickle_cell', 'cystic_fibrosis', 'all']}
        ],
        'action_label': 'Calculate Risk',
        'has_chart': True
    },
    'drug_predictor': {
        'title': '💊 Drug Response Predictor',
        'description': 'Pharmacogenomic-based drug prediction for personalized medicine',
        'module_id': 'drug',
        'primary_color': '#27ae60',
        'secondary_color': '#219a52',
        'api_endpoint': '/api/drug/predict',
        'input_fields': [
            {'label': 'Drug Name', 'name': 'drug_name', 'type': 'select', 'options': ['warfarin', 'clopidogrel', 'codeine', 'azathioprine', 'simvastatin']},
            {'label': 'CYP2D6', 'name': 'CYP2D6', 'type': 'select', 'options': ['ultrarapid', 'extensive', 'intermediate', 'poor']},
            {'label': 'CYP2C19', 'name': 'CYP2C19', 'type': 'select', 'options': ['ultrarapid', 'extensive', 'intermediate', 'poor']}
        ],
        'action_label': 'Predict Response',
        'has_chart': False
    },
    'pandemic': {
        'title': '🌍 Pandemic Risk Prediction',
        'description': 'Real-time pandemic risk assessment with mitigation strategies',
        'module_id': 'pandemic',
        'primary_color': '#e84393',
        'secondary_color': '#d63031',
        'api_endpoint': '/api/pandemic/predict',
        'input_fields': [
            {'label': 'Population Density', 'name': 'population_density', 'type': 'number', 'min': 0, 'max': 50000, 'step': 100},
            {'label': 'Mobility Index', 'name': 'mobility_index', 'type': 'number', 'min': 0, 'max': 100, 'step': 1},
            {'label': 'Healthcare Capacity', 'name': 'healthcare_capacity', 'type': 'number', 'min': 0, 'max': 100, 'step': 1},
            {'label': 'Vaccination Rate', 'name': 'vaccination_rate', 'type': 'number', 'min': 0, 'max': 100, 'step': 1}
        ],
        'action_label': 'Assess Risk',
        'has_chart': True
    },
    'ethics': {
        'title': '⚖️ Ethics Assessment',
        'description': 'Gurmat + Medical ethics review for research proposals and actions',
        'module_id': 'ethics',
        'primary_color': '#6c5ce7',
        'secondary_color': '#5f3dc4',
        'api_endpoint': '/api/ethics/check',
        'input_fields': [
            {'label': 'Action Description', 'name': 'action', 'type': 'text', 'placeholder': 'Describe the research or action...'}
        ],
        'action_label': 'Check Ethics',
        'has_chart': False
    },
    'research': {
        'title': '🔬 Autonomous Research',
        'description': 'Start AI-driven medical research with multi-agent collaboration',
        'module_id': 'research',
        'primary_color': '#0984e3',
        'secondary_color': '#0770c2',
        'api_endpoint': '/api/research/start',
        'input_fields': [
            {'label': 'Research Topic', 'name': 'topic', 'type': 'text', 'placeholder': 'e.g., diabetes mellitus type 2 genetics'},
            {'label': 'Duration (hours)', 'name': 'duration', 'type': 'number', 'min': 1, 'max': 72, 'step': 1}
        ],
        'action_label': 'Start Research',
        'has_chart': True
    }
}


def generate_all_module_panels() -> List[UIPanel]:
    """Generate UI panels for all AMRIT modules"""
    generator = AutoUIGenerator()
    panels = []

    for module_name, config in MODULE_UI_CONFIGS.items():
        panel = generator.generate_panel(module_name, config)
        panels.append(panel)
        print("Generated panel: %s" % panel.title)

    return panels
