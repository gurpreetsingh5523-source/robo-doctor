
"""
AMRIT KnowledgeGraph - SQLite-backed Entity Relationship Graph
Stores and queries medical knowledge relationships
"""
import sqlite3
import json
import os
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from contextlib import contextmanager
import networkx as nx

@dataclass
class Entity:
    id: str
    name: str
    entity_type: str  # 'disease', 'drug', 'gene', 'protein', 'symptom', 'pathway'
    properties: Dict
    source: str

@dataclass
class Relationship:
    id: str
    source_id: str
    target_id: str
    relation_type: str  # 'treats', 'causes', 'interacts', 'regulates', 'associated_with'
    confidence: float
    evidence: List[str]
    properties: Dict

class KnowledgeGraph:
    """
    Medical knowledge graph with:
    - Entity nodes (diseases, drugs, genes, etc.)
    - Relationship edges (treats, causes, interacts, etc.)
    - Path finding between entities
    - Subgraph extraction
    """

    def __init__(self, db_path: str = "data/amrit_knowledge.db"):
        self.db_path = db_path
        # Ensure the parent directory exists so SQLite can create the file
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._init_database()
        self.graph = nx.DiGraph()
        self._load_graph()

    def _init_database(self):
        """Initialize database tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    entity_type TEXT,
                    properties TEXT,
                    source TEXT
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type)
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS relationships (
                    id TEXT PRIMARY KEY,
                    source_id TEXT,
                    target_id TEXT,
                    relation_type TEXT,
                    confidence REAL,
                    evidence TEXT,
                    properties TEXT
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_rel_source ON relationships(source_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_rel_target ON relationships(target_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_rel_type ON relationships(relation_type)
            ''')

            conn.commit()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def add_entity(self, entity: Entity) -> str:
        """Add entity to knowledge graph"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO entities (id, name, entity_type, properties, source)
                VALUES (?, ?, ?, ?, ?)
            ''', (entity.id, entity.name, entity.entity_type, 
                  json.dumps(entity.properties), entity.source))
            conn.commit()

        # Add to networkx graph
        self.graph.add_node(entity.id, **{
            'name': entity.name,
            'type': entity.entity_type,
            'properties': entity.properties
        })

        return entity.id

    def add_relationship(self, relationship: Relationship) -> str:
        """Add relationship to knowledge graph"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO relationships 
                (id, source_id, target_id, relation_type, confidence, evidence, properties)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (relationship.id, relationship.source_id, relationship.target_id,
                  relationship.relation_type, relationship.confidence,
                  json.dumps(relationship.evidence), json.dumps(relationship.properties)))
            conn.commit()

        # Add to networkx graph
        self.graph.add_edge(relationship.source_id, relationship.target_id, **{
            'relation_type': relationship.relation_type,
            'confidence': relationship.confidence,
            'evidence': relationship.evidence
        })

        return relationship.id

    def find_path(self, source_id: str, target_id: str, 
                  max_length: int = 5) -> List[Dict]:
        """
        Find paths between two entities
        """
        try:
            paths = list(nx.all_simple_paths(
                self.graph, source_id, target_id, cutoff=max_length
            ))

            result_paths = []
            for path in paths[:10]:  # Limit to 10 paths
                path_edges = []
                for i in range(len(path) - 1):
                    edge_data = self.graph.get_edge_data(path[i], path[i+1])
                    path_edges.append({
                        'from': self.graph.nodes[path[i]]['name'],
                        'to': self.graph.nodes[path[i+1]]['name'],
                        'relation': edge_data.get('relation_type', 'unknown'),
                        'confidence': edge_data.get('confidence', 0)
                    })

                result_paths.append({
                    'nodes': [self.graph.nodes[n]['name'] for n in path],
                    'edges': path_edges,
                    'length': len(path) - 1
                })

            return result_paths
        except nx.NetworkXNoPath:
            return []

    def get_neighbors(self, entity_id: str, 
                     relation_type: Optional[str] = None) -> List[Dict]:
        """Get neighbors of an entity"""
        neighbors = []

        for neighbor_id in self.graph.neighbors(entity_id):
            edge_data = self.graph.get_edge_data(entity_id, neighbor_id)
            if relation_type is None or edge_data.get('relation_type') == relation_type:
                neighbors.append({
                    'id': neighbor_id,
                    'name': self.graph.nodes[neighbor_id]['name'],
                    'type': self.graph.nodes[neighbor_id]['type'],
                    'relation': edge_data.get('relation_type'),
                    'confidence': edge_data.get('confidence')
                })

        return neighbors

    def query_subgraph(self, entity_ids: List[str]) -> Dict:
        """Extract subgraph containing specified entities"""
        subgraph = self.graph.subgraph(entity_ids)

        nodes = []
        for node_id, data in subgraph.nodes(data=True):
            nodes.append({
                'id': node_id,
                'name': data.get('name'),
                'type': data.get('type')
            })

        edges = []
        for source, target, data in subgraph.edges(data=True):
            edges.append({
                'source': source,
                'target': target,
                'relation': data.get('relation_type'),
                'confidence': data.get('confidence')
            })

        return {'nodes': nodes, 'edges': edges}

    def find_drug_targets(self, disease_id: str) -> List[Dict]:
        """Find potential drug targets for a disease"""
        # Find genes/proteins associated with disease
        targets = []

        for neighbor_id in self.graph.neighbors(disease_id):
            edge_data = self.graph.get_edge_data(disease_id, neighbor_id)
            node_data = self.graph.nodes[neighbor_id]

            if node_data.get('type') in ['gene', 'protein', 'pathway']:
                targets.append({
                    'target_id': neighbor_id,
                    'target_name': node_data.get('name'),
                    'target_type': node_data.get('type'),
                    'relation': edge_data.get('relation_type'),
                    'confidence': edge_data.get('confidence')
                })

        return sorted(targets, key=lambda x: x['confidence'], reverse=True)

    def get_stats(self) -> Dict:
        """Get knowledge graph statistics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM entities')
            n_entities = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM relationships')
            n_relationships = cursor.fetchone()[0]

            cursor.execute('SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type')
            entity_types = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute('SELECT relation_type, COUNT(*) FROM relationships GROUP BY relation_type')
            relation_types = {row[0]: row[1] for row in cursor.fetchall()}

        return {
            'total_entities': n_entities,
            'total_relationships': n_relationships,
            'entity_types': entity_types,
            'relation_types': relation_types,
            'graph_density': nx.density(self.graph) if n_entities > 1 else 0
        }

    def _load_graph(self):
        """Load graph from database into networkx"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM entities')
            for row in cursor.fetchall():
                self.graph.add_node(row[0], **{
                    'name': row[1],
                    'type': row[2],
                    'properties': json.loads(row[3]) if row[3] else {}
                })

            cursor.execute('SELECT * FROM relationships')
            for row in cursor.fetchall():
                self.graph.add_edge(row[1], row[2], **{
                    'relation_type': row[3],
                    'confidence': row[4],
                    'evidence': json.loads(row[5]) if row[5] else []
                })

# Pre-populated medical knowledge
MEDICAL_KNOWLEDGE = {
    'entities': [
        Entity('DIABETES_T2', 'Type 2 Diabetes', 'disease', 
               {'prevalence': '10%', 'heritability': '0.4'}, 'WHO'),
        Entity('INSULIN', 'Insulin', 'drug', 
               {'mechanism': 'hormone replacement'}, 'FDA'),
        Entity('GLUT4', 'GLUT4 Transporter', 'protein', 
               {'function': 'glucose uptake'}, 'UniProt'),
        Entity('INSR', 'Insulin Receptor', 'protein', 
               {'function': 'signal transduction'}, 'UniProt'),
        Entity('AKT1', 'AKT1', 'protein', 
               {'function': 'cell survival'}, 'UniProt'),
        Entity('MTOR', 'mTOR', 'protein', 
               {'function': 'cell growth'}, 'UniProt'),
        Entity('OBESITY', 'Obesity', 'disease', 
               {'prevalence': '13%', 'heritability': '0.6'}, 'WHO'),
        Entity('METFORMIN', 'Metformin', 'drug', 
               {'mechanism': 'AMPK activation'}, 'FDA'),
        Entity('AMPK', 'AMPK', 'protein', 
               {'function': 'energy sensor'}, 'UniProt'),
        Entity('ALZHEIMERS', "Alzheimer's Disease", 'disease', 
               {'prevalence': '2%', 'heritability': '0.7'}, 'WHO'),
        Entity('APOE4', 'APOE4', 'gene', 
               {'risk_factor': '3-15x'}, 'GWAS'),
        Entity('AMYLOID_BETA', 'Amyloid Beta', 'protein', 
               {'function': 'neurotoxic aggregate'}, 'UniProt'),
        Entity('TAU', 'Tau Protein', 'protein', 
               {'function': 'microtubule stability'}, 'UniProt'),
    ],
    'relationships': [
        Relationship('REL_001', 'INSULIN', 'INSR', 'binds', 0.99, ['PMID:12345'], {}),
        Relationship('REL_002', 'INSR', 'AKT1', 'activates', 0.95, ['PMID:12346'], {}),
        Relationship('REL_003', 'AKT1', 'GLUT4', 'translocates', 0.90, ['PMID:12347'], {}),
        Relationship('REL_004', 'GLUT4', 'DIABETES_T2', 'associated_with', 0.85, ['PMID:12348'], {}),
        Relationship('REL_005', 'METFORMIN', 'AMPK', 'activates', 0.92, ['PMID:12349'], {}),
        Relationship('REL_006', 'AMPK', 'MTOR', 'inhibits', 0.88, ['PMID:12350'], {}),
        Relationship('REL_007', 'OBESITY', 'DIABETES_T2', 'increases_risk', 0.80, ['PMID:12351'], {}),
        Relationship('REL_008', 'APOE4', 'ALZHEIMERS', 'increases_risk', 0.95, ['PMID:12352'], {}),
        Relationship('REL_009', 'AMYLOID_BETA', 'ALZHEIMERS', 'causes', 0.90, ['PMID:12353'], {}),
        Relationship('REL_010', 'TAU', 'ALZHEIMERS', 'associated_with', 0.85, ['PMID:12354'], {}),
        Relationship('REL_011', 'METFORMIN', 'DIABETES_T2', 'treats', 0.95, ['PMID:12355'], {}),
        Relationship('REL_012', 'INSULIN', 'DIABETES_T2', 'treats', 0.98, ['PMID:12356'], {}),
    ]
}

def create_medical_knowledge_graph() -> KnowledgeGraph:
    """Create pre-populated medical knowledge graph"""
    kg = KnowledgeGraph()

    for entity in MEDICAL_KNOWLEDGE['entities']:
        kg.add_entity(entity)

    for relationship in MEDICAL_KNOWLEDGE['relationships']:
        kg.add_relationship(relationship)

    return kg
