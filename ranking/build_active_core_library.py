#!/usr/bin/env python3

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / 'knowledgebase'
OUT = ROOT / 'outputs'

registry = pd.read_csv(KB / 'material_registry.csv')
scores_path = KB / 'material_scores.csv'

if scores_path.exists():
    scores = pd.read_csv(scores_path)
else:
    scores = registry.copy()
    scores['overall_score'] = 0
    scores['evidence_score'] = 0

merged = registry.merge(
    scores[['material','overall_score','evidence_score']],
    on='material',
    how='left'
)

for col in ['overall_score','evidence_score']:
    merged[col] = merged[col].fillna(0)

status_weight = {
    'active': 3,
    'pending_review': 1,
    'excluded': -10
}

confidence_weight = {
    'high': 3,
    'medium': 2,
    'low': 1
}

merged['status_weight'] = merged['status'].astype(str).str.lower().map(status_weight).fillna(0)
merged['confidence_weight'] = merged['confidence'].astype(str).str.lower().map(confidence_weight).fillna(1)

merged['active_core_score'] = (
    merged['overall_score'] +
    merged['evidence_score'] +
    merged['status_weight'] +
    merged['confidence_weight']
).round(2)

eligible = merged[merged['status'].astype(str).str.lower() != 'excluded'].copy()

# Keep broad mechanism coverage rather than taking a single global top list.
selected = []
quotas = {
    'structural': 40,
    'interface': 40,
    'constraint': 30
}

for module, quota in quotas.items():
    block = eligible[eligible['entropy_module'].astype(str).str.lower() == module]
    block = block.sort_values('active_core_score', ascending=False).head(quota)
    selected.append(block)

active_core = pd.concat(selected, ignore_index=True).drop_duplicates(subset=['material'])
active_core = active_core.sort_values(['entropy_module','active_core_score'], ascending=[True,False])

cols = [
    'material','category','entropy_module','source','confidence','status',
    'overall_score','evidence_score','active_core_score'
]

active_core[cols].to_csv(KB / 'active_core_library.csv', index=False)
OUT.mkdir(exist_ok=True)
active_core[cols].to_csv(OUT / 'active_core_library.csv', index=False)

print(f'Generated active core library with {len(active_core)} materials')
print(active_core.groupby('entropy_module').size())
print('Output: knowledgebase/active_core_library.csv')
print('Output: outputs/active_core_library.csv')
