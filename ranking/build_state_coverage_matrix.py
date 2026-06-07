#!/usr/bin/env python3

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / 'knowledgebase'

scores = pd.read_csv(KB / 'material_scores.csv')

required = {
    'material',
    'category',
    'entropy_module',
    'confidence_score',
    'evidence_score'
}
missing = required - set(scores.columns)
if missing:
    raise ValueError(f'material_scores.csv is missing required columns: {sorted(missing)}')

merged = scores.copy()


def mechanism_class(row):
    module = str(row.get('entropy_module','')).lower()
    if module == 'structural':
        return 'Structural_Stabilization'
    if module == 'constraint':
        return 'Physical_Encapsulation'
    return 'Chemical_Stabilization'


def score_from_module(row, axis):
    module = str(row.get('entropy_module','')).lower()
    evidence = float(row.get('evidence_score',0))
    confidence = float(row.get('confidence_score',5))

    base = 3 + 0.35*evidence + 0.15*confidence

    if module == 'structural':
        if axis == 'membrane':
            base += 1.0
        elif axis == 'protein':
            base += 1.0
        elif axis == 'nucleic_acid':
            base += 0.5

    elif module == 'interface':
        if axis == 'membrane':
            base += 1.0
        elif axis == 'protein':
            base += 0.5

    elif module == 'constraint':
        base += 1.0

    return max(1, min(10, round(base,2)))


def assay_risk(row):
    module = str(row.get('entropy_module','')).lower()
    category = str(row.get('category','')).lower()

    risk = 0.04

    if module == 'constraint':
        risk += 0.04

    if category in {'surfactant','polymer','hydrogel','mineral'}:
        risk += 0.03

    if category in {'chelator','preservative'}:
        risk += 0.04

    return round(min(risk,0.20),3)


out = pd.DataFrame()
out['material'] = merged['material']
out['mechanism_class'] = merged.apply(mechanism_class, axis=1)
out['membrane_score'] = merged.apply(lambda r: score_from_module(r,'membrane'), axis=1)
out['protein_score'] = merged.apply(lambda r: score_from_module(r,'protein'), axis=1)
out['nucleic_acid_score'] = merged.apply(lambda r: score_from_module(r,'nucleic_acid'), axis=1)
out['assay_risk'] = merged.apply(assay_risk, axis=1)
out['notes'] = (
    'auto_generated_from_material_scores; evidence_score=' +
    merged['evidence_score'].fillna(0).astype(str) +
    '; module=' + merged['entropy_module'].fillna('unknown').astype(str)
)

out = out.drop_duplicates(subset=['material']).sort_values(['mechanism_class','material'])
out.to_csv(KB / 'state_coverage_matrix.csv', index=False)

print(f'Generated state coverage matrix for {len(out)} materials')
print('Output: knowledgebase/state_coverage_matrix.csv')
print(out.groupby('mechanism_class').size())
