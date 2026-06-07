#!/usr/bin/env python3

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / 'knowledgebase'
OUT = ROOT / 'outputs'

active_core_path = KB / 'active_core_library.csv'
registry_path = KB / 'material_registry.csv'

if active_core_path.exists():
    registry = pd.read_csv(active_core_path)
    source_label = 'active_core_library.csv'
else:
    registry = pd.read_csv(registry_path)
    source_label = 'material_registry.csv'

try:
    evidence = pd.read_csv(KB / 'material_evidence_registry.csv')
except Exception:
    evidence = pd.DataFrame(columns=['material','pmid','evidence_type','assay','target','evidence_strength'])

EVIDENCE_WEIGHTS = {
    'ev_preservation': 5,
    'membrane_preservation': 4,
    'vesicle_preservation': 4,
    'liposome_preservation': 4,
    'protein_stabilization': 3,
    'nucleic_acid_preservation': 3,
    'osmolyte_protection': 3,
    'biomineralization': 4,
    'diffusion_constraint': 3,
    'matrix_constraint': 3,
    'anti_aggregation': 2,
    'anti_adsorption': 2,
    'colloid_stabilization': 2,
    'cryopreservation': 2,
    'general_excipient': 1
}

STRENGTH_WEIGHTS = {
    'high': 1.0,
    'medium': 0.6,
    'low': 0.3
}

required_registry_cols = {'material','category','entropy_module','confidence','status'}
missing_registry_cols = required_registry_cols - set(registry.columns)
if missing_registry_cols:
    raise ValueError(f'{source_label} is missing required columns: {sorted(missing_registry_cols)}')

base = registry[['material','category','entropy_module','confidence','status']].copy()
base = base.drop_duplicates(subset=['material'])

confidence_map = {'high':10,'medium':7,'low':4}
base['confidence_score'] = base['confidence'].astype(str).str.lower().map(confidence_map).fillna(5)

if len(evidence):
    evidence = evidence.copy()
    evidence = evidence[evidence['material'].isin(base['material'])]
    evidence['base_evidence_weight'] = evidence['evidence_type'].astype(str).str.lower().map(EVIDENCE_WEIGHTS).fillna(1)
    evidence['strength_weight'] = evidence['evidence_strength'].astype(str).str.lower().map(STRENGTH_WEIGHTS).fillna(0.5)
    evidence['weighted_evidence'] = evidence['base_evidence_weight'] * evidence['strength_weight']

    summary = evidence.groupby('material').agg(
        evidence_count=('material','size'),
        pmid_count=('pmid','nunique'),
        mechanism_diversity=('evidence_type','nunique'),
        assay_diversity=('assay','nunique'),
        target_diversity=('target','nunique'),
        weighted_evidence_score=('weighted_evidence','sum')
    ).reset_index()
else:
    summary = pd.DataFrame(columns=['material','evidence_count','pmid_count','mechanism_diversity','assay_diversity','target_diversity','weighted_evidence_score'])

scores = base.merge(summary,on='material',how='left')

for col in ['evidence_count','pmid_count','mechanism_diversity','assay_diversity','target_diversity','weighted_evidence_score']:
    scores[col] = scores[col].fillna(0)

module_bonus = {'structural':2.0,'interface':1.5,'constraint':1.5}
scores['module_bonus'] = scores['entropy_module'].astype(str).str.lower().map(module_bonus).fillna(1)

scores['evidence_score'] = (
    scores['weighted_evidence_score'] +
    0.5*scores['mechanism_diversity'] +
    0.3*scores['assay_diversity'] +
    0.2*scores['target_diversity']
).clip(upper=20)

scores['overall_score'] = (
    0.35*scores['confidence_score'] +
    0.45*scores['evidence_score'] +
    0.10*scores['mechanism_diversity'] +
    0.10*scores['module_bonus']
).round(2)

scores = scores.sort_values('overall_score', ascending=False)

OUT.mkdir(exist_ok=True)
scores.to_csv(OUT / 'material_scores.csv', index=False)
scores.to_csv(KB / 'material_scores.csv', index=False)

print(f'Generated {len(scores)} material scores from {source_label}')
print('Output: outputs/material_scores.csv')
print('Output: knowledgebase/material_scores.csv')
