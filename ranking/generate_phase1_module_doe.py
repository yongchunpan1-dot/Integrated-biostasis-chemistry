#!/usr/bin/env python3

from itertools import combinations, product
from pathlib import Path
import argparse
import pandas as pd


def load_registry(path):
    df = pd.read_csv(path)
    if "status" in df.columns:
        df = df[df["status"].isin(["active", "pending_review"])]
    return df


def top_by_module(df, module, n=12):
    sub = df[df["entropy_module"].astype(str).str.lower() == module]
    priority = {"high": 3, "medium": 2, "low": 1}
    sub = sub.copy()
    sub["priority_score"] = sub["confidence"].astype(str).str.lower().map(priority).fillna(1)
    return sub.sort_values(["priority_score", "material"], ascending=[False, True]).head(n)


def make_within_module_formulations(sub, label, target_n=12):
    rows = []
    names = list(sub["material"].astype(str))

    for name in names[:4]:
        rows.append({
            "formulation_class": label,
            "formulation": name,
            "design_logic": "single_module_anchor"
        })

    for a, b in combinations(names, 2):
        if len(rows) >= target_n:
            break
        rows.append({
            "formulation_class": label,
            "formulation": f"{a} + {b}",
            "design_logic": "within_module_pair"
        })

    return rows[:target_n]


def make_cross_formulations(structural, interface, constraint, target_n=12):
    rows = []
    s_names = list(structural["material"].astype(str).head(6))
    i_names = list(interface["material"].astype(str).head(6))
    c_names = list(constraint["material"].astype(str).head(6))

    for s, i, c in product(s_names, i_names, c_names):
        if len(rows) >= target_n:
            break
        rows.append({
            "formulation_class": "Cross",
            "formulation": f"{s} + {i} + {c}",
            "design_logic": "cross_module_combination"
        })

    return rows[:target_n]


def build_phase1_library(structural, interface, constraint):
    library = pd.concat([structural, interface, constraint], ignore_index=True)
    library = library.copy()
    keep_cols = [
        "material", "category", "entropy_module", "confidence", "status", "source"
    ]
    available = [c for c in keep_cols if c in library.columns]
    library = library[available].drop_duplicates(subset=["material"])
    library.insert(0, "library_id", [f"M{i+1:03d}" for i in range(len(library))])
    return library


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="knowledgebase/material_registry.csv")
    parser.add_argument("--output", default="outputs/phase1_module_doe_48.csv")
    parser.add_argument("--library-output", default="outputs/phase1_selected_material_library.csv")
    parser.add_argument("--per-class", type=int, default=12)
    args = parser.parse_args()

    df = load_registry(args.registry)

    structural = top_by_module(df, "structural", n=12)
    interface = top_by_module(df, "interface", n=12)
    constraint = top_by_module(df, "constraint", n=12)

    rows = []
    rows.extend(make_within_module_formulations(structural, "Structural", args.per_class))
    rows.extend(make_within_module_formulations(interface, "Interface", args.per_class))
    rows.extend(make_within_module_formulations(constraint, "Constraint", args.per_class))
    rows.extend(make_cross_formulations(structural, interface, constraint, args.per_class))

    out = pd.DataFrame(rows)
    out.insert(0, "formulation_id", [f"F{i+1:03d}" for i in range(len(out))])

    library = build_phase1_library(structural, interface, constraint)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    library.to_csv(args.library_output, index=False)

    print(f"Generated {len(out)} phase-1 DOE formulations at {args.output}")
    print(f"Exported {len(library)} selected phase-1 materials at {args.library_output}")


if __name__ == "__main__":
    main()
