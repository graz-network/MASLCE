## 1. Project Overview

This repository provides a **complete, reproducible synthesis** of the MAS LCE (Master of Advanced Studies in Economic Crime Investigation) research project conducted by David Graz.

The project addresses the following central research problem:

> **How can fraudulent online classified advertisements be detected proactively using transparent, auditable, and operationally meaningful indicators?**

The compendium consolidates:

* the original thesis,
* supporting datasets,
* analytical scripts,
* reconstructed results,
* and publication-ready outputs.

It is designed to be:

* **self-understandable**
* **fully reproducible**
* **audit-ready**
* **usable by practitioners in economic crime and cybercrime**

---

## 2. Core Contribution

The main contribution of the research is the development of:

> **An actionable model for proactive fraud detection based on transparent indicators rather than opaque black-box systems.**

The model relies on three operational indicators:

* **Content similarity** (duplicate or template-based fraud)
* **Price anomaly** (underpricing relative to market value)
* **Profile recency** (new or anonymous seller profiles)

These indicators are combined into a **fraud risk index** used for:

* early detection,
* prioritization,
* and preventive intervention.

---

## 3. Repository Structure

```
final_master_lce_compendium/
│
├── reports/
│   ├── final_article.pdf              # Article-style reconstruction
│   ├── final_article.tex
│   ├── integrity_audit.pdf           # Reproducibility & integrity analysis
│   ├── integrity_audit.tex
│   ├── project_guide.pdf             # User and replication guide
│   ├── project_guide.tex
│
├── scripts/
│   ├── analysis_pipeline.py          # Main reproducibility pipeline
│   ├── compile_latex.py              # LaTeX → PDF builder
│   ├── legacy_econometric/           # Original thesis scripts (traceability)
│
├── data/
│   ├── canonical/                   # Cleaned datasets used in analysis
│   ├── raw/                         # Original datasets (if included)
│   ├── data_dictionary.csv          # Variable definitions
│
├── outputs/
│   ├── tables/                      # Reproduced tables
│   ├── figures/                     # ROC curves, distributions, workflow
│
├── sources/
│   ├── Master_LCE_David-Graz.pdf
│   ├── Master_LCE_Soutenance_David-Graz.pdf
│   ├── Demande_de_ratification.pdf
│
├── MANIFEST.csv                     # File inventory
├── CHECKSUMS.sha256                 # Integrity verification
└── README.md                        # This file
```

---

## 4. Research Design

### 4.1 Methodological Approach

The research follows a **mixed-method design**:

#### 1. Qualitative phase

* 6 expert interviews (law enforcement, analysts, practitioners)
* Thematic analysis
* Identification of recurring fraud indicators

#### 2. Exploratory quantitative phase

* Dataset: ~315 listings
* Development of indicator-based scoring model

#### 3. Case-study validation phase

* Dataset: ~2,166 listings
* Application and evaluation of the model

---

### 4.2 Theoretical Framework

The model is based on the principle:

> **All criminal activity produces observable traces that can be systematically identified.**

Fraudulent listings exhibit detectable signals:

* textual patterns,
* price inconsistencies,
* behavioral anomalies.

---

## 5. Data Description

### Key datasets

| Dataset            | Description                       |
| ------------------ | --------------------------------- |
| Exploratory sample | Initial model development         |
| Case-study sample  | Model validation                  |
| Canonical datasets | Cleaned and standardized versions |

### Key variables

* `content_score` -> similarity of listing text
* `price_score` -> deviation from expected market price
* `profile_score` -> seller account age
* `fraud_index` -> combined risk score
* `risk_target` -> binary classification (acceptable / unfavorable)

---

## 6. Analytical Pipeline

The full analysis is implemented in:

```
scripts/analysis_pipeline.py
```

### Pipeline steps:

1. Load raw data
2. Canonicalize datasets
3. Generate derived features
4. Produce descriptive statistics
5. Train Random Forest model
6. Evaluate performance:

   * Accuracy
   * Precision / Recall
   * F1 score
   * ROC-AUC
7. Generate figures and tables

---

## 7. Model Interpretation

The model is **not a proof of fraud**.

It is a:

> **risk triage tool**

It enables:

* early identification of suspicious listings
* prioritization of investigative resources
* preventive interventions

---

## 8. Reproducibility

### Requirements

* Python >= 3.10
* Libraries:

  * pandas
  * numpy
  * scikit-learn
  * matplotlib

### Run the analysis

```bash
python scripts/analysis_pipeline.py
```

### Compile reports

```bash
python scripts/compile_latex.py reports/final_article.tex
```

---

## 9. Integrity and Audit

The project includes:

* Full file inventory (`MANIFEST.csv`)
* SHA256 checksums
* Explicit documentation of:

  * data transformations
  * model assumptions
  * inconsistencies in original archive

### Key audit findings

* Multiple dataset versions exist in the original archive
* Some confusion-matrix inconsistencies in thesis tables
* One variable (`manual_state_code`) may introduce bias if used improperly

---

## 10. Key Results

* Strong predictive performance on case-study dataset
* Robust detection of high-risk listings
* Clear separation between:

  * acceptable listings
  * high-risk / fraudulent listings

Most importantly:

> **The model remains interpretable and operationally usable.**

---

## 11. Implications

### 11.1 For Practice

* Enables **proactive fraud detection**
* Supports **platform moderation**
* Improves **law enforcement triage**

---

### 11.2 For Policy

* Highlights need for:

  * cross-border cooperation
  * platform accountability
  * preventive strategies

---

### 11.3 For Research

* Demonstrates value of:

  * hybrid qualitative + quantitative methods
  * interpretable models over black-box AI
  * reproducible research in economic crime

---

## 12. Limitations

* Dataset limited to specific platforms/products
* Market price estimation is simplified
* Model predicts **risk**, not confirmed fraud
* External validity requires further testing

---

## 13. Ethical Considerations

* Avoid false accusations
* Use model as decision-support tool only
* Ensure transparency and accountability
* Respect data privacy constraints

---

## 14. How to Use This Project

This compendium can be used for:

* academic evaluation
* replication studies
* operational deployment (with adaptation)
* training and education in economic crime detection

---

## 15. Contact

**Author**: David Graz
**Project**: MAS LCE - Economic Crime Investigation

---

## 16. Final Note

This project demonstrates that:

> **Effective fraud detection does not require opaque AI systems, but rather well-designed, transparent, and auditable analytical frameworks grounded in real-world practice.**

---

If you want, I can also generate:

* a **short README version (1 page)** for GitHub
* or a **technical appendix README** focused only on replication and code
