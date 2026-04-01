# MAS LCE final research compendium

This package reconstructs the David Graz MAS LCE project on fraudulent online classified ads as a self-contained English compendium.

## Main files

- `reports/final_article.pdf` - article-style English redesign of the thesis
- `reports/integrity_audit.pdf` - reproducibility and integrity audit
- `reports/project_guide.pdf` - package guide and data dictionary
- `data/canonical/` - sanitised canonical datasets
- `data/metadata/` - source inventory, manifest, checksums, discrepancy tables
- `scripts/build_all.py` - Python-only build entry point

## Rebuild

```bash
python scripts/build_all.py --use-packaged-data
```

If you have the original extracted `_Master_LCE_Docs` source tree, you can also rebuild from source:

```bash
python scripts/build_all.py --source-root /path/to/_Master_LCE_Docs
```

The package intentionally excludes unsafe legacy scraper code and relies only on archived, sanitised data for reproduction.
