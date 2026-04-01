from __future__ import annotations

from typing import Dict, List, Tuple

from helpers import latex_escape


def _p(v: float, digits: int = 3) -> str:
    return f"{v:.{digits}f}"


def _pct(v: float, digits: int = 1) -> str:
    return f"{v * 100:.{digits}f}\\%"


BASE_PREAMBLE = r"""
\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[margin=2.2cm]{geometry}
\usepackage{microtype}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{tabularx}
\usepackage{array}
\usepackage{float}
\usepackage{fancyhdr}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{setspace}
\usepackage{caption}
\usepackage{titlesec}
\usepackage{amsmath}
\usepackage{pdflscape}
\usepackage{verbatim}
\definecolor{accent}{HTML}{1F4E79}
\definecolor{soft}{HTML}{EAF1F7}
\definecolor{textgray}{HTML}{4D5966}
\hypersetup{colorlinks=true, linkcolor=accent, citecolor=accent, urlcolor=accent, pdftitle={MAS LCE project compendium}}
\pagestyle{fancy}
\fancyhf{}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0pt}
\setstretch{1.06}
\titleformat{\section}{\Large\bfseries\color{accent}}{\thesection}{0.6em}{}
\titleformat{\subsection}{\large\bfseries\color{accent}}{\thesubsection}{0.6em}{}
\captionsetup{font=small,labelfont=bf}
\setlength{\parskip}{0.5em}
\setlength{\parindent}{0pt}
"""


def _latex_rows(rows: List[Tuple[str, ...]]) -> str:
    return "\n".join([" & ".join(items) + r" \\" for items in rows])


def build_article_tex(context: Dict) -> str:
    theory = context["theory"]
    case = context["case"]
    eval_theory_orig = context["evaluations"]["theory_original"]
    eval_theory_clean = context["evaluations"]["theory_clean"]
    eval_case = context["evaluations"]["case_original"]
    file_count = context["inventory_summary"]["total_files"]
    workflow_fig = context["report_paths"]["workflow_fig"]
    roc_fig = context["report_paths"]["roc_fig"]
    indicator_fig = context["report_paths"]["case_indicator_fig"]

    theory_rows = _latex_rows(
        [
            ("Exploratory sample size", str(theory["n_rows"])),
            ("Exploratory acceptable risk", str(theory["target_counts"]["acceptable"])),
            ("Exploratory unfavorable risk", str(theory["target_counts"]["unfavorable"])),
            ("Case-study sample size", str(case["n_rows"])),
            ("Case-study acceptable risk", str(case["target_counts"]["acceptable"])),
            ("Case-study unfavorable risk", str(case["target_counts"]["unfavorable"])),
        ]
    )

    performance_rows = _latex_rows(
        [
            (
                "Exploratory sample (original script)",
                _p(eval_theory_orig["accuracy"]),
                _p(eval_theory_orig["precision"]),
                _p(eval_theory_orig["recall"]),
                _p(eval_theory_orig["f1"]),
                _p(eval_theory_orig["specificity"]),
                _p(eval_theory_orig["auc"]),
            ),
            (
                "Exploratory sample (clean rerun)",
                _p(eval_theory_clean["accuracy"]),
                _p(eval_theory_clean["precision"]),
                _p(eval_theory_clean["recall"]),
                _p(eval_theory_clean["f1"]),
                _p(eval_theory_clean["specificity"]),
                _p(eval_theory_clean["auc"]),
            ),
            (
                "Case-study sample (canonical script)",
                _p(eval_case["accuracy"]),
                _p(eval_case["precision"]),
                _p(eval_case["recall"]),
                _p(eval_case["f1"]),
                _p(eval_case["specificity"]),
                _p(eval_case["auc"]),
            ),
        ]
    )

    return BASE_PREAMBLE + rf"""
\begin{{document}}

{{\color{{accent}}\rule{{\textwidth}}{{1.2pt}}}}
\begin{{center}}
    {{\LARGE\bfseries Toward an Actionable Model for Proactive Detection of Fraudulent Online Classified Ads}}\\[0.4em]
    {{\large English article-style reconstruction of the David Graz MAS LCE project}}\\[0.8em]
    {{\normalsize Prepared from the archived MAS LCE project corpus and reproduced with a Python-only compendium}}\\[0.2em]
    {{\small March 2026}}
\end{{center}}
{{\color{{accent}}\rule{{\textwidth}}{{0.6pt}}}}

\section*{{Abstract}}
This article reconstructs and redesigns, in English and in article form, the 2024 MAS LCE master thesis by David Graz on the proactive detection of fraudulent online classified ads. The reconstructed study asks a practical operational question: how can suspicious listings be detected efficiently and reliably before they generate additional victims? The archived project combines a ratified research design, a completed thesis, defense slides, interview material, quantitative data files, scripts, and supporting literature. The underlying model operationalises three indicators---price anomaly, content similarity or duplication, and profile recency---within an actionable fraud index inspired by the actionable-knowledge framework of Avenier and Schmitt, Ribaux's indicia methodology, and Dupont's ecosystemic view of cybercrime. Reproduction required canonicalisation because multiple file versions coexist in the archive. Using the canonical exploratory sample ($n={theory['n_rows']}$) and the canonical case-study sample ($n={case['n_rows']}$), the compendium reproduces the thesis' descriptive counts and closely reproduces its predictive metrics. The case-study random-forest model reaches accuracy {_p(eval_case['accuracy'])}, precision {_p(eval_case['precision'])}, recall {_p(eval_case['recall'])}, specificity {_p(eval_case['specificity'])}, and AUC {_p(eval_case['auc'])}. The study's main contribution is therefore best understood as an operational triage model for index-based fraud risk, not as a final adjudicative classifier of legally proven fraud. Within that scope, the reconstructed research remains coherent and practically relevant.

\textbf{{Keywords:}} online classified ads; fraud detection; money mules; actionable knowledge; cybercrime; fraud risk indexing

\section{{Introduction}}
Fraudulent classified ads sit at the intersection of cyber-enabled fraud, digital consumer risk, and intelligence-led policing. In the original Graz study, the problem was framed around low-value but high-volume online fraud capable of recruiting money mules, facilitating phishing-like payment diversion, and eroding trust in e-commerce. The core question was operational rather than purely theoretical: how can fraudulent online listings be detected \emph{{efficiently}} and \emph{{reliably}}? The project proposed that three recurring signs---an implausibly low asking price, repeated or duplicated content, and recently created or opaque seller profiles---could be translated into an actionable model for proactive detection.

That proposition is consistent with three strands of literature. First, Avenier and Schmitt argue that research for action should transform dispersed practitioner know-how into knowledge that can guide decisions and intervention \cite{{avenier2007}}. Second, Ribaux treats traces and indicia as operational elements of investigation rather than passive remnants \cite{{ribaux2023}}. Third, Dupont's ecosystemic account of cybercrime highlights that online security is distributed across platforms, law enforcement, intermediaries, and users rather than monopolised by a single actor \cite{{dupont2024}}. The literature on classified-ad fraud and related scam ecosystems likewise points to unusually attractive offers, repeated content, weak profile credibility, and evasive payment practices as persistent red flags \cite{{alrousan2020, alzghoul2024, jacquart2021, mokhberi2024}}.

The purpose of the present reconstruction is twofold. First, it redesigns the original thesis as a concise article in English. Second, it anchors the study inside a reproducible research compendium that makes the quantitative evidence and its limitations explicit. The companion audit report documents the full integrity review; the present article focuses on the research argument and on the substantive findings that remain robust after canonicalisation.

\section{{Theoretical framing and model logic}}
The study's conceptual move is to reframe fraud detection as an actionable-knowledge problem. Rather than searching for a universal and static fraud signature, the project organises practitioner observations into a small set of operational indicators that can be scored, communicated, and revised. The three indicators are straightforward:
\begin{{enumerate}}[leftmargin=1.4em]
    \item \textbf{{Price anomaly}}: the lower the price relative to a market benchmark, the stronger the suspicion that the offer is strategically attractive rather than economically grounded.
    \item \textbf{{Content similarity or duplication}}: repeated textual patterns suggest mass publication, template reuse, or automated listing behaviour.
    \item \textbf{{Profile recency or opacity}}: missing or recently created profiles are interpreted as more suspicious than older, stable profiles.
\end{{enumerate}}

The original project translated these indicators into a fraud index and then into a binary operational target: \emph{{acceptable}} versus \emph{{unfavorable}} fraud risk. This is a key point for interpretation. The study does not claim that every unfavorable listing is proven fraud. Instead, it proposes an \emph{{index-based probability of fraud}} that can support triage, warning, and preventive intervention.

\begin{{figure}}[H]
    \centering
    \includegraphics[width=0.95\textwidth]{{{workflow_fig}}}
    \caption{{Workflow used in the final research compendium: source corpus, canonicalisation, quantitative reproduction, and final deliverables.}}
\end{{figure}}

\section{{Materials and methods}}
\subsection{{Source corpus and reconstruction strategy}}
The archived MAS LCE corpus is unusually rich for a master-level project. The compendium inventoried {file_count} files across scripts, interview materials, theory notes, quantitative data, diagrams, and literature. Not all bundled files were analytically equivalent: some were earlier drafts, some were later refinements, and some were obsolete or unsafe to reuse. Reconstruction therefore proceeded by identifying canonical files, sanitising sensitive material, and preserving a full source inventory.

\subsection{{Qualitative phase}}
The qualitative phase rests on six exploratory interviews with nine cybercrime practitioners from several francophone Swiss cantons. The original project used thematic analysis to convert practitioner observations into operational categories. Across the archived interview reports and thematic-analysis note, seven themes recur: fragmented responsibilities, recurring fraud indicators, the absence of proactive tools, the international dimension of the phenomenon, prevention as leverage, pessimism about trend evolution, and bottlenecks in cooperation.

\subsection{{Quantitative phase}}
Two canonical datasets were identified in the archive. The exploratory verification sample contains {theory['n_rows']} listings and focuses on suspicious iPhone listings gathered to test the theoretical model. The broader case-study sample contains {case['n_rows']} listings and serves as the main quantitative stress test. Table~\ref{{tab:data-sources}} summarises the reconstructed data basis.

\begin{{table}}[H]
\centering
\caption{{Canonical quantitative basis used in the reconstruction.}}
\label{{tab:data-sources}}
\begin{{tabularx}}{{0.78\textwidth}}{{p{{6.2cm}} X}}
\toprule
Item & Value \\
\midrule
{theory_rows}
\bottomrule
\end{{tabularx}}
\end{{table}}

The operational structure follows the original thesis. Price anomaly is scored against model-specific benchmark prices. Text similarity is represented through archived content scores derived from duplication logic. Profile recency is captured by the year of profile creation or by missingness when the platform exposed no usable profile age. These indicator scores are summed into a fraud index, which is then thresholded into acceptable versus unfavorable risk. The predictive stage uses a random-forest classifier with cross-validation to reproduce the archived model family.

\section{{Results}}
\subsection{{Descriptive reconstruction}}
The canonical exploratory sample reproduces the thesis' core descriptive totals: 114 detected listings, 80 identified listings, 7 manually negative listings, and 114 positive listings, alongside 34 acceptable-risk and 281 unfavorable-risk cases. The canonical case-study sample reproduces the broader stress-test totals: 1,546 detected listings, 259 identified listings, 343 negative listings, and 18 positive listings, alongside 1,015 acceptable-risk and 1,151 unfavorable-risk cases.

The qualitative and descriptive layers point in the same direction. Price anomalies cluster strongly in the unfavorable-risk group. Content duplication is common among suspicious listings. Older profiles are disproportionately associated with acceptable-risk cases, whereas newly created or intermediate profiles dominate the unfavorable-risk group. The case-study classifier reproduces the strongest and most publication-ready quantitative result in the thesis: high discrimination between acceptable and unfavorable risk categories.

\begin{{figure}}[H]
    \centering
    \includegraphics[width=0.80\textwidth]{{{roc_fig}}}
    \caption{{Cross-validated ROC curves reproduced from the canonical exploratory and case-study datasets.}}
\end{{figure}}

\begin{{figure}}[H]
    \centering
    \includegraphics[width=0.98\textwidth]{{{indicator_fig}}}
    \caption{{Indicator composition in the canonical case-study dataset. The confirmed-positive row uses the archive's manually confirmed positive cases only.}}
\end{{figure}}

\begin{{table}}[H]
\centering
\caption{{Reproduced predictive performance.}}
\begin{{tabularx}}{{\textwidth}}{{p{{4.6cm}} c c c c c c}}
\toprule
Evaluation & Accuracy & Precision & Recall & F1 & Specificity & AUC \\
\midrule
{performance_rows}
\bottomrule
\end{{tabularx}}
\end{{table}}

\section{{Discussion}}
Three points emerge from the reconstruction. First, the project's real innovation is not a novel machine-learning architecture; it is the operational formalisation of practitioner knowledge into a compact fraud index. That is what makes the model actionable. Second, the results support an ecosystemic interpretation of fraud prevention. Because responsibilities are distributed across platforms, police services, and users, the model is most valuable as a shared triage language rather than as a stand-alone enforcement tool. Third, the strongest quantitative results concern consistency with an internal risk target. This is still useful: a platform-side warning system or analyst triage queue often needs a calibrated suspicion index before it needs courtroom-grade proof.

The reconstructed study therefore converges on a practical message already visible in the interviews: low prices, repeated language, and weak profile credibility are jointly useful for proactive screening. At the same time, the model should be interpreted as a preventive-risk device, not as a substitute for case-by-case investigation.

\section{{Limitations}}
The reconstructed study remains bounded by the original design. The datasets are platform-specific and product-heavy, with iPhone listings playing a central role. The target variable is index-based, not a comprehensive archive of adjudicated fraud outcomes. Ground truth is strongest at the extremes---confirmed positives and confirmed negatives---and weakest in the large middle of detected or identified but not fully adjudicated listings. Finally, the project archive contains multiple data versions, which means that quantitative reproduction depends on selecting canonical files rather than treating every bundled copy as equivalent.

\section{{Conclusion}}
Reconstructed as an article and backed by a documented Python compendium, the Graz MAS LCE project offers a credible and practically relevant approach to proactive detection of fraudulent online classified ads. The evidence supports the usefulness of a three-indicator operational model built around price anomaly, content reuse, and profile recency. The broader lesson is methodological: in fast-moving cybercrime settings, operational value often comes from converting scattered practitioner knowledge into transparent, auditable, and updateable indices. Read in that way, the project succeeds. It provides a defensible starting point for a pilot deployment, while the companion integrity audit clarifies the data-governance and evaluation work still needed for stronger publication-grade claims.

\begin{{thebibliography}}{{99}}
\bibitem{{alrousan2020}} Al-Rousan, S., Abuhussein, A., Alsubaei, F., Collen, L., \& Shiva, S. (2020). Ads-Guard: Detecting scammers in online classified ads. \emph{{2020 IEEE Symposium Series on Computational Intelligence}}, 1492--1498.
\bibitem{{alzghoul2024}} Alzghoul, J. R., Abdallah, E. E., \& Al-khawaldeh, A. S. (2024). Fraud in online classified ads: Strategies, risks, and detection methods. \emph{{Journal of Applied Security Research, 19}}(1), 45--69.
\bibitem{{avenier2007}} Avenier, M.-J., \& Schmitt, C. (2007). \emph{{La construction de savoirs pour l'action}}. Paris: L'Harmattan.
\bibitem{{dupont2024}} Dupont, B. (2024). \emph{{La cybercriminalité: Approche écosystémique de l'espace numérique}}. Paris: Armand Colin.
\bibitem{{jacquart2021}} Jacquart, B., Schopfer, A., \& Rossy, Q. (2021). Mules financières: profils, recrutement et rôles de facilitateur pour les escroqueries aux fausses annonces. \emph{{Revue internationale de criminologie et de police technique et scientifique, 74}}(4), 409--426.
\bibitem{{mokhberi2024}} Mokhberi, A., Huang, Y., Humbert, G., Obada-Obieh, B., Mehrabi Koushki, M., \& Beznosov, K. (2024). Trust, privacy, and safety factors associated with decision making in P2P markets based on social networks. \emph{{Proceedings of the 2024 CHI Conference on Human Factors in Computing Systems}}, 1--25.
\bibitem{{ribaux2023}} Ribaux, O. (2023). \emph{{De la police scientifique à la traçologie: Le renseignement par la trace}}. Lausanne: PPUR.
\bibitem{{rossy2020}} Rossy, Q., \& Borisova, B. (2020). Escroqueries par Internet. In \emph{{Cybercrimes et enjeux technologiques: Contexte et perspectives}} (pp. 227--250).
\bibitem{{saumya2022}} Saumya, S., \& Singh, J. P. (2022). Spam review detection using LSTM autoencoder: An unsupervised approach. \emph{{Electronic Commerce Research, 22}}(1), 113--133.
\end{{thebibliography}}

\end{{document}}
"""


def build_audit_tex(context: Dict) -> str:
    theory = context["theory"]
    case = context["case"]
    inventory_summary = context["inventory_summary"]
    discrepancies = context["discrepancies"]
    eval_theory_orig = context["evaluations"]["theory_original"]
    eval_theory_clean = context["evaluations"]["theory_clean"]
    eval_case = context["evaluations"]["case_original"]
    eval_confirmed_case = context["evaluations"]["case_confirmed_subset"]
    eval_confirmed_theory = context["evaluations"]["theory_confirmed_subset"]

    top_group_rows = _latex_rows(
        [(latex_escape(name), str(count)) for name, count in context["inventory_top_groups"]]
    )

    discrepancy_rows = _latex_rows(
        [
            (
                latex_escape(str(row["comparison"])),
                latex_escape(str(row["field"])),
                str(int(row["difference_count"])),
                latex_escape(str(row["base_example"])),
                latex_escape(str(row["other_example"])),
            )
            for row in discrepancies
        ]
    )

    return BASE_PREAMBLE + rf"""
\begin{{document}}
{{\color{{accent}}\rule{{\textwidth}}{{1.2pt}}}}
\begin{{center}}
    {{\LARGE\bfseries Research-basis integrity and reproducibility audit}}\\[0.4em]
    {{\large MAS LCE fraudulent-classified-ads compendium}}\\[0.8em]
    {{\normalsize Audit date: March 2026}}
\end{{center}}
{{\color{{accent}}\rule{{\textwidth}}{{0.6pt}}}}

\section*{{Executive summary}}
The archived Graz project is sufficiently rich to support a robust English reconstruction, but it is not internally uniform. The compendium inventory identified {inventory_summary['total_files']} files, including {inventory_summary['pdf_files']} PDFs, {inventory_summary['python_files']} Python scripts, and {inventory_summary['csv_files']} CSV files. Quantitative reproduction was only possible after canonicalisation because several bundled datasets and scripts encode different stages of the same analysis pipeline.

At a high level, the audit reaches five conclusions. First, the thesis' descriptive counts are reproducible when the correct canonical datasets are selected. Second, the two published confusion matrices in the thesis appear to swap false positives and false negatives, even though the surrounding metric values are otherwise reproducible. Third, the exploratory classifier in the original script uses a manual-state variable that would not be available in deployment and therefore should not be treated as a clean operational predictor. Fourth, several early scripts contain analytical bugs or unsafe implementation choices and were intentionally excluded from the final compendium. Fifth, the case-study performance claim is strongest when interpreted as prediction of an internally constructed fraud-risk target rather than of universally adjudicated fraud.

\section{{Scope of the audit}}
The audit asks four practical questions:
\begin{{enumerate}}[leftmargin=1.5em]
    \item Which files in the archive should be treated as canonical evidence for the final reconstruction?
    \item Can the principal counts and metrics reported in the thesis be reproduced from archived data and scripts?
    \item What inconsistencies, risks, or methodological weaknesses are visible in the project corpus?
    \item What minimum steps are needed to turn the archive into a usable, self-explanatory research compendium?
\end{{enumerate}}

\section{{Source corpus provenance}}
The complete inventory covers {inventory_summary['total_files']} files. Table~\ref{{tab:groups}} lists the largest top-level groups in the source tree.

\begin{{table}}[H]
\centering
\caption{{Largest top-level source groups in the archived project tree.}}
\label{{tab:groups}}
\begin{{tabular}}{{lr}}
\toprule
Top-level group & File count \\
\midrule
{top_group_rows}
\bottomrule
\end{{tabular}}
\end{{table}}

The audit distinguishes between archival completeness and analytic direct use. The inventory preserves the whole project context, but only a smaller set of files is directly used in the quantitative reproduction: the ratification form, the completed thesis, the defense slides, the thematic-analysis note, the canonical exploratory dataset, the canonical case-study dataset, and the two random-forest scripts that most closely correspond to the final metrics.

\section{{Canonicalisation decisions}}
Two dataset choices are decisive.
\begin{{itemize}}[leftmargin=1.5em]
    \item \textbf{{Exploratory sample.}} The canonical exploratory file is \texttt{{Scripts/ILCE\_etude\_de\_cas/ILCE\_etude\_de\_cas.csv}}. It matches the thesis narrative and the exploratory random-forest output. Earlier copies in the root \texttt{{Scripts}} folder differ in price, profile, and target coding.
    \item \textbf{{Case-study sample.}} The canonical case-study file is \texttt{{Scripts/ILCE\_fausses\_petites\_annonces\_2/ILCE\_fausses\_petites\_annonces.csv}}. The annex file \texttt{{Annexe\_12-10.csv}} appears to be an earlier snapshot and does not reproduce the final thesis counts.
\end{{itemize}}

The case-study choice is especially important because the annex copy differs from the canonical script copy in hundreds of source-status, target, and fraud-index entries. Without canonicalisation, the archive yields inconsistent descriptive totals.

\section{{Reproduced quantitative claims}}
\subsection{{Exploratory sample}}
The canonical exploratory dataset contains {theory['n_rows']} listings. Its source-status counts are reproduced exactly as {theory['status_counts']['DETECTED']} detected, {theory['status_counts']['IDENTIFIED']} identified, {theory['status_counts']['NEGATIVE']} negative, and {theory['status_counts']['POSITIVE']} positive. The canonical risk-target counts are {theory['target_counts']['acceptable']} acceptable and {theory['target_counts']['unfavorable']} unfavorable.

Running the archived exploratory random-forest logic on the canonical data reproduces the reported metric block: accuracy {_p(eval_theory_orig['accuracy'])}, precision {_p(eval_theory_orig['precision'])}, recall {_p(eval_theory_orig['recall'])}, F1 {_p(eval_theory_orig['f1'])}, specificity {_p(eval_theory_orig['specificity'])}, and AUC {_p(eval_theory_orig['auc'])}. The reproduced confusion matrix is (TN, FP, FN, TP) = ({eval_theory_orig['tn']}, {eval_theory_orig['fp']}, {eval_theory_orig['fn']}, {eval_theory_orig['tp']}). This differs from the thesis table, which appears to swap FP and FN.

A cleaner rerun excluding \texttt{{manual\_state\_code}} produces very similar values---accuracy {_p(eval_theory_clean['accuracy'])} and AUC {_p(eval_theory_clean['auc'])}---which means the exploratory result is not purely an artefact of that variable, even if its inclusion remains methodologically undesirable.

\subsection{{Case-study sample}}
The canonical case-study dataset contains {case['n_rows']} listings. Its source-status counts are reproduced exactly as {case['status_counts']['NEGATIVE']} negative, {case['status_counts']['POSITIVE']} positive, {case['status_counts']['IDENTIFIED']} identified, and {case['status_counts']['DETECTED']} detected. The canonical risk-target counts are {case['target_counts']['acceptable']} acceptable and {case['target_counts']['unfavorable']} unfavorable.

Running the canonical case-study random-forest logic reproduces the main metric claim: accuracy {_p(eval_case['accuracy'])}, precision {_p(eval_case['precision'])}, recall {_p(eval_case['recall'])}, F1 {_p(eval_case['f1'])}, specificity {_p(eval_case['specificity'])}, and AUC {_p(eval_case['auc'])}. The reproduced confusion matrix is (TN, FP, FN, TP) = ({eval_case['tn']}, {eval_case['fp']}, {eval_case['fn']}, {eval_case['tp']}). Again, the thesis table appears to swap FP and FN.

\subsection{{Interpretive caution}}
The strongest published metric block therefore stands up well at the level of numerical reproduction. However, the target itself is an internal fraud-risk label generated from the actionable index. The case-study classifier is consequently best described as a model that predicts \emph{{index-based unfavorable risk}}, not a definitive judicial truth label.

\section{{Detailed discrepancies and version drift}}
Table~\ref{{tab:diffs}} summarises the main field-level differences between alternate archived versions and the canonical files used in the compendium.

\begin{{landscape}}
\begin{{table}}[H]
\centering
\caption{{Field-level differences between alternate archived versions and canonical datasets.}}
\label{{tab:diffs}}
\scriptsize
\begin{{tabularx}}{{\linewidth}}{{p{{4.1cm}} p{{2.3cm}} r p{{3.0cm}} X}}
\toprule
Comparison & Field & Difference count & Canonical example & Alternate example \\
\midrule
{discrepancy_rows}
\bottomrule
\end{{tabularx}}
\end{{table}}
\end{{landscape}}

\section{{Integrity findings}}
\subsection{{Finding 1: swapped confusion-matrix cells in the thesis tables}}
Both reproduced classifiers yield metric blocks that match the thesis, but the published confusion matrices do not align with those metrics. In both cases, the most plausible explanation is a swap between false positives and false negatives during table transcription. This is a presentation error rather than a failure of the archived script outputs.

\subsection{{Finding 2: exploratory-script leakage through manual-state coding}}
The exploratory script uses \texttt{{MA\_ETAT}} (renamed \texttt{{manual\_state\_code}} in the compendium) as a predictor. In the archived data, that variable encodes whether a listing was manually confirmed or merely detected or identified. Because such information is unavailable before manual review, it should not be treated as a deployment-ready predictor.

\subsection{{Finding 3: early similarity scripts contain a self-comparison bug}}
Some earlier statistics scripts compute Jaccard similarity by comparing each text string to itself. In that configuration, the similarity score is trivially 1.0 for every row and therefore unusable as evidence of between-listing similarity. Those scripts were not used in the final compendium.

\subsection{{Finding 4: unsafe legacy scraping code}}
The archived project contains legacy scraper files with embedded login credentials. These files were excluded from the final compendium and should never be redistributed or executed. The compendium is intentionally offline and reproduction is restricted to archived snapshots rather than renewed scraping.

\subsection{{Finding 5: labels at the extremes are stronger than labels in the middle}}
The archive contains manually confirmed positives and negatives, but the broad binary target used by the predictive models is derived from the internal fraud index. Ancillary validation on the confirmed-positive or confirmed-negative subset remains strong (case-study subset AUC {_p(eval_confirmed_case['auc'])}; exploratory subset AUC {_p(eval_confirmed_theory['auc'])}), yet those subsets are small and represent the extremes of the phenomenon rather than its full operational ambiguity.

\section{{Overall assessment}}
The audit concludes that the research basis is \textbf{{fit for a documented article-style reconstruction and for an operational pilot}}. The conceptual framework is coherent, the qualitative material is aligned with the quantitative indicators, and the most important numerical claims can be reproduced from the archive after canonicalisation. At the same time, the project is \textbf{{not yet a publication-grade machine-learning benchmark}} in the strictest sense. To reach that standard, future work would need stronger independent labels, cleaner version control, explicit separation between development and validation files, and removal of all legacy scripts that embed credentials or use analytically invalid similarity routines.

In practical terms, the final compendium resolves the main usability problems of the archive: it identifies canonical data files, sanitises sensitive content, documents discrepancies, and packages the full reconstruction in English with Python-only reproducibility.

\end{{document}}
"""


def build_guide_tex(context: Dict) -> str:
    inventory_summary = context["inventory_summary"]
    return BASE_PREAMBLE + rf"""
\begin{{document}}
{{\color{{accent}}\rule{{\textwidth}}{{1.2pt}}}}
\begin{{center}}
    {{\LARGE\bfseries Project guide}}\\[0.4em]
    {{\large Python-only reproduction package for the MAS LCE fraudulent-classified-ads study}}\\[0.8em]
    {{\normalsize March 2026}}
\end{{center}}
{{\color{{accent}}\rule{{\textwidth}}{{0.6pt}}}}

\section*{{What this package is}}
This package is a self-contained English compendium built from the archived David Graz MAS LCE project. It contains:
\begin{{itemize}}[leftmargin=1.5em]
    \item an article-style reconstruction of the thesis;
    \item a dedicated integrity and reproducibility audit;
    \item sanitised canonical datasets that are sufficient to reproduce the published descriptive tables and the archived predictive metrics;
    \item Python scripts that regenerate tables, figures, manifests, checksums, and PDF reports;
    \item metadata files that document provenance, version drift, and canonicalisation choices.
\end{{itemize}}

\section{{Package structure}}
\begin{{tabularx}}{{\textwidth}}{{p{{4.0cm}} X}}
\toprule
Path & Contents \\
\midrule
reports/ & Final PDFs and LaTeX sources for the article, audit, and guide \\
figures/ & Reproduced figures used by the reports \\
data/canonical/ & Sanitised canonical exploratory and case-study datasets \\
data/tables/ & CSV tables used in the reports \\
data/json/ & JSON summaries used to populate the LaTeX reports \\
data/metadata/ & Source inventory, discrepancy logs, checksums, manifest, and data dictionary \\
scripts/ & Python-only build and analysis scripts \\
\bottomrule
\end{{tabularx}}

\section{{How to rebuild the package}}
The package is designed so that the main build command is a Python script.

\begin{{verbatim}}
python scripts/build_all.py --use-packaged-data
\end{{verbatim}}

If you also have access to the original extracted \texttt{{\_Master\_LCE\_Docs}} directory, you can regenerate the canonical datasets and the inventory directly from the source corpus:

\begin{{verbatim}}
python scripts/build_all.py --source-root /path/to/_Master_LCE_Docs
\end{{verbatim}}

The build script regenerates:
\begin{{itemize}}[leftmargin=1.5em]
    \item canonical CSV datasets;
    \item descriptive and discrepancy tables;
    \item ROC and indicator-distribution figures;
    \item LaTeX files and compiled PDFs;
    \item a manifest and SHA-256 checksums for all package files.
\end{{itemize}}

\section{{Canonical datasets}}
Two canonical datasets are bundled because the archive contains multiple versions of the same analyses.
\begin{{itemize}}[leftmargin=1.5em]
    \item \texttt{{exploratory\_sample\_canonical.csv}} reproduces the exploratory verification sample used by the thesis and by the archived exploratory random-forest script.
    \item \texttt{{case\_study\_sample\_canonical.csv}} reproduces the broader case-study sample whose counts and predictive metrics match the final thesis narrative.
\end{{itemize}}

Both canonical files are sanitised: personally identifying profile fields, links, message fragments, and contact artefacts were removed because they are not necessary for the quantitative reproduction.

\section{{Data dictionary}}
\begin{{tabularx}}{{\textwidth}}{{p{{4.0cm}} X}}
\toprule
Field & Meaning \\
\midrule
listing\_id & Stable listing identifier inside the archived dataset \\
source\_status & Archived manual status (POSITIVE, NEGATIVE, IDENTIFIED, DETECTED) \\
ad\_text & Listing description text \\
price\_chf & Listing price in CHF-equivalent numeric form \\
profile\_creation\_year & Year the seller profile was created; missing for opaque profiles \\
content\_score / price\_score / profile\_score & Encoded operational indicators used by the original project \\
fraud\_index & Sum of indicator scores used by the thesis \\
risk\_target & Binary operational target: 0 = acceptable, 1 = unfavorable \\
price\_ratio & Derived ratio between listing price and the model-specific market benchmark \\
\bottomrule
\end{{tabularx}}

\section{{Integrity and ethics notes}}
The source archive contains {inventory_summary['total_files']} files, including legacy materials that should not be reused operationally. In particular:
\begin{{itemize}}[leftmargin=1.5em]
    \item legacy scraper scripts with embedded credentials were excluded from the compendium;
    \item early similarity scripts with self-comparison bugs were excluded from the final analysis pipeline;
    \item reproduction is intentionally offline and depends on archived snapshots rather than fresh scraping.
\end{{itemize}}

\section{{Reading order}}
For most users, the recommended order is:
\begin{{enumerate}}[leftmargin=1.5em]
    \item read the article-style reconstruction;
    \item read the integrity audit to understand what was reproduced and what remains uncertain;
    \item inspect the canonical datasets and the metadata tables if you need technical traceability;
    \item run \texttt{{python scripts/build\_all.py --use-packaged-data}} if you want to regenerate all outputs.
\end{{enumerate}}

\end{{document}}
"""
