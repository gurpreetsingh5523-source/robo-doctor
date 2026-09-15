# Contributing to Robo Doctor

🕉️ **ਸਰਬੱਤ ਦਾ ਭਲਾ — Welfare of All Humanity**

Thank you for considering seva through code. Robo Doctor exists so that
people who cannot afford a hospital still get a first line of care.

## Ground rules (non-negotiable)

1. **The doctor-approval gate must never be weakened.** No PR that lets a
   prescription bypass physician review will ever be merged.
2. **No fabricated medical output.** If a capability (LLM, docking engine,
   API) is unavailable, the system must say so — never invent a value.
3. **Ethics filter stays on.** All contributions pass `EthicsFilter`.
   Eugenics, discrimination, consent bypass, or bioweapon-adjacent features
   are rejected.
4. **Patient privacy.** Never commit patient data, `.db` files, or API keys.

## Dev setup (5 minutes)

```bash
git clone https://github.com/gurpreetsingh5523-source/robo-doctor.git
cd robo-doctor
pip install -r requirements.txt
python -m unittest discover -s tests   # all tests must pass
python -m src.dashboard.dashboard      # http://localhost:8000
```

## Where to help

| Area | Good first tasks |
|---|---|
| `src/medical/symptom_analyzer.py` | Add symptoms + test mappings (cite a clinical source) |
| `src/medical/prescription_workflow.py` | Expand drug knowledge base, interaction rules |
| `src/medical/alphagenome_client.py` | Wire the real AlphaGenome Atlas API |
| `src/medical/docking_gateway.py` | RDKit/Meeko ligand preparation pipeline |
| `src/core/data_collector.py` | More literature sources, better dedup |
| Voice | Punjabi/Hindi STT integration (Qwen/Whisper) |
| Dashboard UI | Friendly web front-end for clinics |

## Pull request process

1. Fork, branch from `main`: `git checkout -b feature/my-change`
2. Add tests for every new module (see `tests/test_all_modules.py`)
3. `python -m unittest discover -s tests` must be 100% green
4. Describe *what you verified live*, not just what you wrote
5. One logical change per PR

## Code of conduct

Seva spirit: serve without ego (hankaar), assume good faith, be honest about
limitations. Unethical use discussions are closed, not debated.
