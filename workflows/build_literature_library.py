#!/usr/bin/env python3
"""Build an IBC literature-derived material evidence table.

This script queries the Europe PMC public REST API, searches preservation-related
literature domains, matches retrieved titles/abstracts against the local IBC
materials dictionary, and writes mined evidence tables to outputs/.

It is intentionally lightweight and does not require an API key.
"""

from __future__ import annotations

import argparse
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

EUROPE_PMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

DOMAIN_QUERIES: dict[str, list[str]] = {
    "cryopreservation": [
        "cryopreservation additive",
        "cryoprotectant osmolyte",
        "cell cryopreservation excipient",
    ],
    "lyophilization": [
        "lyophilization excipient",
        "freeze drying stabilizer",
        "drying protection excipient",
    ],
    "vaccine_stabilization": [
        "vaccine stabilization excipient",
        "lyophilized vaccine stabilizer",
        "vaccine formulation excipient",
    ],
    "protein_formulation": [
        "protein formulation excipient",
        "monoclonal antibody formulation stabilizer",
        "protein aggregation inhibitor excipient",
    ],
    "extracellular_vesicle_preservation": [
        "extracellular vesicle preservation",
        "exosome storage stabilizer",
        "extracellular vesicle lyophilization",
    ],
    "cell_therapy_preservation": [
        "cell therapy preservation additive",
        "cell formulation excipient",
        "cell storage stabilizer",
    ],
    "biomaterials": [
        "hydrogel preservation biomaterial",
        "biomaterial encapsulation preservation",
        "protective hydrogel biological preservation",
    ],
    "biomineralization": [
        "silica encapsulation preservation",
        "biosilicification biomolecule preservation",
        "calcium phosphate encapsulation biomolecule",
    ],
}

MECHANISM_ALIASES = {
    "Structural_Stabilization": "structural_stabilization",
    "Interface_Stabilization": "interface_stabilization",
    "Chemical_Stabilization": "chemical_stabilization",
    "Physical_Encapsulation": "physical_encapsulation",
}


@dataclass(frozen=True)
class Material:
    name: str
    mechanism_class: str
    status: str
    pattern: re.Pattern[str]


def canonical_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("_", " ").strip()


def compile_material_pattern(name: str) -> re.Pattern[str]:
    plain = re.escape(canonical_text(name))
    compact = re.escape(str(name).replace("_", " "))
    pattern = rf"\b({plain}|{compact})\b"
    return re.compile(pattern, flags=re.IGNORECASE)


def load_materials(path: Path) -> list[Material]:
    df = pd.read_csv(path)
    required = {"material", "mechanism_class", "status"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in {path}: {sorted(missing)}")

    materials: list[Material] = []
    for _, row in df.iterrows():
        name = str(row["material"]).strip()
        if not name or name.lower() == "nan":
            continue
        materials.append(
            Material(
                name=name,
                mechanism_class=str(row["mechanism_class"]).strip(),
                status=str(row["status"]).strip(),
                pattern=compile_material_pattern(name),
            )
        )
    return materials


def search_europe_pmc(query: str, page_size: int = 50) -> list[dict]:
    params = {
        "query": query,
        "format": "json",
        "pageSize": page_size,
        "resultType": "core",
    }
    response = requests.get(EUROPE_PMC_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get("resultList", {}).get("result", [])


def paper_text(paper: dict) -> str:
    return " ".join(
        [
            str(paper.get("title", "")),
            str(paper.get("abstractText", "")),
        ]
    )


def infer_evidence_level(material_status: str, paper: dict) -> str:
    publication_type = str(paper.get("pubType", "")).lower()
    if material_status == "active":
        return "high_prior"
    if "review" in publication_type:
        return "review_supported"
    return "literature_mentioned"


def mine_domain(
    domain: str,
    queries: Iterable[str],
    materials: list[Material],
    page_size: int,
    delay: float,
) -> list[dict]:
    rows: list[dict] = []
    seen = set()

    for query in queries:
        papers = search_europe_pmc(query, page_size=page_size)
        time.sleep(delay)

        for paper in papers:
            text = paper_text(paper)
            if not text.strip():
                continue

            pmid = paper.get("pmid", "")
            doi = paper.get("doi", "")
            title = paper.get("title", "")
            journal = paper.get("journalTitle", "")
            year = paper.get("pubYear", "")

            for material in materials:
                if not material.pattern.search(text):
                    continue

                key = (material.name, domain, pmid, doi, title)
                if key in seen:
                    continue
                seen.add(key)

                rows.append(
                    {
                        "material": material.name,
                        "source_domain": domain,
                        "query": query,
                        "paper_title": title,
                        "doi": doi,
                        "pmid": pmid,
                        "journal": journal,
                        "year": year,
                        "mechanism_class": material.mechanism_class,
                        "material_status": material.status,
                        "evidence_level": infer_evidence_level(material.status, paper),
                    }
                )
    return rows


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=["material", "mention_count", "domains_found", "first_year", "latest_year"]
        )

    work = df.copy()
    work["year_numeric"] = pd.to_numeric(work["year"], errors="coerce")
    summary = (
        work.groupby("material")
        .agg(
            mention_count=("paper_title", "count"),
            domains_found=("source_domain", lambda x: ";".join(sorted(set(map(str, x))))),
            first_year=("year_numeric", "min"),
            latest_year=("year_numeric", "max"),
        )
        .reset_index()
        .sort_values(["mention_count", "material"], ascending=[False, True])
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine literature for IBC materials.")
    parser.add_argument("--materials", default="knowledgebase/materials_master.csv")
    parser.add_argument("--output", default="outputs/literature_materials_mined.csv")
    parser.add_argument("--summary", default="outputs/mining_summary.csv")
    parser.add_argument("--page-size", type=int, default=50)
    parser.add_argument("--delay", type=float, default=0.25)
    args = parser.parse_args()

    material_path = Path(args.materials)
    output_path = Path(args.output)
    summary_path = Path(args.summary)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    materials = load_materials(material_path)
    all_rows: list[dict] = []

    for domain, queries in DOMAIN_QUERIES.items():
        print(f"Mining domain: {domain}")
        rows = mine_domain(domain, queries, materials, args.page_size, args.delay)
        print(f"  matched rows: {len(rows)}")
        all_rows.extend(rows)

    columns = [
        "material",
        "source_domain",
        "query",
        "paper_title",
        "doi",
        "pmid",
        "journal",
        "year",
        "mechanism_class",
        "material_status",
        "evidence_level",
    ]
    mined = pd.DataFrame(all_rows, columns=columns).drop_duplicates()
    mined.to_csv(output_path, index=False)

    summary = build_summary(mined)
    summary.to_csv(summary_path, index=False)

    print(f"Wrote {len(mined)} mined evidence rows to {output_path}")
    print(f"Wrote {len(summary)} material summary rows to {summary_path}")


if __name__ == "__main__":
    main()
