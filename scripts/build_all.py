from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from analysis_pipeline import (
    build_qualitative_themes,
    build_source_inventory,
    canonicalize_dataset,
    compare_versions,
    confirmed_summary,
    evaluate_confirmed_extremes,
    evaluate_random_forest,
    get_key_source_paths,
    indicator_distribution,
    load_raw_csv,
    metrics_dataframe,
    plot_indicator_distribution,
    plot_roc_curves,
    plot_workflow,
    risk_summary,
    status_summary,
)
from helpers import ensure_dir, latex_escape, rel, sha256_file, write_json, write_text
from report_templates import build_article_tex, build_audit_tex, build_guide_tex


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the MAS LCE final research compendium.")
    parser.add_argument("--source-root", type=Path, default=None, help="Path to the extracted _Master_LCE_Docs folder.")
    parser.add_argument("--use-packaged-data", action="store_true", help="Reuse the canonical packaged data instead of rebuilding from the source corpus.")
    return parser.parse_args()



def source_root_from_default() -> Path:
    default = Path("/mnt/data/master_lce_extracted/_Master_LCE_Docs")
    if default.exists():
        return default
    raise FileNotFoundError("No source root supplied and default extracted source tree was not found.")



def compile_latex(tex_path: Path) -> None:
    cwd = tex_path.parent
    cmd = ["pdflatex", "-interaction=nonstopmode", tex_path.name]
    for _ in range(2):
        result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
        log_path = cwd / (tex_path.stem + ".build.log")
        log_path.write_text(result.stdout, encoding="utf-8")
        if result.returncode != 0:
            raise RuntimeError(f"LaTeX compilation failed for {tex_path.name}. See {log_path}.")



def save_dataframe(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)



def make_inventory_summary(inventory: pd.DataFrame) -> Dict[str, int]:
    return {
        "total_files": int(len(inventory)),
        "pdf_files": int((inventory["suffix"] == ".pdf").sum()),
        "python_files": int((inventory["suffix"] == ".py").sum()),
        "csv_files": int((inventory["suffix"] == ".csv").sum()),
    }



def top_groups(inventory: pd.DataFrame, n: int = 8) -> List[Tuple[str, int]]:
    counts = inventory["top_level_group"].value_counts().head(n)
    return [(str(idx), int(val)) for idx, val in counts.items()]



def counts_dict(df: pd.DataFrame, col: str) -> Dict[str, int]:
    vc = df[col].value_counts(dropna=False)
    return {str(k): int(v) for k, v in vc.items()}



def build_data_dictionary() -> pd.DataFrame:
    rows = [
        ("listing_id", "Integer identifier preserved from the archived dataset."),
        ("title", "Listing title."),
        ("price_chf", "Numeric listing price in CHF-equivalent form."),
        ("source_status", "Archived manual status, translated to English: POSITIVE, NEGATIVE, IDENTIFIED, or DETECTED."),
        ("ad_text", "Listing description text."),
        ("location", "Archived location string."),
        ("profile_creation_year", "Year the seller profile was created; missing when opaque or absent."),
        ("profile_creation_missing", "Binary indicator for missing profile creation year."),
        ("content_score", "Indicator score for content similarity or duplication: 1 unique, 2 similar, 3 duplicated."),
        ("price_score", "Indicator score for price anomaly: 1 market-consistent, 2 underpriced, 3 suspiciously low."),
        ("profile_score", "Indicator score for profile recency: 1 older, 2 intermediate or missing, 3 new."),
        ("fraud_index", "Summed indicator index used by the original project."),
        ("manual_state_code", "Archived intermediate code reflecting the manual state of the listing in the original project."),
        ("risk_target", "Binary operational target derived from the fraud index: 0 acceptable, 1 unfavorable."),
        ("content_band", "Human-readable band derived from content_score."),
        ("price_band", "Human-readable band derived from price_score."),
        ("profile_band", "Human-readable band derived from profile_score."),
        ("risk_band", "Human-readable band derived from the fraud index."),
        ("risk_target_label", "Text label for risk_target."),
        ("dataset", "Dataset origin within the compendium: exploratory_sample or case_study_sample."),
        ("market_price_chf", "Model-specific benchmark price used by the archived scripts."),
        ("price_ratio", "Derived ratio price_chf / market_price_chf."),
        ("confirmed_extreme", "Binary indicator for manually confirmed POSITIVE or NEGATIVE cases."),
        ("confirmed_positive", "Binary indicator for archived POSITIVE cases."),
        ("confirmed_negative", "Binary indicator for archived NEGATIVE cases."),
    ]
    return pd.DataFrame(rows, columns=["field", "description"])



def build_integrity_findings(theory_eval_orig, theory_eval_clean, case_eval, case_confirmed, theory_confirmed) -> pd.DataFrame:
    rows = [
        {
            "finding_id": 1,
            "title": "Confusion-matrix tables in the thesis swap false positives and false negatives.",
            "severity": "moderate",
            "evidence": f"Exploratory reproduced confusion matrix is TN={theory_eval_orig.tn}, FP={theory_eval_orig.fp}, FN={theory_eval_orig.fn}, TP={theory_eval_orig.tp}; case-study reproduced confusion matrix is TN={case_eval.tn}, FP={case_eval.fp}, FN={case_eval.fn}, TP={case_eval.tp}.",
            "impact": "Narrative metric values remain reproducible, but the published confusion tables are not internally consistent.",
            "action_taken_in_compendium": "Corrected values reported in the audit and linked back to the archived scripts.",
        },
        {
            "finding_id": 2,
            "title": "The exploratory random-forest script uses a manual-state predictor that is not deployment-available.",
            "severity": "moderate",
            "evidence": f"Original exploratory accuracy = {theory_eval_orig.accuracy:.3f}; clean rerun without manual-state feature = {theory_eval_clean.accuracy:.3f}.",
            "impact": "The original exploratory classifier is not a fully clean operational benchmark.",
            "action_taken_in_compendium": "Both the original and clean reruns are reported side by side.",
        },
        {
            "finding_id": 3,
            "title": "Archived scripts contain early similarity routines that compare each text to itself.",
            "severity": "high",
            "evidence": "Functions named calculate_statistics_with_jaccard or calculate_similarity_jaccard in early scripts compute Jaccard similarity row-to-same-row, producing trivial 1.0 scores.",
            "impact": "Those scripts are unsuitable as evidence of between-listing similarity.",
            "action_taken_in_compendium": "Excluded from the final analysis pipeline and documented in the audit.",
        },
        {
            "finding_id": 4,
            "title": "Legacy scraper files embed login credentials and should never be redistributed operationally.",
            "severity": "critical",
            "evidence": "Credential-bearing scraper files were found in the source archive and deliberately excluded from the final package.",
            "impact": "Unsafe for reuse and inconsistent with good research-data security practice.",
            "action_taken_in_compendium": "Only sanitised canonical data are shipped; no live scraper code is included.",
        },
        {
            "finding_id": 5,
            "title": "Predictive performance refers primarily to an internal risk target, not universal judicial truth.",
            "severity": "moderate",
            "evidence": f"Case-study risk-target classifier AUC = {case_eval.auc:.3f}; confirmed-extremes subset AUC = {case_confirmed.auc:.3f}.",
            "impact": "Metrics are best interpreted as consistency with the actionable fraud index rather than as final fraud adjudication accuracy.",
            "action_taken_in_compendium": "The article and audit explicitly distinguish the operational target from confirmed fraud labels.",
        },
        {
            "finding_id": 6,
            "title": "Despite version drift, the archive remains strong enough for a documented reconstruction.",
            "severity": "low",
            "evidence": f"Exploratory confirmed-extremes subset AUC = {theory_confirmed.auc:.3f}; case-study main AUC = {case_eval.auc:.3f} after canonicalisation.",
            "impact": "The research basis is usable when provenance and canonicalisation are made explicit.",
            "action_taken_in_compendium": "Canonical files, discrepancy tables, and source inventory are bundled in the package.",
        },
    ]
    return pd.DataFrame(rows)



def build_readme() -> str:
    return """# MAS LCE final research compendium\n\nThis package reconstructs the David Graz MAS LCE project on fraudulent online classified ads as a self-contained English compendium.\n\n## Main files\n\n- `reports/final_article.pdf` - article-style English redesign of the thesis\n- `reports/integrity_audit.pdf` - reproducibility and integrity audit\n- `reports/project_guide.pdf` - package guide and data dictionary\n- `data/canonical/` - sanitised canonical datasets\n- `data/metadata/` - source inventory, manifest, checksums, discrepancy tables\n- `scripts/build_all.py` - Python-only build entry point\n\n## Rebuild\n\n```bash\npython scripts/build_all.py --use-packaged-data\n```\n\nIf you have the original extracted `_Master_LCE_Docs` source tree, you can also rebuild from source:\n\n```bash\npython scripts/build_all.py --source-root /path/to/_Master_LCE_Docs\n```\n\nThe package intentionally excludes unsafe legacy scraper code and relies only on archived, sanitised data for reproduction.\n"""



def build_manifest(package_root: Path) -> pd.DataFrame:
    rows = []
    for path in sorted(package_root.rglob("*")):
        if path.is_file() and path.name not in {"manifest.csv", "checksums.sha256"}:
            rows.append({
                "relative_path": rel(path, package_root),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            })
    return pd.DataFrame(rows)



def write_checksums(manifest: pd.DataFrame, out_path: Path) -> None:
    lines = [f"{row.sha256}  {row.relative_path}" for row in manifest.itertuples(index=False)]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")



def prepare_context(theory_df: pd.DataFrame, case_df: pd.DataFrame, inventory: pd.DataFrame, evaluations: Dict[str, object], discrepancy_tables: List[pd.DataFrame], report_paths: Dict[str, str]) -> Dict:
    inventory_sum = make_inventory_summary(inventory)
    theory_status = counts_dict(theory_df, "source_status")
    case_status = counts_dict(case_df, "source_status")
    theory_target = {
        "acceptable": int((theory_df["risk_target"] == 0).sum()),
        "unfavorable": int((theory_df["risk_target"] == 1).sum()),
    }
    case_target = {
        "acceptable": int((case_df["risk_target"] == 0).sum()),
        "unfavorable": int((case_df["risk_target"] == 1).sum()),
    }
    discrepancies = pd.concat(discrepancy_tables, ignore_index=True)
    return {
        "theory": {"n_rows": len(theory_df), "status_counts": theory_status, "target_counts": theory_target},
        "case": {"n_rows": len(case_df), "status_counts": case_status, "target_counts": case_target},
        "evaluations": {k: v.as_dict() for k, v in evaluations.items()},
        "inventory_summary": inventory_sum,
        "inventory_top_groups": top_groups(inventory),
        "discrepancies": discrepancies.to_dict(orient="records"),
        "report_paths": report_paths,
    }



def main() -> None:
    args = parse_args()

    data_canonical_dir = ensure_dir(PACKAGE_ROOT / "data" / "canonical")
    data_tables_dir = ensure_dir(PACKAGE_ROOT / "data" / "tables")
    data_json_dir = ensure_dir(PACKAGE_ROOT / "data" / "json")
    data_metadata_dir = ensure_dir(PACKAGE_ROOT / "data" / "metadata")
    figures_dir = ensure_dir(PACKAGE_ROOT / "figures")
    reports_dir = ensure_dir(PACKAGE_ROOT / "reports")
    docs_dir = ensure_dir(PACKAGE_ROOT / "docs")

    if args.use_packaged_data:
        theory_canonical = pd.read_csv(data_canonical_dir / "exploratory_sample_canonical.csv")
        case_canonical = pd.read_csv(data_canonical_dir / "case_study_sample_canonical.csv")
        inventory = pd.read_csv(data_metadata_dir / "source_inventory.csv")
        discrepancy_theory = pd.read_csv(data_tables_dir / "theory_version_differences.csv")
        discrepancy_case = pd.read_csv(data_tables_dir / "case_version_differences.csv")
    else:
        source_root = args.source_root or source_root_from_default()
        key_paths = get_key_source_paths(source_root)

        # Canonical datasets from authoritative archived files.
        theory_raw = load_raw_csv(key_paths["theory_dataset"])
        case_raw = load_raw_csv(key_paths["case_dataset"])
        theory_canonical = canonicalize_dataset(theory_raw, "exploratory_sample")
        case_canonical = canonicalize_dataset(case_raw, "case_study_sample")
        save_dataframe(theory_canonical, data_canonical_dir / "exploratory_sample_canonical.csv")
        save_dataframe(case_canonical, data_canonical_dir / "case_study_sample_canonical.csv")

        # Alternate versions for discrepancy analysis.
        theory_alt = load_raw_csv(key_paths["theory_original_alt"])
        case_alt = load_raw_csv(key_paths["case_annex_alt"])
        discrepancy_theory = compare_versions(theory_raw, theory_alt, "exploratory_root_scripts_vs_canonical")
        discrepancy_case = compare_versions(case_raw, case_alt, "case_annex_vs_canonical")
        save_dataframe(discrepancy_theory, data_tables_dir / "theory_version_differences.csv")
        save_dataframe(discrepancy_case, data_tables_dir / "case_version_differences.csv")

        inventory = build_source_inventory(source_root, key_paths)
        save_dataframe(inventory, data_metadata_dir / "source_inventory.csv")

    # Shared metadata.
    save_dataframe(build_data_dictionary(), data_metadata_dir / "data_dictionary.csv")
    save_dataframe(build_qualitative_themes(), data_tables_dir / "qualitative_themes.csv")

    # Descriptive tables.
    save_dataframe(status_summary(theory_canonical), data_tables_dir / "exploratory_status_summary.csv")
    save_dataframe(status_summary(case_canonical), data_tables_dir / "case_status_summary.csv")
    save_dataframe(risk_summary(theory_canonical), data_tables_dir / "exploratory_risk_summary.csv")
    save_dataframe(risk_summary(case_canonical), data_tables_dir / "case_risk_summary.csv")
    save_dataframe(confirmed_summary(theory_canonical), data_tables_dir / "exploratory_confirmed_summary.csv")
    save_dataframe(confirmed_summary(case_canonical), data_tables_dir / "case_confirmed_summary.csv")

    theory_indicator = indicator_distribution(theory_canonical, "exploratory_sample")
    case_indicator = indicator_distribution(case_canonical, "case_study_sample")
    save_dataframe(theory_indicator, data_tables_dir / "exploratory_indicator_distribution.csv")
    save_dataframe(case_indicator, data_tables_dir / "case_indicator_distribution.csv")

    # Model evaluations.
    theory_eval_orig, theory_fpr, theory_tpr, _ = evaluate_random_forest(theory_canonical, "exploratory_sample", True, "exploratory_original_script")
    theory_eval_clean, theory_fpr_clean, theory_tpr_clean, _ = evaluate_random_forest(theory_canonical, "exploratory_sample", False, "exploratory_clean_rerun")
    case_eval, case_fpr, case_tpr, _ = evaluate_random_forest(case_canonical, "case_study_sample", False, "case_study_original_script")
    theory_confirmed = evaluate_confirmed_extremes(theory_canonical, "exploratory_sample")
    case_confirmed = evaluate_confirmed_extremes(case_canonical, "case_study_sample")
    evaluations = {
        "theory_original": theory_eval_orig,
        "theory_clean": theory_eval_clean,
        "case_original": case_eval,
        "theory_confirmed_subset": theory_confirmed,
        "case_confirmed_subset": case_confirmed,
    }
    metrics_df = metrics_dataframe(evaluations.values())
    save_dataframe(metrics_df, data_tables_dir / "reproduced_metrics.csv")

    integrity_findings = build_integrity_findings(theory_eval_orig, theory_eval_clean, case_eval, case_confirmed, theory_confirmed)
    save_dataframe(integrity_findings, data_tables_dir / "integrity_findings.csv")

    # Figures.
    plot_workflow(figures_dir / "workflow_overview.pdf")
    plot_workflow(figures_dir / "workflow_overview.png")
    plot_roc_curves(figures_dir / "roc_curves.pdf", (theory_fpr, theory_tpr), (case_fpr, case_tpr), theory_eval_orig.auc, case_eval.auc)
    plot_roc_curves(figures_dir / "roc_curves.png", (theory_fpr, theory_tpr), (case_fpr, case_tpr), theory_eval_orig.auc, case_eval.auc)
    plot_indicator_distribution(figures_dir / "case_indicator_distribution.pdf", case_indicator, "case_study_sample")
    plot_indicator_distribution(figures_dir / "case_indicator_distribution.png", case_indicator, "case_study_sample")
    plot_indicator_distribution(figures_dir / "exploratory_indicator_distribution.pdf", theory_indicator, "exploratory_sample")
    plot_indicator_distribution(figures_dir / "exploratory_indicator_distribution.png", theory_indicator, "exploratory_sample")

    # Context and JSON summaries.
    report_paths = {
        "workflow_fig": "../figures/workflow_overview.pdf",
        "roc_fig": "../figures/roc_curves.pdf",
        "case_indicator_fig": "../figures/case_indicator_distribution.pdf",
    }
    context = prepare_context(theory_canonical, case_canonical, inventory, evaluations, [discrepancy_theory, discrepancy_case], report_paths)
    write_json(data_json_dir / "context.json", context)

    # Reports.
    article_tex = build_article_tex(context)
    audit_tex = build_audit_tex(context)
    guide_tex = build_guide_tex(context)
    article_path = reports_dir / "final_article.tex"
    audit_path = reports_dir / "integrity_audit.tex"
    guide_path = reports_dir / "project_guide.tex"
    write_text(article_path, article_tex)
    write_text(audit_path, audit_tex)
    write_text(guide_path, guide_tex)
    compile_latex(article_path)
    compile_latex(audit_path)
    compile_latex(guide_path)

    # README and notes.
    write_text(PACKAGE_ROOT / "README.md", build_readme())
    write_text(
        docs_dir / "canonicalisation_note.txt",
        "The final compendium uses Scripts/ILCE_etude_de_cas/ILCE_etude_de_cas.csv as the exploratory canonical dataset and Scripts/ILCE_fausses_petites_annonces_2/ILCE_fausses_petites_annonces.csv as the case-study canonical dataset. Alternate copies are retained only through discrepancy tables.\n",
    )

    # Manifest and checksums.
    manifest = build_manifest(PACKAGE_ROOT)
    save_dataframe(manifest, data_metadata_dir / "manifest.csv")
    write_checksums(manifest, data_metadata_dir / "checksums.sha256")

    print("Build completed successfully.")
    print(f"Reports written to: {reports_dir}")


if __name__ == "__main__":
    main()
