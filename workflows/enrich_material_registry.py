#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

INPUT='knowledgebase/materials_master_v2.csv'
OUTPUT='knowledgebase/materials_master_v2_enriched.csv'

CATEGORY_MAP={
 'trehalose':'sugar','sucrose':'sugar','mannitol':'polyol','glycerol':'polyol',
 'ectoine':'osmolyte','hydroxyectoine':'osmolyte','betaine':'osmolyte',
 'arginine':'amino_acid','histidine':'amino_acid','proline':'amino_acid',
 'dextran':'polymer','pullulan':'polymer','peg':'polymer','pvp':'polymer',
 'alginate':'hydrogel','chitosan':'hydrogel','silica':'mineral'
}

if not Path(INPUT).exists():
    raise FileNotFoundError(INPUT)

_df=pd.read_csv(INPUT)

if 'material' in _df.columns:
    lower=_df['material'].astype(str).str.lower()
    _df['descriptor_category']=lower.map(CATEGORY_MAP).fillna('unknown')
    _df['water_solubility']='unknown'
    _df['ev_compatibility']='unknown'
    _df['pcr_compatibility']='unknown'
    _df['protein_compatibility']='unknown'
    _df['rank_ready']=False

_df.to_csv(OUTPUT,index=False)
print(f'Enriched {len(_df)} materials')
