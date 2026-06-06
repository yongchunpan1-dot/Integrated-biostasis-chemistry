#!/usr/bin/env python3
from pathlib import Path
import argparse
import pandas as pd

CATEGORY_DESCRIPTOR_MAP = {
    'sugar': ['glass_former', 'protein_stabilizer', 'nucleic_acid_protective'],
    'polyol': ['osmolyte', 'protein_stabilizer'],
    'osmolyte': ['osmolyte', 'protein_stabilizer', 'membrane_stabilizer'],
    'amino_acid': ['protein_stabilizer', 'osmolyte'],
    'polymer': ['polymer', 'membrane_stabilizer', 'protein_stabilizer'],
    'surfactant': ['membrane_stabilizer', 'ev_compatibility'],
    'hydrogel': ['hydrogel', 'membrane_stabilizer'],
    'biopolymer': ['polymer', 'membrane_stabilizer'],
    'protein_polymer': ['polymer', 'protein_stabilizer', 'membrane_stabilizer'],
    'mineral': ['mineralizing', 'membrane_stabilizer', 'nucleic_acid_protective'],
    'buffer': ['pcr_compatibility', 'protein_stabilizer'],
    'chelator': ['nucleic_acid_protective', 'pcr_compatibility'],
    'antioxidant': ['antioxidant', 'protein_stabilizer', 'nucleic_acid_protective'],
}

MODULE_DESCRIPTOR_MAP = {
    'structural': ['glass_former', 'osmolyte', 'protein_stabilizer'],
    'interface': ['membrane_stabilizer', 'polymer', 'ev_compatibility'],
    'constraint': ['hydrogel', 'mineralizing', 'membrane_stabilizer'],
}


def infer_descriptors(row):
    descriptors = set()
    category = str(row.get('category', '')).lower()
    module = str(row.get('entropy_module', '')).lower()
    descriptors.update(CATEGORY_DESCRIPTOR_MAP.get(category, []))
    descriptors.update(MODULE_DESCRIPTOR_MAP.get(module, []))
    return descriptors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--materials', default='knowledgebase/material_registry.csv')
    parser.add_argument('--targets', default='knowledgebase/state_targets.csv')
    parser.add_argument('--output', default='outputs/state_coverage_ranking.csv')
    args = parser.parse_args()

    materials = pd.read_csv(args.materials)
    targets = pd.read_csv(args.targets)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for _, mat in materials.iterrows():
        desc = infer_descriptors(mat)
        score = 0.0
        covered = []
        for _, target in targets.iterrows():
            d = str(target['primary_descriptor'])
            w = float(target['weight'])
            if d in desc:
                score += w
                covered.append(str(target['state_target']))
        rows.append({
            'material': mat.get('material'),
            'category': mat.get('category'),
            'entropy_module': mat.get('entropy_module'),
            'coverage_score': score,
            'covered_states': ';'.join(covered),
            'descriptor_count': len(desc),
            'inferred_descriptors': ';'.join(sorted(desc)),
        })

    out = pd.DataFrame(rows).sort_values('coverage_score', ascending=False)
    out.to_csv(args.output, index=False)
    print(f'Wrote {len(out)} ranked materials to {args.output}')

if __name__ == '__main__':
    main()
