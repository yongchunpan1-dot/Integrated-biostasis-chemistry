#!/usr/bin/env python3

"""
Phase 0 Candidate Universe Mining

V1 goal:
- Read search_domains.csv
- Generate literature mining query table
- Create placeholder outputs for downstream normalization

Future versions:
- PubMed E-utilities integration
- PMID retrieval
- Abstract parsing
- Material extraction
- Alias normalization
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / 'knowledgebase'
OUT = ROOT / 'outputs'

OUT.mkdir(exist_ok=True)

search_domains = pd.read_csv(KB / 'search_domains.csv')

queries = []
for _, row in search_domains.iterrows():
    queries.append({
        'domain': row['domain'],
        'priority': row['priority'],
        'query': row['keyword'],
        'status': 'pending_search'
    })

query_df = pd.DataFrame(queries)
query_df.to_csv(OUT / 'literature_queries.csv', index=False)

raw_schema = pd.DataFrame(columns=[
    'domain',
    'query',
    'pmid',
    'title',
    'year',
    'material_raw'
])
raw_schema.to_csv(OUT / 'raw_material_mentions.csv', index=False)

normalized_schema = pd.DataFrame(columns=[
    'material_raw',
    'normalized_material',
    'domain',
    'pmid'
])
normalized_schema.to_csv(OUT / 'normalized_material_mentions.csv', index=False)

candidate_schema = pd.DataFrame(columns=[
    'material',
    'pmid_count',
    'domain_count',
    'mention_count',
    'confidence'
])
candidate_schema.to_csv(OUT / 'mined_materials.csv', index=False)

print('Phase 0 mining scaffold generated')
print('outputs/literature_queries.csv')
print('outputs/raw_material_mentions.csv')
print('outputs/normalized_material_mentions.csv')
print('outputs/mined_materials.csv')
