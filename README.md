# Integrated Biostasis Chemistry

**Integrated Biostasis Chemistry (IBC)** is a minimal, state-driven framework for discovering chemical environments that preserve biological-state information over time.

IBC focuses on three state layers:

1. **Membrane state** — structure and compartment integrity
2. **Protein state** — functional and enzymatic activity
3. **Nucleic-acid state** — amplifiable genetic information

The core idea is:

```text
Material
  ↓
Entropy-control mechanism
  ↓
State coverage
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
| Chemical Stabilization | Suppress irreversible chemical damage | Trolox, glutathione, catalase, EDTA |
| Physical Encapsulation | Restrict accessibility and configurational freedom | silica, calcium phosphate, hydrogel |

## Repository structure

```text
.github/workflows/generate_formulations.yml   GitHub Action to generate ranked formulations
knowledgebase/state_coverage_matrix.csv       Prior material-to-state coverage matrix
ranking/generate_formulations.py              State-driven formulation generator
validation/experimental_results_template.csv  Template for experimental feedback
```

## How to run

### On GitHub

Go to **Actions → Generate IBC Formulations → Run workflow**.

The workflow generates:

```text
outputs/top48_formulations.csv
```

### Locally

```bash
pip install pandas numpy
python ranking/generate_formulations.py --top 48 --output outputs/top48_formulations.csv
```

## Current status

This is a clean v0.1 scaffold. The state coverage scores are prior assumptions, not final experimental values. They should be updated after membrane, protein, and nucleic-acid preservation experiments.
