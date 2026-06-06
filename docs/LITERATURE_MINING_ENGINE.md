# IBC Literature Mining Engine

## Purpose

The Literature Mining Engine updates the IBC material knowledgebase from live scientific literature rather than relying only on manually curated seed materials.

The goal is to support this workflow:

```text
Live literature search
        ↓
Material mention extraction
        ↓
Mechanism/domain assignment
        ↓
Evidence table generation
        ↓
Active library expansion
        ↓
Formulation generation
```

## Current v0.1 implementation

The current implementation uses the public Europe PMC search API, which does not require an API key.

It searches across preservation-related domains:

- cryopreservation
- lyophilization
- vaccine stabilization
- protein formulation
- extracellular vesicle preservation
- cell therapy preservation
- biomaterials
- biomineralization

It then matches retrieved titles and abstracts against materials listed in:

```text
knowledgebase/materials_master.csv
```

The mined result is written to:

```text
outputs/literature_materials_mined.csv
```

## Important limitation

This first version is a conservative literature-mining scaffold. It detects material mentions by dictionary matching. It does not yet perform full natural-language relation extraction, concentration extraction, or outcome extraction.

Future versions should add:

- DOI/PMID normalization
- concentration extraction
- biological system extraction
- preservation outcome extraction
- material synonym expansion
- evidence scoring
- automatic update of materials_master.csv

## Why this matters

IBC should not remain a manually curated list of familiar excipients. The long-term goal is a continuously updating preservation-chemistry knowledgebase that can expand from hundreds to thousands of candidate materials while still prioritizing high-confidence, biocompatible, preservation-relevant candidates.
