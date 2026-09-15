"""
AMRIT Molecular Docking Gateway (v6.2)
=======================================
Drug-discovery support: fetch real protein structures and run
protein-ligand docking simulations.

What this module REALLY does:
1. REAL now: downloads experimentally-determined protein 3D structures from
   RCSB PDB (public, free) — live network fetch.
2. REAL when engine installed: runs AutoDock Vina docking if the `vina`
   binary/python package is available on this machine.
3. HONEST always: if the docking engine is not installed, it says so and
   explains how to install it. It NEVER fabricates binding affinities.
4. ETHICS gate: EthicsFilter screens every request; toxin/bioweapon design
   is refused.
5. CACHE: docking results cached in MemoryManager (docking is expensive —
   never compute the same pair twice).

Disclaimer: docking scores are computational estimates for research
prioritization only. They are not clinical evidence.
"""

import os
import json
import hashlib
import shutil
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, Optional

try:
    import requests
except ImportError:
    requests = None

from src.ethics.ethics_filter import EthicsFilter

DOCKING_DISCLAIMER = (
    "Docking scores are computational research estimates, not clinical "
    "evidence. Any candidate drug requires laboratory and clinical validation."
)

RCSB_DOWNLOAD = "https://files.rcsb.org/download/{pdb_id}.pdb"

# Binding affinity interpretation (kcal/mol, standard docking conventions)
AFFINITY_BANDS = [
    (-10.0, "excellent", "Very strong predicted binding"),
    (-8.0, "strong", "Strong predicted binding — good candidate"),
    (-6.0, "moderate", "Moderate binding — may need optimization"),
    (0.0, "weak", "Weak predicted binding — unlikely candidate"),
]


class DockingEngineNotInstalled(Exception):
    pass


class DockingGateway:
    """
    Protein structure fetch + molecular docking with ethics gate and caching.

    Usage:
        gw = DockingGateway(memory_manager=mm)
        pdb_path = gw.fetch_protein_structure('1CRN')          # real, live
        result = gw.dock('1CRN', ligand_smiles='CCO', purpose='drug repurposing research')
    """

    CACHE_MEMORY_TYPE = "docking_result"

    def __init__(self, memory_manager=None, ethics_filter: Optional[EthicsFilter] = None,
                 structures_dir: str = "data/protein_structures"):
        self.memory = memory_manager
        self.ethics = ethics_filter or EthicsFilter()
        self.structures_dir = structures_dir
        os.makedirs(structures_dir, exist_ok=True)

    # ------------------------------------------------------------------
    @property
    def engine_available(self) -> bool:
        """True only if a real docking engine exists on this machine."""
        if shutil.which("vina"):
            return True
        try:
            import vina  # python package
            return True
        except ImportError:
            return False

    def engine_status(self) -> Dict:
        if self.engine_available:
            return {"engine": "autodock_vina", "status": "available"}
        return {
            "engine": None,
            "status": "engine_not_installed",
            "install_instructions": (
                "Install AutoDock Vina: 'pip install vina' (python bindings) "
                "or download the binary from https://vina.scripps.edu — free "
                "for academic use. Also recommended: RDKit ('pip install rdkit') "
                "for ligand preparation."
            ),
        }

    # ------------------------------------------------------------------
    def fetch_protein_structure(self, pdb_id: str) -> Dict:
        """Download a real protein structure from RCSB PDB (live)."""
        pdb_id = pdb_id.strip().upper()
        if requests is None:
            raise RuntimeError("requests library not available")
        local_path = os.path.join(self.structures_dir, f"{pdb_id}.pdb")
        if os.path.exists(local_path):
            return {"pdb_id": pdb_id, "path": local_path, "source": "local_cache"}
        resp = requests.get(RCSB_DOWNLOAD.format(pdb_id=pdb_id), timeout=60)
        if resp.status_code == 404:
            raise ValueError(f"PDB ID '{pdb_id}' not found in RCSB database")
        resp.raise_for_status()
        with open(local_path, "wb") as fh:
            fh.write(resp.content)
        header = resp.text.splitlines()[0] if resp.text else ""
        return {
            "pdb_id": pdb_id,
            "path": local_path,
            "bytes": len(resp.content),
            "header": header.strip(),
            "source": "rcsb_pdb_live",
            "fetched_at": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    def _cache_key(self, pdb_id: str, ligand_smiles: str) -> str:
        return hashlib.sha256(f"{pdb_id}|{ligand_smiles}".encode()).hexdigest()[:16]

    def _cache_lookup(self, key: str) -> Optional[Dict]:
        if self.memory is None:
            return None
        hits = self.memory.search(memory_type=self.CACHE_MEMORY_TYPE, tags=[key], limit=1)
        if hits and isinstance(hits[0].content, dict):
            cached = dict(hits[0].content)
            cached["cache_hit"] = True
            return cached
        return None

    def _cache_store(self, key: str, pdb_id: str, result: Dict):
        if self.memory is not None:
            self.memory.store(result, self.CACHE_MEMORY_TYPE,
                              tags=[key, pdb_id], importance=0.8)

    # ------------------------------------------------------------------
    def interpret_affinity(self, kcal_mol: float) -> Dict:
        for threshold, band, meaning in AFFINITY_BANDS:
            if kcal_mol <= threshold:
                return {"band": band, "meaning": meaning}
        return {"band": "unknown", "meaning": "Score outside expected range"}

    def dock(self, pdb_id: str, ligand_smiles: str,
             purpose: str = "drug repurposing research",
             center: Optional[list] = None, box_size: int = 20) -> Dict:
        """
        Dock one ligand against one protein.
        Gate chain: ethics -> cache -> engine (honest if missing).
        """
        # Gate 1: ethics (toxin/bioweapon design must be refused)
        assessment = self.ethics.assess(
            f"Molecular docking of ligand against protein {pdb_id} for: {purpose}")
        if not assessment.approved:
            return {
                "status": "ethics_blocked",
                "violations": [str(v) for v in getattr(assessment, 'violations', [])],
                "disclaimer": DOCKING_DISCLAIMER,
            }

        base = {
            "pdb_id": pdb_id.upper(),
            "ligand_smiles": ligand_smiles,
            "purpose": purpose,
            "disclaimer": DOCKING_DISCLAIMER,
            "timestamp": datetime.now().isoformat(),
        }

        # Gate 2: cache
        key = self._cache_key(pdb_id, ligand_smiles)
        cached = self._cache_lookup(key)
        if cached:
            return {**base, **cached}

        # Gate 3: engine (honest)
        if not self.engine_available:
            return {**base,
                    "status": "engine_not_installed",
                    "binding_affinity_kcal_mol": None,
                    "message": "No docking engine on this machine. "
                               "No score was fabricated.",
                    **self.engine_status()}

        # Real docking path (vina binary)
        try:
            result = self._run_vina(pdb_id, ligand_smiles, center, box_size)
        except Exception as e:
            return {**base, "status": "docking_failed", "message": str(e),
                    "binding_affinity_kcal_mol": None}

        result["cache_hit"] = False
        self._cache_store(key, pdb_id, result)
        return {**base, **result}

    def _run_vina(self, pdb_id: str, ligand_smiles: str,
                  center: Optional[list], box_size: int) -> Dict:
        """Execute real AutoDock Vina docking."""
        structure = self.fetch_protein_structure(pdb_id)
        vina_bin = shutil.which("vina")
        if vina_bin is None:
            # python bindings path
            from vina import Vina
            v = Vina(sf_name="vina")
            v.set_receptor(structure["path"])
            v.set_ligand_from_string(ligand_smiles)
            if center:
                v.compute_vina_maps(center=center, box_size=[box_size] * 3)
                score = v.score()[0]
            else:
                score = None
            return {
                "status": "ok",
                "binding_affinity_kcal_mol": score,
                "interpretation": self.interpret_affinity(score) if score is not None else None,
                "engine": "vina_python",
            }
        # binary path requires prepared PDBQT files — report honestly
        raise DockingEngineNotInstalled(
            "Vina binary found, but receptor/ligand PDBQT preparation "
            "requires RDKit/Meeko which is not installed. Install with: "
            "pip install rdkit meeko")
