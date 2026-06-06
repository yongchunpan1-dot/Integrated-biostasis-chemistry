#!/usr/bin/env python3

from itertools import combinations
from pathlib import Path
import argparse
import pandas as pd

try:
    import yaml
except ImportError:
    yaml = None


def load_compatibility_rules(path):

    if yaml is None:
        return {}

    if not Path(path).exists():
        return {}

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def compatibility_value(level):

    mapping = {
        "high": 1.0,
        "medium": 0.5,
        "low": 0.0,
        "none": 1.0
    }

    return mapping.get(str(level).lower(), 0.5)


def calculate_compatibility(materials, rules):

    if not rules:
        return 1.0

    pcr_scores = []
    lcms_scores = []
    ev_scores = []

    for material in materials:

        rule = rules.get(material, {})

        pcr_scores.append(compatibility_value(rule.get("pcr", "medium")))
        lcms_scores.append(compatibility_value(rule.get("lcms", "medium")))
        ev_scores.append(compatibility_value(rule.get("ev", "medium")))

    return (sum(pcr_scores)+sum(lcms_scores)+sum(ev_scores)) / (len(pcr_scores)+len(lcms_scores)+len(ev_scores))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ranking", default="outputs/state_coverage_ranking.csv")
    parser.add_argument("--compatibility", default="knowledgebase/compatibility_rules.yaml")
    parser.add_argument("--top-materials", type=int, default=20)
    parser.add_argument("--combo-size", type=int, default=4)
    parser.add_argument("--top-formulations", type=int, default=48)
    parser.add_argument("--output", default="outputs/top48_state_formulations.csv")

    args = parser.parse_args()
    df = pd.read_csv(args.ranking).head(args.top_materials)
    rules = load_compatibility_rules(args.compatibility)

    rows = []
    for combo in combinations(df.index, args.combo_size):
        sub = df.loc[list(combo)]
        materials = list(sub["material"].astype(str))

        coverage_score = float(sub["coverage_score"].sum())
        compatibility_score = calculate_compatibility(materials, rules)
        simplicity_score = max(0.0, 1.0 - (len(materials)-2)*0.1)

        final_score = (0.50*coverage_score + 0.35*compatibility_score + 0.15*simplicity_score)

        rows.append({
            "formulation": " + ".join(materials),
            "materials": len(materials),
            "coverage_score": round(coverage_score,3),
            "compatibility_score": round(compatibility_score,3),
            "simplicity_score": round(simplicity_score,3),
            "final_score": round(final_score,3)
        })

    out = pd.DataFrame(rows).sort_values("final_score", ascending=False).head(args.top_formulations)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(f"Generated {len(out)} formulations")


if __name__ == "__main__":
    main()
