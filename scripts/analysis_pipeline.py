from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    auc,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from helpers import decode_u_escape_name, rel, sha256_file


STATUS_TRANSLATION = {
    "POSITIF": "POSITIVE",
    "POSITIVE": "POSITIVE",
    "NEGATIVE": "NEGATIVE",
    "IDENTIFIED": "IDENTIFIED",
    "DETECTED": "DETECTED",
    "DETECTER": "DETECTED",
}

CONTENT_BANDS = {1: "unique", 2: "similar", 3: "duplicated"}
PRICE_BANDS = {1: "market-consistent", 2: "underpriced", 3: "suspiciously-low"}
PROFILE_BANDS = {1: "older-profile", 2: "intermediate-or-missing", 3: "new-profile"}
RISK_TARGET = {0: "acceptable", 1: "unfavorable"}
RISK_BANDS = {
    0: "legitimate",
    1: "low",
    2: "low",
    3: "low",
    4: "borderline",
    5: "borderline",
    6: "marked",
    7: "marked",
    8: "marked",
    9: "high",
    10: "fraud-confirmed",
}


@dataclass
class ModelEvaluation:
    name: str
    dataset: str
    n_rows: int
    class_0: int
    class_1: int
    tn: int
    fp: int
    fn: int
    tp: int
    accuracy: float
    precision: float
    recall: float
    f1: float
    specificity: float
    auc: float

    def as_dict(self) -> Dict[str, float | int | str]:
        return {
            "evaluation": self.name,
            "dataset": self.dataset,
            "n_rows": self.n_rows,
            "class_0": self.class_0,
            "class_1": self.class_1,
            "tn": self.tn,
            "fp": self.fp,
            "fn": self.fn,
            "tp": self.tp,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "specificity": self.specificity,
            "auc": self.auc,
        }


def get_key_source_paths(source_root: Path) -> Dict[str, Path]:
    return {
        "ratification": source_root / "Demande de ratification TM 2023-24 - Graz David.pdf",
        "thesis": source_root / "Master_LCE_David-Graz.pdf",
        "slides": source_root / "Master_LCE_Soutenance_David-Graz.pdf",
        "qualitative_analysis": source_root / "Annexes_12" / "Analyse th#U00e9matique.odt",
        "theory_dataset": source_root / "Scripts" / "ILCE_etude_de_cas" / "ILCE_etude_de_cas.csv",
        "theory_original_alt": source_root / "Scripts" / "ILCE_fausses_petites_annonces.csv",
        "case_dataset": source_root / "Scripts" / "ILCE_fausses_petites_annonces_2" / "ILCE_fausses_petites_annonces.csv",
        "case_annex_alt": source_root / "Annexes_12" / "Annexe_12-10.csv",
        "theory_script": source_root / "Scripts" / "ILCE_etude_de_cas" / "sc_random_forest.py",
        "case_script": source_root / "Scripts" / "ILCE_fausses_petites_annonces_2" / "random_forest.py",
    }


def _normalize_status(value: object) -> str:
    text = "" if pd.isna(value) else str(value).strip()
    return STATUS_TRANSLATION.get(text, text or "UNKNOWN")



def _market_price(title: str) -> int:
    title_l = (title or "").lower()
    if "iphone 13" in title_l:
        return 750
    if "iphone 14" in title_l:
        return 850
    if "iphone 15" in title_l:
        return 1200
    return 400



def load_raw_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=";")



def canonicalize_dataset(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    canonical = pd.DataFrame()
    canonical["listing_id"] = df["ID"].astype(int)
    canonical["title"] = df["TITRE"].fillna("").astype(str)
    canonical["price_chf"] = pd.to_numeric(df["PRIX"], errors="coerce")
    canonical["source_status"] = df["ETAT"].map(_normalize_status)
    canonical["ad_text"] = df["ANNONCE"].fillna("").astype(str)
    canonical["location"] = df["LIEU"].fillna("").astype(str)

    profile_year = pd.to_numeric(df["PROFILE_CREATION"], errors="coerce")
    # In the exploratory files, 0 encodes missing or anonymous profiles.
    profile_year = profile_year.replace({0: np.nan})
    canonical["profile_creation_year"] = profile_year
    canonical["profile_creation_missing"] = canonical["profile_creation_year"].isna().astype(int)

    canonical["content_score"] = pd.to_numeric(df["MA_ANNONCE"], errors="coerce")
    canonical["price_score"] = pd.to_numeric(df["MA_PRIX"], errors="coerce")
    canonical["profile_score"] = pd.to_numeric(df["MA_PROFIL"], errors="coerce")
    canonical["fraud_index"] = pd.to_numeric(df["MA_DANGER"], errors="coerce")
    canonical["manual_state_code"] = pd.to_numeric(df["MA_ETAT"], errors="coerce")
    canonical["risk_target"] = pd.to_numeric(df["MA_CIBLE"], errors="coerce").astype("Int64")

    canonical["content_band"] = canonical["content_score"].map(CONTENT_BANDS)
    canonical["price_band"] = canonical["price_score"].map(PRICE_BANDS)
    canonical["profile_band"] = canonical["profile_score"].map(PROFILE_BANDS)
    canonical["risk_band"] = canonical["fraud_index"].map(RISK_BANDS)
    canonical["risk_target_label"] = canonical["risk_target"].map(RISK_TARGET)
    canonical["dataset"] = dataset_name

    canonical["market_price_chf"] = canonical["title"].map(_market_price)
    canonical["price_ratio"] = canonical["price_chf"] / canonical["market_price_chf"]

    canonical["confirmed_extreme"] = canonical["source_status"].isin(["POSITIVE", "NEGATIVE"]).astype(int)
    canonical["confirmed_positive"] = (canonical["source_status"] == "POSITIVE").astype(int)
    canonical["confirmed_negative"] = (canonical["source_status"] == "NEGATIVE").astype(int)

    return canonical



def build_source_inventory(source_root: Path, key_paths: Dict[str, Path]) -> pd.DataFrame:
    relevant_lookup = {path.resolve(): name for name, path in key_paths.items() if path.exists()}
    rows = []
    for path in sorted(source_root.rglob("*")):
        if not path.is_file():
            continue
        rel_path = decode_u_escape_name(rel(path, source_root))
        top_level = rel_path.split("/")[0]
        rows.append(
            {
                "relative_path": rel_path,
                "top_level_group": top_level,
                "suffix": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "directly_used": int(path.resolve() in relevant_lookup),
                "direct_use_label": relevant_lookup.get(path.resolve(), ""),
            }
        )
    return pd.DataFrame(rows)



def build_qualitative_themes() -> pd.DataFrame:
    rows = [
        {
            "theme_id": 1,
            "theme": "Fragmented responsibilities",
            "description": "Cybercrime enforcement is institutionally fragmented across cantons and between public and private actors.",
            "operational_relevance": "Detection tools must be understandable by multiple security actors and support coordination rather than a single central operator.",
            "source_basis": "Thematic analysis of six exploratory interviews",
        },
        {
            "theme_id": 2,
            "theme": "Recurring fraud indicators",
            "description": "Very low prices, recently created profiles, repetitive text, and unusual payment arrangements recur across interviews.",
            "operational_relevance": "These indicators anchor the actionable model and can be translated into scoring rules.",
            "source_basis": "Interview reports and thematic analysis",
        },
        {
            "theme_id": 3,
            "theme": "Absence of proactive tools",
            "description": "Practitioners describe a mostly reactive workflow in which platforms and police intervene after victims complain.",
            "operational_relevance": "A triage model is valuable if it works before victimization and does not depend on private platform data.",
            "source_basis": "Interview reports and thesis section 4.1",
        },
        {
            "theme_id": 4,
            "theme": "Transnational organised activity",
            "description": "Respondents link a share of fraudulent listings to transnational, adaptive, and organised networks.",
            "operational_relevance": "Local detection must be paired with broader coordination and intelligence sharing.",
            "source_basis": "Interview reports and thematic analysis",
        },
        {
            "theme_id": 5,
            "theme": "Prevention as leverage",
            "description": "Interviewees repeatedly stress awareness and prevention because many losses are individually small yet collectively large.",
            "operational_relevance": "The model can support public warning systems and platform-side warning labels.",
            "source_basis": "Interview reports and defense slides",
        },
        {
            "theme_id": 6,
            "theme": "Pessimism about trend evolution",
            "description": "Practitioners expect volume, automation, and complexity to increase faster than institutional adaptation.",
            "operational_relevance": "The model must remain updateable and embedded in a feedback loop.",
            "source_basis": "Thematic analysis and thesis discussion",
        },
        {
            "theme_id": 7,
            "theme": "Cooperation bottlenecks",
            "description": "Limited judicial cooperation and weak platform engagement constrain enforcement.",
            "operational_relevance": "Operational value lies in ecosystem-wide risk management, not only downstream prosecution.",
            "source_basis": "Interview reports and thesis discussion",
        },
    ]
    return pd.DataFrame(rows)



def status_summary(df: pd.DataFrame) -> pd.DataFrame:
    vc = df["source_status"].value_counts().rename_axis("source_status").reset_index(name="count")
    vc["share"] = vc["count"] / len(df)
    return vc.sort_values("source_status").reset_index(drop=True)



def risk_summary(df: pd.DataFrame) -> pd.DataFrame:
    vc = df["risk_target_label"].value_counts().rename_axis("risk_target_label").reset_index(name="count")
    vc["share"] = vc["count"] / len(df)
    return vc.sort_values("risk_target_label").reset_index(drop=True)



def confirmed_summary(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["source_status"].isin(["POSITIVE", "NEGATIVE"])
    vc = df.loc[mask, "source_status"].value_counts().rename_axis("confirmed_status").reset_index(name="count")
    vc["share_within_confirmed_extremes"] = vc["count"] / vc["count"].sum()
    return vc.sort_values("confirmed_status").reset_index(drop=True)



def indicator_distribution(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    subsets = {
        "All listings": pd.Series(True, index=df.index),
        "Acceptable risk": df["risk_target"] == 0,
        "Unfavorable risk": df["risk_target"] == 1,
        "Confirmed legitimate": df["source_status"] == "NEGATIVE",
        "Confirmed positive": df["source_status"] == "POSITIVE",
    }
    records: List[dict] = []
    for subset_name, mask in subsets.items():
        sub = df.loc[mask]
        total = len(sub)
        if total == 0:
            continue
        for col, label_map, pretty_name in [
            ("content_score", CONTENT_BANDS, "Content similarity"),
            ("price_score", PRICE_BANDS, "Price anomaly"),
            ("profile_score", PROFILE_BANDS, "Profile recency"),
        ]:
            counts = sub[col].value_counts().sort_index()
            for code, label in label_map.items():
                count = int(counts.get(code, 0))
                records.append(
                    {
                        "dataset": dataset_name,
                        "subset": subset_name,
                        "indicator": pretty_name,
                        "code": code,
                        "label": label,
                        "count": count,
                        "share": count / total,
                    }
                )
    return pd.DataFrame(records)



def compare_versions(base_df: pd.DataFrame, other_df: pd.DataFrame, version_name: str) -> pd.DataFrame:
    base = base_df.sort_values("ID").reset_index(drop=True)
    other = other_df.sort_values("ID").reset_index(drop=True)
    merged = base.merge(other, on="ID", suffixes=("_base", "_other"))
    checks = [
        "ETAT",
        "MA_ANNONCE",
        "MA_PRIX",
        "MA_PROFIL",
        "MA_DANGER",
        "MA_ETAT",
        "MA_CIBLE",
    ]
    rows = []
    for col in checks:
        left = merged[f"{col}_base"]
        right = merged[f"{col}_other"]
        diff_mask = left.fillna("<NA>") != right.fillna("<NA>")
        rows.append(
            {
                "comparison": version_name,
                "field": col,
                "difference_count": int(diff_mask.sum()),
                "base_example": "",
                "other_example": "",
            }
        )
        if diff_mask.any():
            idx = diff_mask.idxmax()
            rows[-1]["base_example"] = str(left.loc[idx])
            rows[-1]["other_example"] = str(right.loc[idx])
    return pd.DataFrame(rows)



def _build_model_matrix(df: pd.DataFrame, include_manual_state: bool) -> Tuple[pd.DataFrame, pd.Series, ColumnTransformer]:
    work = df.copy()
    work["ad_text"] = work["ad_text"].fillna("")
    work["profile_creation_year_model"] = work["profile_creation_year"].fillna(2023)

    features = ["ad_text", "price_chf", "price_ratio", "profile_creation_year_model"]
    numeric_features = ["price_chf", "price_ratio", "profile_creation_year_model"]
    if include_manual_state:
        work["manual_state_code"] = work["manual_state_code"].fillna(2)
        features.append("manual_state_code")
        numeric_features.append("manual_state_code")

    X = work[features]
    y = work["risk_target"].astype(int)

    preprocessor = ColumnTransformer(
        transformers=[
            ("tfidf", TfidfVectorizer(max_features=100), "ad_text"),
            (
                "num",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="mean")),
                    ("scaler", StandardScaler()),
                ]),
                numeric_features,
            ),
        ]
    )
    return X, y, preprocessor



def evaluate_random_forest(df: pd.DataFrame, dataset_label: str, include_manual_state: bool, evaluation_name: str) -> Tuple[ModelEvaluation, np.ndarray, np.ndarray, np.ndarray]:
    X, y, preprocessor = _build_model_matrix(df, include_manual_state)
    pipeline = Pipeline(
        [
            ("preprocessing", preprocessor),
            ("classification", RandomForestClassifier(n_estimators=100, random_state=42)),
        ]
    )
    splitter = StratifiedKFold(n_splits=5)
    y_pred = cross_val_predict(pipeline, X, y, cv=splitter)
    y_prob = cross_val_predict(pipeline, X, y, cv=splitter, method="predict_proba")[:, 1]
    cm = confusion_matrix(y, y_pred, labels=[0, 1])
    tn, fp, fn, tp = [int(v) for v in cm.ravel()]
    fpr, tpr, _ = roc_curve(y, y_prob)
    evaluation = ModelEvaluation(
        name=evaluation_name,
        dataset=dataset_label,
        n_rows=len(df),
        class_0=int((y == 0).sum()),
        class_1=int((y == 1).sum()),
        tn=tn,
        fp=fp,
        fn=fn,
        tp=tp,
        accuracy=float(accuracy_score(y, y_pred)),
        precision=float(precision_score(y, y_pred, zero_division=0)),
        recall=float(recall_score(y, y_pred, zero_division=0)),
        f1=float(f1_score(y, y_pred, zero_division=0)),
        specificity=float(tn / (tn + fp)),
        auc=float(auc(fpr, tpr)),
    )
    return evaluation, fpr, tpr, y_pred



def evaluate_confirmed_extremes(df: pd.DataFrame, dataset_label: str) -> ModelEvaluation:
    subset = df[df["source_status"].isin(["POSITIVE", "NEGATIVE"])].copy()
    subset["confirmed_target"] = (subset["source_status"] == "POSITIVE").astype(int)
    subset["ad_text"] = subset["ad_text"].fillna("")
    subset["profile_creation_year_model"] = subset["profile_creation_year"].fillna(2023)
    X = subset[["ad_text", "price_chf", "price_ratio", "profile_creation_year_model"]]
    y = subset["confirmed_target"]
    preprocessor = ColumnTransformer(
        transformers=[
            ("tfidf", TfidfVectorizer(max_features=100), "ad_text"),
            (
                "num",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="mean")),
                    ("scaler", StandardScaler()),
                ]),
                ["price_chf", "price_ratio", "profile_creation_year_model"],
            ),
        ]
    )
    pipeline = Pipeline(
        [
            ("preprocessing", preprocessor),
            ("classification", RandomForestClassifier(n_estimators=100, random_state=42)),
        ]
    )
    splitter = StratifiedKFold(n_splits=5)
    y_pred = cross_val_predict(pipeline, X, y, cv=splitter)
    y_prob = cross_val_predict(pipeline, X, y, cv=splitter, method="predict_proba")[:, 1]
    cm = confusion_matrix(y, y_pred, labels=[0, 1])
    tn, fp, fn, tp = [int(v) for v in cm.ravel()]
    fpr, tpr, _ = roc_curve(y, y_prob)
    return ModelEvaluation(
        name="confirmed_subset_validation",
        dataset=dataset_label,
        n_rows=len(subset),
        class_0=int((y == 0).sum()),
        class_1=int((y == 1).sum()),
        tn=tn,
        fp=fp,
        fn=fn,
        tp=tp,
        accuracy=float(accuracy_score(y, y_pred)),
        precision=float(precision_score(y, y_pred, zero_division=0)),
        recall=float(recall_score(y, y_pred, zero_division=0)),
        f1=float(f1_score(y, y_pred, zero_division=0)),
        specificity=float(tn / (tn + fp)),
        auc=float(auc(fpr, tpr)),
    )



def plot_workflow(output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")

    boxes = [
        (0.4, 3.0, 2.4, 1.1, "Project corpus\n(thesis, slides, scripts, data, interviews)"),
        (3.3, 3.0, 2.4, 1.1, "Canonicalization\n(version control, sanitisation, inventory)"),
        (6.2, 3.0, 1.4, 1.1, "Exploratory\nsample\n(n=315)"),
        (7.9, 3.0, 1.4, 1.1, "Case-study\nsample\n(n=2,166)"),
        (3.3, 1.0, 2.4, 1.1, "Python-only reproduction\nfigures, tables, metrics"),
        (6.2, 1.0, 3.1, 1.1, "Deliverables\narticle, audit, guide, manifest, checksums"),
    ]
    for x, y, w, h, label in boxes:
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.04", linewidth=1.2, edgecolor="#30465a", facecolor="#eaf1f7")
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=10)

    arrows = [
        ((2.8, 3.55), (3.3, 3.55)),
        ((5.7, 3.55), (6.2, 3.55)),
        ((7.6, 3.55), (7.9, 3.55)),
        ((4.5, 3.0), (4.5, 2.1)),
        ((5.7, 1.55), (6.2, 1.55)),
    ]
    for (x1, y1), (x2, y2) in arrows:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=1.4, color="#30465a"))

    ax.text(0.4, 4.55, "Research-compendium workflow", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)



def plot_roc_curves(output_path: Path, theory_curve: Tuple[np.ndarray, np.ndarray], case_curve: Tuple[np.ndarray, np.ndarray], theory_auc: float, case_auc: float) -> None:
    fig, ax = plt.subplots(figsize=(6.6, 5.0))
    ax.plot(theory_curve[0], theory_curve[1], lw=2, label=f"Exploratory sample (AUC = {theory_auc:.3f})")
    ax.plot(case_curve[0], case_curve[1], lw=2, label=f"Case-study sample (AUC = {case_auc:.3f})")
    ax.plot([0, 1], [0, 1], linestyle="--", color="0.4", lw=1)
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title("Reproduced ROC curves")
    ax.legend(frameon=False, loc="lower right")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)



def plot_indicator_distribution(output_path: Path, distribution_df: pd.DataFrame, dataset_name: str) -> None:
    subset_order = ["Acceptable risk", "Unfavorable risk", "Confirmed legitimate", "Confirmed positive"]
    indicator_order = ["Price anomaly", "Content similarity", "Profile recency"]
    fig, axes = plt.subplots(1, 3, figsize=(12.2, 4.4), sharey=True)
    palette = ["#d7e3f1", "#84a9cf", "#2f6690"]

    for ax, indicator in zip(axes, indicator_order):
        pivot = (
            distribution_df[(distribution_df["dataset"] == dataset_name) & (distribution_df["subset"].isin(subset_order)) & (distribution_df["indicator"] == indicator)]
            .pivot(index="subset", columns="label", values="share")
            .reindex(subset_order)
            .fillna(0)
        )
        cols = list(pivot.columns)
        bottom = np.zeros(len(pivot))
        for color, col in zip(palette, cols):
            values = pivot[col].to_numpy()
            ax.barh(pivot.index, values, left=bottom, color=color, edgecolor="white", label=col)
            bottom += values
        ax.set_title(indicator)
        ax.set_xlim(0, 1)
        ax.grid(axis="x", alpha=0.2)
        if ax is axes[0]:
            ax.set_ylabel("")
    handles, labels = axes[-1].get_legend_handles_labels()
    # deduplicate while preserving order
    seen = []
    h_final, l_final = [], []
    for h, l in zip(handles, labels):
        if l not in seen:
            seen.append(l)
            h_final.append(h)
            l_final.append(l)
    fig.legend(h_final, l_final, frameon=False, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle(f"Indicator composition by subset: {dataset_name.replace('-', ' ').title()}")
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)



def metrics_dataframe(evaluations: Iterable[ModelEvaluation]) -> pd.DataFrame:
    return pd.DataFrame([ev.as_dict() for ev in evaluations])
