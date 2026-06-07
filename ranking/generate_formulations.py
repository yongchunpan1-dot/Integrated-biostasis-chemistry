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


def score(mm, pp, nn, risk, mechanism_factor, family_factor, subfamily_factor, target_bias_bonus=0):
    cov = (mm + pp + nn) / 3
    bal = balance(mm, pp, nn)
    return (
        0.36 * cov +
        0.22 * bal +
        0.17 * mechanism_factor +
        0.15 * family_factor +
        0.10 * subfamily_factor +
        target_bias_bonus -
        0.10 * risk
    )


def row_to_material(row):
    return {
        'material': row.material,
        'label': row.entropy_control_label,
        'family': row.family,
        'subfamily': row.subfamily,
        'membrane': float(row.membrane_score),
        'protein': float(row.protein_score),
        'na': float(row.nucleic_acid_score),
        'risk': float(row.assay_risk),
    }


def diverse(combo):
    families = [x['family'] for x in combo]
    subfamilies = [x['subfamily'] for x in combo]
    return (
        len(families) == len(set(families)) and
        len(subfamilies) == len(set(subfamilies))
    )


def target_bias(mm, pp, nn):
    vals = {'Membrane': mm, 'Protein': pp, 'Nucleic_Acid': nn}
    max_v = max(vals.values())
    min_v = min(vals.values())
    if max_v - min_v <= 1:
        return 'Balanced'
    return max(vals, key=vals.get)


def summarize_combo(combo, group, idx, desired_bias=None):
    if not diverse(combo):
        return None

    mm = sum(x['membrane'] for x in combo)
    pp = sum(x['protein'] for x in combo)
    nn = sum(x['na'] for x in combo)
    risk = sum(x['risk'] for x in combo)
    labels = {x['label'] for x in combo}
    families = {x['family'] for x in combo}
    subfamilies = {x['subfamily'] for x in combo}
    bias = target_bias(mm, pp, nn)

    mechanism_factor = len(labels) / 3
    family_factor = len(families) / len(combo)
    subfamily_factor = len(subfamilies) / len(combo)
    bias_bonus = 0.15 if desired_bias is not None and bias == desired_bias else 0

    tfi = score(
        mm,
        pp,
        nn,
        risk,
        mechanism_factor,
        family_factor,
        subfamily_factor,
        bias_bonus,
    )

    return [
        f'IBC-{group}-{idx:03d}',
        group,
        ';'.join(x['material'] for x in combo),
        ';'.join(sorted(labels)),
        ';'.join(sorted(families)),
        ';'.join(sorted(subfamilies)),
        mm,
        pp,
        nn,
        risk,
        bias,
        tfi,
    ]


def select_diverse(candidates, limit):
    selected = []
    material_counts = {}
    family_pair_counts = {}

    for row in sorted(candidates, key=lambda x: x[-1], reverse=True):
        materials = row[2].split(';')
        families = tuple(sorted(row[4].split(';')))

        if any(material_counts.get(m, 0) >= 3 for m in materials):
            continue
        if family_pair_counts.get(families, 0) >= 2:
            continue

        selected.append(row)
        for m in materials:
            material_counts[m] = material_counts.get(m, 0) + 1
        family_pair_counts[families] = family_pair_counts.get(families, 0) + 1

        if len(selected) >= limit:
            break

    if len(selected) < limit:
        seen = {tuple(r[2].split(';')) for r in selected}
        for row in sorted(candidates, key=lambda x: x[-1], reverse=True):
            key = tuple(row[2].split(';'))
            if key not in seen:
                selected.append(row)
                seen.add(key)
            if len(selected) >= limit:
                break

    return selected[:limit]


def ranked_combinations(materials, group, limit, combo_size=2):
    candidates = []
    for combo in itertools.combinations(materials, combo_size):
        row = summarize_combo(combo, group, len(candidates) + 1)
        if row is not None:
            candidates.append(row)
    return select_diverse(candidates, limit)


def ranked_cross_product(pools, keys, group, limit, desired_bias=None):
    candidates = []
    for combo in itertools.product(*(pools[k] for k in keys)):
        row = summarize_combo(combo, group, len(candidates) + 1, desired_bias=desired_bias)
        if row is not None:
            candidates.append(row)
    return select_diverse(candidates, limit)


def build(top, output):
    m = pd.read_csv(MATRIX_PATH)

    required = {
        'material',
        'entropy_control_label',
        'family',
        'subfamily',
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

    columns = [
        'formulation_id',
        'group',
        'materials',
        'entropy_control_labels',
        'families',
        'subfamilies',
        'membrane',
        'protein',
        'na',
        'assay_risk',
        'target_bias',
        'predicted_tfi',
    ]

    grouped_rows = []

    # Same-principle formulations: identify which internal strategy pairs work.
    grouped_rows.extend(ranked_combinations(physical, 'P2', 8, combo_size=2))
    grouped_rows.extend(ranked_combinations(chemical, 'C2', 8, combo_size=2))
    grouped_rows.extend(ranked_combinations(encapsulation, 'E2', 8, combo_size=2))

    # Cross-principle formulations: preserve space for dual mechanisms.
    grouped_rows.extend(ranked_cross_product(pools, ('P', 'C'), 'PC', 6))
    grouped_rows.extend(ranked_cross_product(pools, ('P', 'E'), 'PE', 6))
    grouped_rows.extend(ranked_cross_product(pools, ('C', 'E'), 'CE', 4))

    # Triple-principle formulations: include balanced and target-biased designs.
    grouped_rows.extend(ranked_cross_product(pools, ('P', 'C', 'E'), 'PCE-B', 2, desired_bias='Balanced'))
    grouped_rows.extend(ranked_cross_product(pools, ('P', 'C', 'E'), 'PCE-M', 2, desired_bias='Membrane'))
    grouped_rows.extend(ranked_cross_product(pools, ('P', 'C', 'E'), 'PCE-P', 2, desired_bias='Protein'))
    grouped_rows.extend(ranked_cross_product(pools, ('P', 'C', 'E'), 'PCE-N', 2, desired_bias='Nucleic_Acid'))

    df = pd.DataFrame(grouped_rows, columns=columns).head(top)

    print(f'Generated {len(df)} subfamily-diverse DOE formulations')
    df.to_csv(output, index=False)
    print('\nFormulation summary:')
    print(df.groupby('group').size())


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--top', type=int, default=48)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    build(a.top, a.output)
