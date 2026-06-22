#!/usr/bin/env python3
"""Sync evidence metadata into knowledgebase/core_material_state_matrix.csv.

This script keeps the core material state matrix as the source of truth for
formulation design, then fills evidence metadata from the candidate universe
and the PMID/DOI evidence registry.
"""

from pathlib import Path
import argparse
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "knowledgebase"

CORE_MATRIX = KB / "core_material_state_matrix.csv"
CANDIDATE_UNIVERSE = KB / "candidate_universe.csv"
EVIDENCE_REGISTRY = KB / "material_evidence_registry.csv"
ALIASES_FILE = KB / "material_aliases.csv"

ALIASES = {
    "PEG": "PEG_mid_MW",
    "PVP": "PVP_mid_MW",
    "Dextran": "Dextran_mid_MW",
    "NAC": "N_Acetylcysteine",
    "Silica": "Silicic_Acid",
    "Poloxamer_188": "Poloxamer188",
    "Hydroxypropyl_beta_Cyclodextrin": "Hydroxypropyl_Beta_Cyclodextrin",
    "Sucrose_Acetate_Isobutyrate": "SAIB",
}

RANK = {
    "Unknown": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "Low": 1,
    "Medium": 2,
    "High": 3,
}


def read_csv(path):
    return pd.read_csv(path).fillna("") if path.exists() else pd.DataFrame()


def norm(x, amap):
    s = str(x).strip()
    return amap.get(s, amap.get(s.replace("_", " "), s))


def best(values):
    out, score = "Unknown", 0
    for v in values:
        r = RANK.get(str(v).strip(), 0)
        if r > score:
            out, score = str(v).strip().capitalize(), r
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(CORE_MATRIX))
    args = parser.parse_args()

    state = read_csv(CORE_MATRIX)
    universe = read_csv(CANDIDATE_UNIVERSE)
    registry = read_csv(EVIDENCE_REGISTRY)
    alias_df = read_csv(ALIASES_FILE)

    if state.empty:
        raise FileNotFoundError(f"Core material matrix not found or empty: {CORE_MATRIX}")

    amap = dict(ALIASES)
    if not alias_df.empty:
        for _, row in alias_df.iterrows():
            amap[str(row["alias"]).strip()] = str(row["normalized_material"]).strip()

    for df in [universe, registry]:
        if not df.empty and "material" in df.columns:
            df["_m"] = df["material"].apply(lambda x: norm(x, amap))

    rows = []
    for _, row in state.iterrows():
        m = norm(row["material"], amap)
        u = universe[universe["_m"] == m] if "_m" in universe else pd.DataFrame()
        r = registry[registry["_m"] == m] if "_m" in registry else pd.DataFrame()

        sources = sorted(set(u["source"])) if not u.empty and "source" in u else []
        types = sorted(set(r["evidence_type"])) if not r.empty and "evidence_type" in r else []
        assays = sorted(set(r["assay"])) if not r.empty and "assay" in r else []
        targets = sorted(set(r["target"])) if not r.empty and "target" in r else []

        vals = []
        if not u.empty and "confidence" in u:
            vals += list(u["confidence"])
        if not r.empty and "evidence_strength" in r:
            vals += list(r["evidence_strength"])

        row["evidence_count"] = len(u) + len(r)
        row["confidence"] = best(vals)
        row["evidence_sources"] = ";".join([x for x in sources if x])
        row["registry_evidence_types"] = ";".join([x for x in types if x])
        row["registry_assays"] = ";".join([x for x in assays if x])
        row["registry_targets"] = ";".join([x for x in targets if x])

        if len(r):
            row["evidence_status"] = "Registry_Supported"
        elif "literature_seed" in sources:
            row["evidence_status"] = "Literature_Seeded"
        elif sources:
            row["evidence_status"] = "Candidate_Seeded"
        else:
            row["evidence_status"] = "Unreviewed"

        rows.append(row)

    out = pd.DataFrame(rows)
    preferred = [
        "material",
        "entropy_control_label",
        "family",
        "subfamily",
        "membrane_score",
        "protein_score",
        "nucleic_acid_score",
        "assay_risk",
        "evidence_count",
        "confidence",
        "evidence_status",
        "evidence_sources",
        "registry_evidence_types",
        "registry_assays",
        "registry_targets",
        "notes",
    ]
    cols = [c for c in preferred if c in out.columns] + [c for c in out.columns if c not in preferred]
    out[cols].to_csv(args.output, index=False)
    print(f"Synced evidence for {len(out)} core materials -> {args.output}")


if __name__ == "__main__":
    main()
