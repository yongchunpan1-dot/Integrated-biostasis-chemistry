#!/usr/bin/env python3

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / 'knowledgebase'
OUT = ROOT / 'outputs'

candidate_path = KB / 'candidate_universe.csv'
registry_path = KB / 'material_registry.csv'
scores_path = KB / 'material_scores.csv'

if candidate_path.exists():
    registry = pd.read_csv(candidate_path)
    source_label = 'candidate_universe.csv'
else:
    registry = pd.read_csv(registry_path)
    source_label = 'material_registry.csv'

required_cols = {'material','category','entropy_module','source','confidence','status'}
missing = required_cols - set(registry.columns)
if missing:
    raise ValueError(f'{source_label} is missing required columns: {sorted(missing)}')

registry = registry.copy().drop_duplicates(subset=['material'])

if scores_path.exists():
    scores = pd.read_csv(scores_path)
else:
    scores = pd.DataFrame(columns=['material','overall_score','evidence_score'])

if 'overall_score' not in scores.columns:
    scores['overall_score'] = 0
if 'evidence_score' not in scores.columns:
    scores['evidence_score'] = 0

merged = registry.merge(
    scores[['material','overall_score','evidence_score']].drop_duplicates(subset=['material']),
    on='material',
    how='left'
)

for col in ['overall_score','evidence_score']:
    merged[col] = merged[col].fillna(0)

status_weight = {
    'active': 3,
    'pending_review': 1,
    'candidate': 1,
    'excluded': -10
}

confidence_weight = {
    'high': 3,
    'medium': 2,
    'low': 1
}

tier_weight = {
    'core': 2,
    'candidate': 1,
    'backup': 0
}

merged['status_weight'] = merged['status'].astype(str).str.lower().map(status_weight).fillna(0)
merged['confidence_weight'] = merged['confidence'].astype(str).str.lower().map(confidence_weight).fillna(1)

if 'universe_tier' in merged.columns:
    merged['tier_weight'] = merged['universe_tier'].astype(str).str.lower().map(tier_weight).fillna(0)
else:
    merged['tier_weight'] = 0

merged['active_core_score'] = (
    merged['overall_score'] +
    merged['evidence_score'] +
    merged['status_weight'] +
    merged['confidence_weight'] +
    merged['tier_weight']
).round(2)

eligible = merged[merged['status'].astype(str).str.lower() != 'excluded'].copy()

# Broad module quotas keep phase-1 screening balanced across mechanism classes.
quotas = {
    'structural': 45,
    'interface': 45,
    'constraint': 35,
    'chemical': 35
}

selected = []
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
if 'universe_tier' in active_core.columns:
    cols.insert(6, 'universe_tier')
if 'aliases' in active_core.columns:
    cols.append('aliases')
if 'mechanism_note' in active_core.columns:
    cols.append('mechanism_note')

active_core[cols].to_csv(KB / 'active_core_library.csv', index=False)
OUT.mkdir(exist_ok=True)
active_core[cols].to_csv(OUT / 'active_core_library.csv', index=False)

print(f'Generated active core library with {len(active_core)} materials from {source_label}')
print(active_core.groupby('entropy_module').size())
print('Output: knowledgebase/active_core_library.csv')
print('Output: outputs/active_core_library.csv')
