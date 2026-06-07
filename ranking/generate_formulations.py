import argparse
import itertools
import pandas as pd
import numpy as np


MATRIX_PATH = 'knowledgebase/state_coverage_matrix.csv'


def balance(m, p, n):
    x = np.array([m, p, n], dtype=float)
    mean = x.mean()
    if mean == 0:
        return 0
    cv = x.std() / mean
    return max(0, 1 - cv)


def score(mm, pp, nn, risk, mechanism_factor):
    cov = (mm + pp + nn) / 3
    bal = balance(mm, pp, nn)
    return (
        0.45 * cov +
        0.30 * bal +
        0.15 * mechanism_factor -
        0.10 * risk
    )


def row_to_material(row):
    return {
        'material': row.material,
        'label': row.entropy_control_label,
        'membrane': float(row.membrane_score),
        'protein': float(row.protein_score),
        'na': float(row.nucleic_acid_score),
        'risk': float(row.assay_risk),
    }


def summarize_combo(combo, group, idx):
    mm = sum(x['membrane'] for x in combo)
    pp = sum(x['protein'] for x in combo)
    nn = sum(x['na'] for x in combo)
    risk = sum(x['risk'] for x in combo)
    labels = {x['label'] for x in combo}
    mechanism_factor = len(labels) / 3
    tfi = score(mm, pp, nn, risk, mechanism_factor)

    return [
        f'IBC-{group}-{idx:03d}',
        group,
        ';'.join(x['material'] for x in combo),
        ';'.join(sorted(labels)),
        mm,
        pp,
        nn,
        risk,
        tfi,
    ]


def build(top, output):
    m = pd.read_csv(MATRIX_PATH)

    required = {
        'material',
        'entropy_control_label',
        'membrane_score',
        'protein_score',
        'nucleic_acid_score',
        'assay_risk',
    }
    missing = required - set(m.columns)
    if missing:
        raise ValueError(f'{MATRIX_PATH} missing required columns: {sorted(missing)}')

    physical = [row_to_material(r) for _, r in m[m.entropy_control_label == 'Physical_Stabilization'].iterrows()]
    chemical = [row_to_material(r) for _, r in m[m.entropy_control_label == 'Chemical_Quenching'].iterrows()]
    encapsulation = [row_to_material(r) for _, r in m[m.entropy_control_label == 'Isolation_Encapsulation'].iterrows()]

    pools = {
        'P': physical,
        'C': chemical,
        'E': encapsulation,
    }

    rows = []

    # Single-mechanism combinations: true formulations with two materials from the same principle.
    single_specs = [
        ('P2', 'P', 6),
        ('C2', 'C', 5),
        ('E2', 'E', 5),
    ]
    for group, key, limit in single_specs:
        candidates = []
        for combo in itertools.combinations(pools[key], 2):
            candidates.append(summarize_combo(combo, group, len(candidates) + 1))
        candidates = sorted(candidates, key=lambda x: x[-1], reverse=True)[:limit]
        rows.extend(candidates)

    # Dual-mechanism combinations.
    dual_specs = [
        ('PC', ('P', 'C'), 8),
        ('PE', ('P', 'E'), 8),
        ('CE', ('C', 'E'), 6),
    ]
    for group, keys, limit in dual_specs:
        candidates = []
        for combo in itertools.product(*(pools[k] for k in keys)):
            candidates.append(summarize_combo(combo, group, len(candidates) + 1))
        candidates = sorted(candidates, key=lambda x: x[-1], reverse=True)[:limit]
        rows.extend(candidates)

    # Triple-mechanism combinations: one material from each entropy-control principle.
    triple = []
    for combo in itertools.product(physical, chemical, encapsulation):
        triple.append(summarize_combo(combo, 'PCE', len(triple) + 1))
    triple = sorted(triple, key=lambda x: x[-1], reverse=True)[:16]
    rows.extend(triple)

    columns = [
        'formulation_id',
        'group',
        'materials',
        'entropy_control_labels',
        'membrane',
        'protein',
        'na',
        'assay_risk',
        'predicted_tfi',
    ]

    df = pd.DataFrame(rows, columns=columns)
    df = df.sort_values('predicted_tfi', ascending=False).head(top)

    print(f'Generated {len(df)} true combination formulations')
    df.to_csv(output, index=False)
    print('\nFormulation summary:')
    print(df.groupby('group').size())


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--top', type=int, default=48)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    build(a.top, a.output)
