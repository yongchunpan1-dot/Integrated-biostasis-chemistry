#!/usr/bin/env python3

from itertools import combinations
from pathlib import Path
import argparse
import pandas as pd


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--ranking',
        default='outputs/state_coverage_ranking.csv'
    )

    parser.add_argument(
        '--top-materials',
        type=int,
        default=20
    )

    parser.add_argument(
        '--combo-size',
        type=int,
        default=4
    )

    parser.add_argument(
        '--top-formulations',
        type=int,
        default=48
    )

    parser.add_argument(
        '--output',
        default='outputs/top48_state_formulations.csv'
    )

    args = parser.parse_args()

    df = pd.read_csv(args.ranking)

    df = df.head(args.top_materials)

    rows = []

    for combo in combinations(df.index, args.combo_size):

        sub = df.loc[list(combo)]

        # --------------------------------------------------
        # 1. Biological State Coverage
        # --------------------------------------------------

        coverage = float(sub['coverage_score'].sum())

        # --------------------------------------------------
        # 2. Assay Compatibility
        # (placeholder until compatibility_rules.yaml exists)
        # --------------------------------------------------

        compatibility = 1.0

        if 'covered_states' in sub.columns:

            states = ';'.join(
                sub['covered_states'].astype(str)
            )

            if 'PCR_readout_compatibility' in states:
                compatibility += 0.50

            if 'EV_assay_compatibility' in states:
                compatibility += 0.50

            if 'LCMS_readout_compatibility' in states:
                compatibility += 0.25

        # --------------------------------------------------
        # 3. Simplicity
        # fewer components = easier translation
        # --------------------------------------------------

        simplicity = max(
            0.0,
            1.0 - (len(sub) - 2) * 0.1
        )

        # --------------------------------------------------
        # Final Score
        # --------------------------------------------------

        final_score = (
            0.50 * coverage +
            0.35 * compatibility +
            0.15 * simplicity
        )

        rows.append({

            'formulation':
                ' + '.join(
                    sub['material'].astype(str)
                ),

            'materials':
                len(sub),

            'coverage_score':
                round(coverage, 3),

            'compatibility_score':
                round(compatibility, 3),

            'simplicity_score':
                round(simplicity, 3),

            'final_score':
                round(final_score, 3)

        })

    out = pd.DataFrame(rows)

    out = out.sort_values(
        'final_score',
        ascending=False
    )

    out = out.head(
        args.top_formulations
    )

    Path(args.output).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    out.to_csv(
        args.output,
        index=False
    )

    print(
        f'Generated {len(out)} formulations'
    )


if __name__ == '__main__':
    main()
```
