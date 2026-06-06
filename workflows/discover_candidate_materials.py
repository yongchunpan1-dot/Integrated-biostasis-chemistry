#!/usr/bin/env python3
"""Discover candidate preservation materials from mined literature.

This script is intentionally conservative. It reads mined literature output from
workflows/build_literature_library.py and extracts candidate material-like terms
from titles. It does not automatically promote candidates into the active library.

Output:
  outputs/candidate_materials.csv

The goal is to move from:
  known material dictionary matching

toward:
  literature -> candidate material discovery -> review -> active library
"""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "based", "by", "for", "from", "in",
    "into", "is", "of", "on", "or", "the", "to", "using", "with", "without",
    "effect", "effects", "study", "studies", "evaluation", "analysis", "role",
    "impact", "improved", "improvement", "stability", "stabilization", "storage",
    "preservation", "formulation", "formulations", "cryopreservation",
    "lyophilization", "vaccine", "protein", "cell", "cells", "vesicles",
    "extracellular", "biomaterials", "biomaterial", "hydrogel", "hydrogels",
    "encapsulation", "encapsulated", "delivery", "system", "systems",
}

# Material-like suffixes and patterns common in formulation literature.
MATERIAL_PATTERNS = [
    r"\b[A-Za-z]+ose\b",          # sugars: sucrose, trehalose, maltose
    r"\b[A-Za-z]+itol\b",         # polyols: mannitol, sorbitol, xylitol
    r"\b[A-Za-z]+ol\b",           # glycerol, propylene glycol-like terms
    r"\b[A-Za-z]+ine\b",          # amino acids/osmolytes: proline, betaine
    r"\b[A-Za-z]+ate\b",          # citrate, phosphate, ascorbate
    r"\b[A-Za-z]+mer\b",          # polymer, poloxamer
    r"\b[A-Za-z]+an\b",           # chitosan, pullulan, dextran
    r"\bPEG\b",
    r"\bPVP\b",
    r"\bBSA\b",
    r"\bHSA\b",
    r"\bEDTA\b",
    r"\bEGTA\b",
    r"\bDTPA\b",
]

NEGATIVE_TERMS = {
    "ethanol", "methanol", "acetone", "acetonitrile", "chloroform", "sds",
    "triton", "urea", "guanidine", "formaldehyde", "paraformaldehyde",
}


def normalize_term(term: str) -> str:
    term = term.strip(" .,:;()[]{}\n\t")
    term = re.sub(r"\s+", " ", term)
    return term


def load_known_materials(path: Path) -> set[str]:
    if not path.exists():
        return set()
    df = pd.read_csv(path)
    if "material" not in df.columns:
        return set()
    return {str(x).replace("_", " ").lower() for x in df["material"].dropna()}


def extract_candidates(text: str) -> set[str]:
    candidates: set[str] = set()
    for pattern in MATERIAL_PATTERNS:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            term = normalize_term(match)
            if not term:
                continue
            low = term.lower()
            if low in STOPWORDS or low in NEGATIVE_TERMS:
                continue
            if len(low) < 3:
                continue
            candidates.add(term)
    return candidates


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover candidate IBC materials from mined literature.")
    parser.add_argument("--input", default="outputs/literature_materials_mined.csv")
    parser.add_argument("--known", default="knowledgebase/materials_master.csv")
    parser.add_argument("--output", default="outputs/candidate_materials.csv")
    parser.add_argument("--min-count", type=int, default=2)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    mined = pd.read_csv(input_path)
    known = load_known_materials(Path(args.known))

    counts: Counter[str] = Counter()
    domains: defaultdict[str, set[str]] = defaultdict(set)
    example_titles: dict[str, str] = {}

    for _, row in mined.iterrows():
        title = str(row.get("paper_title", ""))
        domain = str(row.get("source_domain", ""))
        for candidate in extract_candidates(title):
            low = candidate.lower()
            if low in known:
                continue
            counts[candidate] += 1
            domains[candidate].add(domain)
            example_titles.setdefault(candidate, title)

    rows = []
    for candidate, count in counts.most_common():
        if count < args.min_count:
            continue
        rows.append(
            {
                "candidate_material": candidate,
                "mention_count": count,
                "domains_found": ";".join(sorted(domains[candidate])),
                "review_status": "pending_review",
                "suggested_action": "curate_before_active_library",
                "example_title": example_titles.get(candidate, ""),
            }
        )

    out = pd.DataFrame(
        rows,
        columns=[
            "candidate_material",
            "mention_count",
            "domains_found",
            "review_status",
            "suggested_action",
            "example_title",
        ],
    )
    out.to_csv(output_path, index=False)
    print(f"Wrote {len(out)} candidate materials to {output_path}")


if __name__ == "__main__":
    main()
