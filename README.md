# Integrated Biostasis Chemistry

**Integrated Biostasis Chemistry (IBC)** is a minimal, evidence-driven framework for discovering chemical environments that preserve biological-state information over time.

IBC focuses on three state layers:

1. **Membrane state** — structure and compartment integrity
2. **Protein state** — functional and enzymatic activity
3. **Nucleic-acid state** — amplifiable genetic information

The core idea is:

```text
Literature search / evidence registry
  ↓
Candidate material universe
  ↓
Core material state matrix (~50 materials)
  ↓
Predicted Temporal Fidelity Index
  ↓
Experimental validation
  ↓
Updated next-generation design
```

## Preservation mechanism classes

IBC currently uses three broad preservation mechanism classes:

| Class | Purpose | Examples |
|---|---|---|
| Structural Stabilization | Reduce molecular mobility, interfacial damage, and structural disorder | trehalose, ectoine, PEG, dextran, glycerol |
| Chemical Protection | Suppress irreversible chemical damage | Trolox, glutathione, methionine, chelators |
| Physical Encapsulation | Restrict accessibility, diffusion, and configurational freedom | silicic acid, calcium phosphate, alginate, agarose |

## Repository structure

```text
.github/workflows/generate_formulations.yml       GitHub Action to sync evidence and generate ranked formulations
knowledgebase/candidate_universe.csv              Literature-derived candidate material universe
knowledgebase/core_material_state_matrix.csv      Filtered core material set with membrane/protein/NA scores
knowledgebase/material_evidence_registry.csv      PMID/DOI-level evidence registry scaffold
knowledgebase/material_aliases.csv                Alias normalization table, e.g. TMOS/TEOS/silica -> Silicic_Acid
scripts/sync_state_evidence.py                    Connects evidence tables to the core state matrix
ranking/generate_formulations.py                  State-driven formulation generator
validation/experimental_results_template.csv      Template for experimental feedback
archive/legacy_tables/                            Retired intermediate tables kept for traceability
```

## Evidence-linked workflow

The design pipeline separates evidence collection, core-material selection, formulation scoring, and experimental feedback:

```text
knowledgebase/material_evidence_registry.csv
knowledgebase/candidate_universe.csv
        ↓
scripts/sync_state_evidence.py
        ↓
outputs/core_material_state_matrix_evidence_synced.csv
        ↓
ranking/generate_formulations.py
        ↓
outputs/top48_formulations.csv
        ↓
validation/experimental_results_template.csv
```

The synchronized core matrix keeps the original membrane/protein/nucleic-acid prior scores, but fills evidence metadata including:

```text
evidence_count
confidence
evidence_status
evidence_sources
registry_evidence_types
registry_assays
registry_targets
```

## How to run

### On GitHub

Go to **Actions → Generate IBC Formulations → Run workflow**.

The workflow generates two downloadable artifacts:

```text
outputs/core_material_state_matrix_evidence_synced.csv
outputs/top48_formulations.csv
```

### Locally

```bash
pip install pandas numpy
python scripts/sync_state_evidence.py --output outputs/core_material_state_matrix_evidence_synced.csv
cp outputs/core_material_state_matrix_evidence_synced.csv knowledgebase/core_material_state_matrix.csv
python ranking/generate_formulations.py --top 48 --output outputs/top48_formulations.csv
```

## Current status

This is a v0.2 evidence-linked scaffold. The state coverage scores are still literature-derived priors rather than final experimental values. The current workflow is designed to support the first experimental cycle: literature search -> candidate universe -> filtered core material matrix -> 48 stratified formulations -> membrane/protein/nucleic-acid validation.

The next major improvement should be completing `knowledgebase/material_evidence_registry.csv` with PMID/DOI-level evidence from systematic literature review, then using experimental results to update the prior scores in `knowledgebase/core_material_state_matrix.csv`.
