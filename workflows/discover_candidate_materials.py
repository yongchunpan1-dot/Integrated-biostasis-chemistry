#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from collections import Counter
import pandas as pd

SEED_MATERIALS = [
    'trehalose','sucrose','maltodextrin','lactose','mannitol','sorbitol','xylitol',
    'glycerol','ectoine','hydroxyectoine','betaine','proline','arginine','glycine',
    'methionine','leucine','histidine','taurine','carnitine','dextran','pullulan',
    'alginate','chitosan','gelatin','collagen','hyaluronic acid','cellulose',
    'silica','peg','pvp','poloxamer','albumin','bsa','hsa','edta','egta','dtpa',
    'citrate','phosphate','ascorbate','glutathione','trolox','hepes','tris'
]


def load_known_materials(path: Path) -> set[str]:
    try:
        df = pd.read_csv(path)
        if 'material' in df.columns:
            return {str(x).lower() for x in df['material'].dropna()}
    except Exception:
        pass
    return set()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='outputs/literature_materials_mined.csv')
    parser.add_argument('--known', default='knowledgebase/materials_master.csv')
    parser.add_argument('--output', default='outputs/candidate_materials.csv')
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    text = ' '.join(df.astype(str).fillna('').agg(' '.join, axis=1).tolist()).lower()

    known = load_known_materials(Path(args.known))

    rows = []
    counts = Counter()
    for material in SEED_MATERIALS:
        counts[material] = text.count(material.lower())

    for material, count in counts.most_common():
        if count < 2:
            continue
        rows.append({
            'candidate_material': material,
            'mention_count': count,
            'already_in_master_library': material in known,
            'review_status': 'pending_review'
        })

    out = pd.DataFrame(rows)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(f'Wrote {len(out)} candidates')

if __name__ == '__main__':
    main()
