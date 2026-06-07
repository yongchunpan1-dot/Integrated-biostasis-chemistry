#!/usr/bin/env python3

"""
Phase 0 Candidate Universe Mining

This script supports two modes:

1. Offline scaffold mode, default:
   - Reads search_domains.csv
   - Writes outputs/literature_queries.csv
   - Creates empty downstream output tables

2. PubMed mining mode:
   - Use --fetch-pubmed
   - Searches PubMed with NCBI E-utilities
   - Fetches titles, abstracts, and years
   - Matches materials from material_dictionary.csv and material_aliases.csv
   - Writes raw, normalized, and ranked material candidate tables

The script does not directly modify candidate_universe.csv. Human review should happen
before mined candidates are promoted into the frozen candidate universe.
"""

from __future__ import annotations

import argparse
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / 'knowledgebase'
OUT = ROOT / 'outputs'

EUTILS = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils'


def read_csv_required(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f'Missing required file: {path}')
    return pd.read_csv(path)


def pubmed_get(endpoint: str, params: Dict[str, str]) -> bytes:
    url = f'{EUTILS}/{endpoint}?{urllib.parse.urlencode(params)}'
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def search_pubmed(query: str, retmax: int, email: str | None = None) -> List[str]:
    params = {
        'db': 'pubmed',
        'term': query,
        'retmode': 'xml',
        'retmax': str(retmax),
        'sort': 'relevance',
    }
    if email:
        params['email'] = email

    xml_bytes = pubmed_get('esearch.fcgi', params)
    root = ET.fromstring(xml_bytes)
    return [elem.text for elem in root.findall('.//Id') if elem.text]


def fetch_pubmed_records(pmids: List[str], email: str | None = None) -> List[Dict[str, str]]:
    if not pmids:
        return []

    params = {
        'db': 'pubmed',
        'id': ','.join(pmids),
        'retmode': 'xml',
    }
    if email:
        params['email'] = email

    xml_bytes = pubmed_get('efetch.fcgi', params)
    root = ET.fromstring(xml_bytes)

    records = []
    for article in root.findall('.//PubmedArticle'):
        pmid_elem = article.find('.//PMID')
        pmid = pmid_elem.text if pmid_elem is not None else ''

        title_elem = article.find('.//ArticleTitle')
        title = ''.join(title_elem.itertext()) if title_elem is not None else ''

        abstract_parts = []
        for abs_elem in article.findall('.//Abstract/AbstractText'):
            abstract_parts.append(''.join(abs_elem.itertext()))
        abstract = ' '.join(abstract_parts)

        year = ''
        year_elem = article.find('.//PubDate/Year')
        if year_elem is not None and year_elem.text:
            year = year_elem.text
        else:
            medline_date = article.find('.//PubDate/MedlineDate')
            if medline_date is not None and medline_date.text:
                match = re.search(r'(19|20)\d{2}', medline_date.text)
                if match:
                    year = match.group(0)

        records.append({
            'pmid': pmid,
            'title': title,
            'abstract': abstract,
            'year': year,
        })

    return records


def build_material_terms(dictionary: pd.DataFrame, aliases: pd.DataFrame) -> pd.DataFrame:
    terms = []

    for _, row in dictionary.iterrows():
        material = str(row['material'])
        terms.append({
            'term': material,
            'normalized_material': material,
            'category': row.get('category', ''),
            'entropy_module': row.get('entropy_module', ''),
            'priority': row.get('priority', ''),
        })
        terms.append({
            'term': material.replace('_', ' '),
            'normalized_material': material,
            'category': row.get('category', ''),
            'entropy_module': row.get('entropy_module', ''),
            'priority': row.get('priority', ''),
        })

    if len(aliases):
        for _, row in aliases.iterrows():
            terms.append({
                'term': str(row['alias']),
                'normalized_material': str(row['normalized_material']),
                'category': '',
                'entropy_module': '',
                'priority': '',
            })

    terms_df = pd.DataFrame(terms)
    terms_df = terms_df.dropna(subset=['term', 'normalized_material'])
    terms_df['term'] = terms_df['term'].astype(str).str.strip()
    terms_df = terms_df[terms_df['term'] != '']
    terms_df = terms_df.drop_duplicates(subset=['term', 'normalized_material'])
    terms_df['term_length'] = terms_df['term'].str.len()
    return terms_df.sort_values('term_length', ascending=False)


def material_hits(text: str, terms_df: pd.DataFrame) -> Iterable[Dict[str, str]]:
    if not text:
        return []

    hits = []
    for _, row in terms_df.iterrows():
        term = str(row['term'])
        pattern = r'(?<![A-Za-z0-9])' + re.escape(term) + r'(?![A-Za-z0-9])'
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append({
                'material_raw': term,
                'normalized_material': row['normalized_material'],
                'category': row.get('category', ''),
                'entropy_module': row.get('entropy_module', ''),
                'priority': row.get('priority', ''),
            })
    return hits


def write_empty_outputs(query_df: pd.DataFrame) -> None:
    query_df.to_csv(OUT / 'literature_queries.csv', index=False)

    pd.DataFrame(columns=[
        'domain', 'query', 'pmid', 'title', 'year', 'material_raw'
    ]).to_csv(OUT / 'raw_material_mentions.csv', index=False)

    pd.DataFrame(columns=[
        'material_raw', 'normalized_material', 'domain', 'pmid'
    ]).to_csv(OUT / 'normalized_material_mentions.csv', index=False)

    pd.DataFrame(columns=[
        'material', 'pmid_count', 'domain_count', 'mention_count', 'confidence'
    ]).to_csv(OUT / 'mined_materials.csv', index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--fetch-pubmed', action='store_true', help='Actually query PubMed using NCBI E-utilities')
    parser.add_argument('--retmax', type=int, default=50, help='Max PubMed records per query')
    parser.add_argument('--email', default=None, help='Optional email for NCBI E-utilities')
    parser.add_argument('--sleep', type=float, default=0.34, help='Delay between NCBI requests')
    args = parser.parse_args()

    OUT.mkdir(exist_ok=True)

    search_domains = read_csv_required(KB / 'search_domains.csv')
    dictionary = read_csv_required(KB / 'material_dictionary.csv')
    aliases_path = KB / 'material_aliases.csv'
    aliases = pd.read_csv(aliases_path) if aliases_path.exists() else pd.DataFrame(columns=['alias', 'normalized_material'])

    query_df = search_domains.rename(columns={'keyword': 'query'}).copy()
    query_df['status'] = 'pending_search'
    query_df.to_csv(OUT / 'literature_queries.csv', index=False)

    if not args.fetch_pubmed:
        write_empty_outputs(query_df)
        print('Phase 0 mining scaffold generated. Use --fetch-pubmed to query PubMed.')
        print('Output: outputs/literature_queries.csv')
        return

    terms_df = build_material_terms(dictionary, aliases)

    raw_rows = []
    norm_rows = []

    for _, q in query_df.iterrows():
        domain = q['domain']
        query = q['query']
        print(f'Searching PubMed: [{domain}] {query}')

        try:
            pmids = search_pubmed(query, retmax=args.retmax, email=args.email)
            time.sleep(args.sleep)
            records = fetch_pubmed_records(pmids, email=args.email)
            time.sleep(args.sleep)
        except Exception as exc:
            print(f'WARNING: PubMed query failed for {query}: {exc}')
            continue

        for rec in records:
            text = f"{rec.get('title', '')} {rec.get('abstract', '')}"
            hits = material_hits(text, terms_df)
            for hit in hits:
                raw_rows.append({
                    'domain': domain,
                    'query': query,
                    'pmid': rec.get('pmid', ''),
                    'title': rec.get('title', ''),
                    'year': rec.get('year', ''),
                    'material_raw': hit['material_raw'],
                })
                norm_rows.append({
                    'material_raw': hit['material_raw'],
                    'normalized_material': hit['normalized_material'],
                    'domain': domain,
                    'pmid': rec.get('pmid', ''),
                    'category': hit.get('category', ''),
                    'entropy_module': hit.get('entropy_module', ''),
                    'priority': hit.get('priority', ''),
                })

    raw_df = pd.DataFrame(raw_rows)
    norm_df = pd.DataFrame(norm_rows)

    raw_cols = ['domain', 'query', 'pmid', 'title', 'year', 'material_raw']
    norm_cols = ['material_raw', 'normalized_material', 'domain', 'pmid', 'category', 'entropy_module', 'priority']

    if raw_df.empty:
        raw_df = pd.DataFrame(columns=raw_cols)
    if norm_df.empty:
        norm_df = pd.DataFrame(columns=norm_cols)

    raw_df.to_csv(OUT / 'raw_material_mentions.csv', index=False)
    norm_df.to_csv(OUT / 'normalized_material_mentions.csv', index=False)

    if norm_df.empty:
        ranked = pd.DataFrame(columns=['material', 'pmid_count', 'domain_count', 'mention_count', 'confidence'])
    else:
        ranked = norm_df.groupby('normalized_material').agg(
            pmid_count=('pmid', 'nunique'),
            domain_count=('domain', 'nunique'),
            mention_count=('normalized_material', 'size')
        ).reset_index().rename(columns={'normalized_material': 'material'})

        ranked['confidence'] = ranked.apply(
            lambda r: 'high' if r['pmid_count'] >= 10 or r['domain_count'] >= 3 else ('medium' if r['pmid_count'] >= 3 else 'low'),
            axis=1
        )
        ranked = ranked.sort_values(['pmid_count', 'domain_count', 'mention_count'], ascending=False)

    ranked.to_csv(OUT / 'mined_materials.csv', index=False)

    print(f'Raw material mentions: {len(raw_df)}')
    print(f'Normalized material mentions: {len(norm_df)}')
    print(f'Mined materials: {len(ranked)}')
    print('Output: outputs/raw_material_mentions.csv')
    print('Output: outputs/normalized_material_mentions.csv')
    print('Output: outputs/mined_materials.csv')


if __name__ == '__main__':
    main()
