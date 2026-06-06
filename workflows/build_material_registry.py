#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

REGISTRY='knowledgebase/material_registry.csv'
SEED='knowledgebase/active_library_expansion_seed.csv'
CANDIDATES='outputs/candidate_materials.csv'
OUT='knowledgebase/materials_master_v2.csv'

registry=pd.read_csv(REGISTRY) if Path(REGISTRY).exists() else pd.DataFrame()
seed=pd.read_csv(SEED) if Path(SEED).exists() else pd.DataFrame()

frames=[registry,seed]

if Path(CANDIDATES).exists():
    cand=pd.read_csv(CANDIDATES)
    if 'candidate_material' in cand.columns:
        cand=cand.rename(columns={'candidate_material':'material'})
        cand['status']='pending_review'
        frames.append(cand[['material','status']])

merged=pd.concat(frames,ignore_index=True,sort=False)
merged=merged.drop_duplicates(subset=['material'])
Path('knowledgebase').mkdir(exist_ok=True)
merged.to_csv(OUT,index=False)
print(f'Built registry with {len(merged)} materials')
