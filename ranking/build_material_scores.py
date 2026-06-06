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

scores = registry[['material','category','entropy_module','confidence','status']].copy()

confidence_map = {'high':10,'medium':7,'low':4}
scores['confidence_score'] = scores['confidence'].astype(str).str.lower().map(confidence_map).fillna(5)

mechanism_counts = evidence.groupby('material').size().reset_index(name='mechanism_count')
scores = scores.merge(mechanism_counts,on='material',how='left')
scores = scores.merge(pmid_counts,on='material',how='left')

scores['mechanism_count'] = scores['mechanism_count'].fillna(0)
scores['pmid_count'] = scores['pmid_count'].fillna(0)

scores['evidence_score'] = (scores['mechanism_count']*2 + scores['pmid_count']).clip(upper=10)

module_bonus = {'structural':2.0,'interface':1.5,'constraint':1.5}
scores['module_bonus'] = scores['entropy_module'].astype(str).str.lower().map(module_bonus).fillna(1)

scores['overall_score'] = (
    0.45*scores['confidence_score'] +
    0.35*scores['evidence_score'] +
    0.20*scores['module_bonus']
).round(2)

scores = scores.sort_values('overall_score', ascending=False)

OUT.mkdir(exist_ok=True)
scores.to_csv(OUT / 'material_scores.csv', index=False)

print(f'Generated {len(scores)} material scores')
print('Output: outputs/material_scores.csv')
