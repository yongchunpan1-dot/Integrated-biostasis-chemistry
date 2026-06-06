#!/usr/bin/env python3

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / 'knowledgebase'
OUT = ROOT / 'outputs'

registry = pd.read_csv(KB / 'material_registry.csv')
evidence = pd.read_csv(KB / 'descriptor_evidence.csv')

try:
    lit = pd.read_csv(KB / 'material_evidence_registry.csv')
except Exception:
    lit = pd.DataFrame(columns=['material'])

pmid_counts = lit.groupby('material').size().reset_index(name='pmid_count')
EVIDENCE_WEIGHTS = {
    'ev_preservation': 5,
    'vesicle_preservation': 4,
    'liposome_preservation': 4,
    'membrane_preservation': 4,
    'protein_stabilization': 3,
    'nucleic_acid_preservation': 3,
    'osmolyte_protection': 3,
    'anti_aggregation': 2,
    'anti_adsorption': 2,
    'cryopreservation': 2,
    'biomineralization': 4,
    'diffusion_constraint': 3,
    'matrix_constraint': 3,
    'colloid_stabilization': 2
}

if len(lit):
    lit['evidence_weight'] = (
        lit['evidence_type']
        .astype(str)
        .map(EVIDENCE_WEIGHTS)
        .fillna(1)
    )

    weighted_evidence = (
        lit.groupby('material')['evidence_weight']
        .sum()
        .reset_index(name='weighted_evidence_score')
    )
else:
    weighted_evidence = pd.DataFrame(
        columns=['material','weighted_evidence_score']
    )

scores = registry[['material','category','entropy_module','confidence','status']].copy()

confidence_map = {'high':10,'medium':7,'low':4}
scores['confidence_score'] = scores['confidence'].astype(str).str.lower().map(confidence_map).fillna(5)

mechanism_counts = evidence.groupby('material').size().reset_index(name='mechanism_count')
scores = scores.merge(mechanism_counts,on='material',how='left')
scores = scores.merge(pmid_counts,on='material',how='left')
scores = scores.merge(weighted_evidence,on='material',how='left')

scores['mechanism_count'] = scores['mechanism_count'].fillna(0)
scores['pmid_count'] = scores['pmid_count'].fillna(0)

scores['weighted_evidence_score'] = (
    scores['weighted_evidence_score']
    .fillna(0)
)

scores['evidence_score'] = (
    scores['weighted_evidence_score']
).clip(upper=20)

module_bonus = {'structural':2.0,'interface':1.5,'constraint':1.5}
scores['module_bonus'] = scores['entropy_module'].astype(str).str.lower().map(module_bonus).fillna(1)

scores['overall_score'] = (
    0.40*scores['confidence_score'] +
    0.40*scores['evidence_score'] +
    0.10*scores['mechanism_count'] +
    0.10*scores['module_bonus']
).round(2)

scores = scores.sort_values('overall_score', ascending=False)

OUT.mkdir(exist_ok=True)
scores.to_csv(OUT / 'material_scores.csv', index=False)

print(f'Generated {len(scores)} material scores')
print('Output: outputs/material_scores.csv')
