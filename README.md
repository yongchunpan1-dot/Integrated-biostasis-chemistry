# Integrated Biostasis Chemistry

**Integrated Biostasis Chemistry (IBC)** is a minimal, state-driven framework for discovering chemical environments that preserve biological-state information over time.

IBC focuses on three state layers:

1. **Membrane state** — structure and compartment integrity
2. **Protein state** — functional and enzymatic activity
3. **Nucleic-acid state** — amplifiable genetic information

The core idea is:

```text
Literature / evidence sources
  ↓
Candidate material universe
  ↓
State coverage matrix
  ↓
Predicted Temporal Fidelity Index
  ↓
Experimental validation
  ↓
Updated next-generation design
```

## Entropy-control mechanism classes

IBC currently uses three broad preservation mechanism classes:

| Class | Purpose | Examples |
|---|---|---|
| Structural Stabilization | Reduce molecular mobility and structural disorder | trehalose, dextran, PEG, glycerol |
| Chemical Stabilization | Suppress irreversible chemical damage | Trolox, glutathione, EDTA |
| Physical Encapsulation | Restrict accessibility and configurational freedom | silicic acid, calcium phosphate, hydrogel |

## Repository structure

```text
.github/workflows/generate_formulations.yml   GitHub Action to sync evidence and generate ranked formulations
knowledgebase/candidate_universe.csv          Literature-derived candidate material universe
knowledgebase/literature_materials.csv        Literature-supported material summary
knowledgebase/material_evidence_registry.csv  PMID/DOI evidence registry scaffold
knowledgebase/state_coverage_matrix.csv       Material-to-state coverage scoring matrix
scripts/sync_state_evidence.py                Connects evidence tables to the state matrix
ranking/generate_formulations.py              State-driven formulation generator
validation/experimental_results_template.csv  Template for experimental feedback
```

## Evidence-linked workflow

The design pipeline now separates evidence collection from formulation scoring:

```text
candidate_universe.csv
literature_materials.csv
material_evidence_registry.csv
        ↓
scripts/sync_state_evidence.py
        ↓
outputs/state_coverage_matrix_evidence_synced.csv
        ↓
ranking/generate_formulations.py
        ↓
outputs/top48_formulations.csv
```

The synchronized state matrix keeps the original membrane/protein/nucleic-acid scores, but fills evidence metadata including:

```text
evidence_count
confidence
evidence_status
evidence_sources
literature_domains
registry_evidence_types
```

## How to run

### On GitHub

Go to **Actions → Generate IBC Formulations → Run workflow**.

The workflow generates:

```text
outputs/state_coverage_matrix_evidence_synced.csv
outputs/top48_formulations.csv
```

### Locally

```bash
pip install pandas numpy
python scripts/sync_state_evidence.py --output outputs/state_coverage_matrix_evidence_synced.csv
cp outputs/state_coverage_matrix_evidence_synced.csv knowledgebase/state_coverage_matrix.csv
python ranking/generate_formulations.py --top 48 --output outputs/top48_formulations.csv
```

## Current status

This is a v0.1 evidence-linked scaffold. The state coverage scores are still prior assumptions, not final experimental values. Evidence fields currently summarize internal literature-support tables and registry scaffolds; PMID/DOI-level evidence should be completed in `knowledgebase/material_evidence_registry.csv` after systematic review.
