#!/usr/bin/env python3
"""Sync evidence metadata into knowledgebase/state_coverage_matrix.csv."""

from pathlib import Path
import argparse
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "knowledgebase"

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

RANK = {"Unknown": 0, "low": 1, "medium": 2, "high": 3, "Low": 1, "Medium": 2, "High": 3}


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
    p = argparse.ArgumentParser()
    p.add_argument("--output", default=str(KB / "state_coverage_matrix.csv"))
    a = p.parse_args()

    state = read_csv(KB / "state_coverage_matrix.csv")
    universe = read_csv(KB / "candidate_universe.csv")
    lit = read_csv(KB / "literature_materials.csv")
    reg = read_csv(KB / "material_evidence_registry.csv")
    alias_df = read_csv(KB / "material_aliases.csv")

    amap = dict(ALIASES)
    if not alias_df.empty:
        for _, r in alias_df.iterrows():
            amap[str(r["alias"]).strip()] = str(r["normalized_material"]).strip()

    for df in [universe, lit, reg]:
        if not df.empty and "material" in df.columns:
            df["_m"] = df["material"].apply(lambda x: norm(x, amap))

    rows = []
    for _, row in state.iterrows():
        m = norm(row["material"], amap)
        u = universe[universe["_m"] == m] if "_m" in universe else pd.DataFrame()
        l = lit[lit["_m"] == m] if "_m" in lit else pd.DataFrame()
        r = reg[reg["_m"] == m] if "_m" in reg else pd.DataFrame()

        sources = sorted(set(u["source"])) if not u.empty and "source" in u else []
        domains = sorted(set(l["domain"])) if not l.empty and "domain" in l else []
        types = sorted(set(r["evidence_type"])) if not r.empty and "evidence_type" in r else []
        vals = []
        if not u.empty and "confidence" in u: vals += list(u["confidence"])
        if not l.empty and "evidence_level" in l: vals += list(l["evidence_level"])
        if not r.empty and "evidence_strength" in r: vals += list(r["evidence_strength"])

        row["evidence_count"] = len(u) + len(l) + len(r)
        row["confidence"] = best(vals)
        row["evidence_sources"] = ";".join([x for x in sources if x])
        row["literature_domains"] = ";".join([x for x in domains if x])
        row["registry_evidence_types"] = ";".join([x for x in types if x])

        if len(l) or "literature_seed" in sources:
            row["evidence_status"] = "Literature_Supported"
        elif len(r):
            row["evidence_status"] = "Evidence_Pending_PMID"
        elif sources:
            row["evidence_status"] = "Seed_Supported"
        else:
            row["evidence_status"] = "Unreviewed"
        rows.append(row)

    out = pd.DataFrame(rows)
    preferred = ["material","entropy_control_label","family","subfamily","membrane_score","protein_score","nucleic_acid_score","assay_risk","evidence_count","confidence","evidence_status","evidence_sources","literature_domains","registry_evidence_types","notes"]
    cols = [c for c in preferred if c in out.columns] + [c for c in out.columns if c not in preferred]
    out[cols].to_csv(a.output, index=False)
    print(f"Synced evidence for {len(out)} materials -> {a.output}")

if __name__ == "__main__":
    main()
