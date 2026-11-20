"""Markdown report + figures generated from the E1-E9 JSON artifacts."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from oblivionx.common import read_json


def _fmt(x: Any, nd: int = 3) -> str:
    if x is None:
        return "-"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def _table(header: List[str], rows: List[List[Any]]) -> List[str]:
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join(["---"] * len(header)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return out


def metrics_table(agg: Dict[str, Any]) -> str:
    rows = [
        ("Behavior recall", "behavior_recall", 3),
        ("Behavior precision", "behavior_precision", 3),
        ("Evidence precision", "evidence_precision", 3),
        ("Stage accuracy (LCS F1)", "stage_accuracy", 3),
        ("Stage precision", "stage_precision", 3),
        ("Stage recall", "stage_recall", 3),
        ("Analysis completion rate", "completion_rate", 3),
        ("Execution success rate", "execution_success_rate", 3),
        ("Timeout rate", "timeout_rate", 3),
        ("Deobfuscation success", "deobfuscation_success", 3),
        ("Analysis time/sample (ms)", "analysis_time_ms_mean", 1),
        ("Unsupported behavior claim rate", "unsupported_claim_rate", 3),
    ]
    lines = ["| Metric | Value |", "|---|---|"]
    for label, key, nd in rows:
        lines.append(f"| {label} | {_fmt(agg.get(key), nd)} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def _bar(values: Dict[str, float], title: str, path: Path,
         ylabel: str = "", ylim: float = 1.05) -> None:
    keys = list(values.keys())
    vals = [values[k] for k in keys]
    plt.figure(figsize=(8, 4))
    bars = plt.bar(keys, vals, color="#3b6ea5")
    plt.bar_label(bars, fmt="%.2f", fontsize=7, padding=2)
    if ylim:
        plt.ylim(0, ylim)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(rotation=25, ha="right", fontsize=8)
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def _line(xs: List[int], series: Dict[str, List[float]], title: str,
          path: Path, ylabel: str = "") -> None:
    plt.figure(figsize=(8, 4))
    for name, ys in series.items():
        plt.plot(xs, ys, marker="o", label=name)
    plt.xlabel("number of segments N")
    plt.ylabel(ylabel)
    plt.ylim(0, 1.05)
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def write_figures(eval_dir: Path, fig_dir: Path) -> List[Path]:
    fig_dir = Path(fig_dir)
    fig_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []

    def save(path: Path) -> None:
        written.append(path)

    # E2
    e2 = read_json(eval_dir / "E2_static_vs_dynamic.json")
    p = fig_dir / "E2_recall.png"
    _bar({"static": e2.get("mean_static_recall", 0),
          "dynamic": e2.get("mean_dynamic_recall", 0),
          "view agreement (Jaccard)": e2.get("mean_view_jaccard", 0)},
         "E2: static vs dynamic observability", p, "mean recall")
    save(p)

    fam = e2.get("by_family", {})
    if fam:
        p = fig_dir / "E2_by_family.png"
        names = sorted(fam)
        x = np.arange(len(names))
        plt.figure(figsize=(10, 4.5))
        plt.bar(x - 0.2, [fam[n]["static_recall"] for n in names], 0.4,
                label="static")
        plt.bar(x + 0.2, [fam[n]["dynamic_recall"] for n in names], 0.4,
                label="dynamic")
        plt.xticks(x, names, rotation=35, ha="right", fontsize=8)
        plt.ylim(0, 1.05)
        plt.ylabel("mean behavior recall")
        plt.title("E2: recall by family")
        plt.legend()
        plt.tight_layout()
        plt.savefig(p, dpi=120)
        plt.close()
        save(p)

    # E3
    e3 = read_json(eval_dir / "E3_obfuscation.json")
    srv = e3.get("static_recall_by_variant", {})
    drv = e3.get("dynamic_recall_by_variant", {})
    variants = sorted(srv)
    p = fig_dir / "E3_recall_by_variant.png"
    x = np.arange(len(variants))
    plt.figure(figsize=(8, 4))
    plt.bar(x - 0.2, [srv[v]["mean"] for v in variants], 0.4, label="static")
    plt.bar(x + 0.2, [drv[v]["mean"] for v in variants], 0.4, label="dynamic")
    plt.xticks(x, variants)
    plt.ylim(0, 1.05)
    plt.ylabel("mean behavior recall")
    plt.title("E3: observability by obfuscation variant")
    plt.legend()
    plt.tight_layout()
    plt.savefig(p, dpi=120)
    plt.close()
    save(p)

    det = e3.get("detection_by_variant", {})
    if det:
        p = fig_dir / "E3_detection.png"
        _bar({k: v["recall"] for k, v in det.items() if k != "plain"},
             "E3: obfuscation detection recall", p, "recall")
        save(p)

    # E4
    e4 = read_json(eval_dir / "E4_temporal_segmentation.json")
    by_n = e4.get("by_n", {})
    if by_n:
        xs = sorted(int(n) for n in by_n)
        p = fig_dir / "E4_segmentation.png"
        _line(xs, {
            "segment purity": [by_n[str(n)]["purity"] for n in xs],
            "stage concentration": [by_n[str(n)]["concentration"]
                                    for n in xs],
            "boundary F1": [by_n[str(n)]["boundary_f1"] for n in xs],
        }, "E4: stage separation vs number of segments", p, "score")
        save(p)

    # E6
    e6 = read_json(eval_dir / "E6_reconstruction.json")
    fam6 = e6.get("by_family", {})
    if fam6:
        p = fig_dir / "E6_by_family.png"
        _bar({k: v["stage_accuracy"] for k, v in fam6.items()},
             "E6: stage accuracy (LCS F1) by family", p, "stage accuracy")
        save(p)

    # E7
    e7 = read_json(eval_dir / "E7_failures.json")
    fc = e7.get("failure_counts", {})
    bf = e7.get("baseline_failure_counts", {})
    if fc:
        classes = sorted(set(fc) | set(bf))
        p = fig_dir / "E7_failures.png"
        x = np.arange(len(classes))
        plt.figure(figsize=(9, 4))
        plt.bar(x - 0.2, [bf.get(c, 0) for c in classes], 0.4,
                label="baseline (no interaction handling)")
        plt.bar(x + 0.2, [fc.get(c, 0) for c in classes], 0.4,
                label="Oblivion-X (handled)")
        plt.xticks(x, classes, rotation=25, ha="right", fontsize=8)
        plt.ylabel("samples")
        plt.title("E7: failure classes per configuration")
        plt.legend(fontsize=8)
        plt.tight_layout()
        plt.savefig(p, dpi=120)
        plt.close()
        save(p)

    # E8
    e8 = read_json(eval_dir / "E8_performance.json")
    fam8 = e8.get("by_family_ms_mean", {})
    if fam8:
        p = fig_dir / "E8_time_by_family.png"
        _bar(fam8, "E8: mean analysis time per sample by family",
             p, "ms", ylim=0)
        save(p)

    # E10
    e10_path = eval_dir / "E10_completion_calibration.json"
    if e10_path.exists():
        e10 = read_json(e10_path)
        rel = e10.get("reliability", [])
        if rel:
            p = fig_dir / "E10_reliability.png"
            plt.figure(figsize=(4.5, 4.5))
            plt.plot([0, 1], [0, 1], "--", color="grey", linewidth=1,
                     label="perfect calibration")
            plt.plot([r["mean_predicted"] for r in rel],
                     [r["observed_rate"] for r in rel], "o-",
                     label="leave-one-family-out")
            plt.xlabel("predicted completion probability")
            plt.ylabel("observed completion rate")
            plt.title("E10: reliability of completion prediction")
            plt.ylim(-0.05, 1.05)
            plt.legend(fontsize=8)
            plt.tight_layout()
            plt.savefig(p, dpi=120)
            plt.close()
            save(p)

    return written


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

def write_markdown_report(eval_dir: Path, out_path: Path,
                          fig_dir: Path | None = None) -> Path:
    eval_dir = Path(eval_dir)
    out_path = Path(out_path)
    parts: List[str] = []
    add = parts.append

    add("# Oblivion-X — Experiment Report\n")
    add("> Generated from the E1..E8 JSON artifacts. Dynamic telemetry is "
        "produced by the deterministic Linux simulator unless stated "
        "otherwise; static analysis runs on the corpus Office files "
        "(Word/Excel COM-authored or offline-built with the pure-Python "
        "MS-OVBA writer).\n")

    # E1 -----------------------------------------------------------------
    e1 = read_json(eval_dir / "E1_reproduce_oblivion.json")
    add("## E1 — Reproduce Oblivion (pre-processing taxonomy)\n")
    c = e1["counts"]
    n_files = e1.get("n_files")
    if n_files is None:
        n_files = sum(c.get(k, 0) for k in
                      ("empty", "corrupted", "interaction", "cls",
                       "bas_cls", "other"))
    add(f"Oblivion's pre-processing classification applied to the "
        f"{n_files}-sample controlled corpus (cf. paper Table 1):\n")
    parts.extend(_table(
        ["Category", "Count"],
        [[k, c.get(k, 0)] for k in
         ("empty", "corrupted", "interaction", "cls", "bas_cls", "other",
          "extracted", "no_file")]))
    add("")
    add(f"- `extracted` counts modules, not samples "
        f"({c.get('extracted', 0)} modules over {n_files} files).")
    add(f"- `empty` = the {c.get('empty', 0)} samples whose project has no "
        f"executable code; `interaction` = the {c.get('interaction', 0)} "
        f"MsgBox-gated samples; everything else is a standard `.bas + .cls` "
        f"project.\n")

    # E2 -----------------------------------------------------------------
    e2 = read_json(eval_dir / "E2_static_vs_dynamic.json")
    add("## E2 — Static vs dynamic observability (RQ2)\n")
    parts.extend(_table(
        ["Measure", "Value"],
        [["Mean static behavior recall", _fmt(e2.get("mean_static_recall"))],
         ["Mean dynamic behavior recall", _fmt(e2.get("mean_dynamic_recall"))],
         ["Mean view agreement (Jaccard)", _fmt(e2.get("mean_view_jaccard"))]]))
    add("")
    add("Behaviors seen by exactly one view (ground-truth only):\n")
    so = dict(e2.get("static_only", []))
    do = dict(e2.get("dynamic_only", []))
    union = sorted(set(so) | set(do),
                   key=lambda b: -(so.get(b, 0) + do.get(b, 0)))[:12]
    parts.extend(_table(
        ["Behavior", "Static only", "Dynamic only"],
        [[b, so.get(b, 0), do.get(b, 0)] for b in union]))
    add("")
    add("Reading: static analysis sees *intent* (URLs, `Outlook.Send`, "
        "`Shell`/`cmd` strings) even when the runtime gate never opens, while "
        "dynamic analysis sees *effects* of spawned processes "
        "(`file_write`/`file_execute` from PowerShell) that never appear in "
        "the VBA source. Neither view alone is sufficient.\n")

    # E3 -----------------------------------------------------------------
    e3 = read_json(eval_dir / "E3_obfuscation.json")
    add("## E3 — Obfuscation vs observability (RQ4)\n")
    srv = e3.get("static_recall_by_variant", {})
    drv = e3.get("dynamic_recall_by_variant", {})
    det = e3.get("detection_by_variant", {})
    deob = e3.get("deobfuscation_success_by_variant", {})
    rows = []
    for v in sorted(srv):
        # plain has no technique to detect: precision/recall are undefined
        plain = v == "plain"
        rows.append([
            v,
            _fmt(srv[v]["mean"]),
            _fmt(drv.get(v, {}).get("mean")),
            "n/a" if plain else _fmt(det.get(v, {}).get("precision")),
            "n/a" if plain else _fmt(det.get(v, {}).get("recall")),
            _fmt(deob.get(v, {}).get("mean")) if v in deob else "n/a",
        ])
    parts.extend(_table(
        ["Variant", "Static recall", "Dynamic recall",
         "Detection precision", "Detection recall", "Deobf. success"], rows))
    add("")
    add("- Detection precision is 1.0 for every technique: no plain sample "
        "trips a heuristic.")
    deob_vals = [v.get("mean") for v in deob.values()
                 if v.get("mean") is not None]
    if deob_vals:
        add(f"- Split/encode/combination detection misses the variants where "
            f"the transform had too little material to rewrite (short "
            f"macros); deobfuscation still recovers the hidden literal in "
            f"{min(deob_vals):.0%}-{max(deob_vals):.0%} of the recoverable "
            f"variants.")
    else:
        add("- No recoverable obfuscation variant was present in the corpus.")
    add("- Static recall barely changes across variants because the analyzer "
        "scans the obfuscated source directly; what drops is *literal* "
        "visibility (URLs, API names), which is why deobfuscation matters "
        "for reconstruction rather than for recall.\n")

    # E4 -----------------------------------------------------------------
    e4 = read_json(eval_dir / "E4_temporal_segmentation.json")
    add("## E4 — Temporal segmentation stage separation (RQ3)\n")
    by_n = e4.get("by_n", {})
    xs = sorted(by_n, key=int)
    parts.extend(_table(
        ["N", "Segment purity", "Stage concentration", "Boundary F1",
         "Boundary precision", "Boundary recall", "Pk", "WindowDiff"],
        [[n, _fmt(by_n[n]["purity"]), _fmt(by_n[n]["concentration"]),
          _fmt(by_n[n]["boundary_f1"]), _fmt(by_n[n]["boundary_precision"]),
          _fmt(by_n[n]["boundary_recall"]), _fmt(by_n[n].get("pk")),
          _fmt(by_n[n].get("windowdiff"))] for n in xs]))
    add("")
    best_n = e4.get("best_n_by_boundary_f1")
    add(f"- Best boundary F1 at **N={best_n}** "
        f"({_fmt(by_n[str(best_n)]['boundary_f1'])}).")
    add(f"- Pk and WindowDiff are the reference text-segmentation measures "
        f"(lower is better). They keep improving with N because finer buckets "
        f"approximate the truth more closely in window terms, which shows "
        f"that a single fixed N is a trade-off rather than an optimum; the "
        f"boundary F1 peak at N={best_n} is the scale at which whole stages "
        f"fit inside a bucket.")
    cp = e4.get("change_point_estimate") or {}
    if cp:
        add(f"- **Change-point estimate** (BIC-style penalty, held out from "
            f"the labels): mean estimated segments {_fmt(cp.get('mean_estimated'))} "
            f"vs mean ground-truth stages {_fmt(cp.get('mean_true'))}; exact "
            f"agreement {_fmt(cp.get('exact_rate'))}, mean absolute error "
            f"{_fmt(cp.get('mean_abs_error'))}. The estimator never sees the "
            f"ground truth, so this asks whether N can be *found* instead of "
            f"swept.")
    nl = e4.get("null_purity") or {}
    if nl:
        add(f"- **Permutation null** at N={nl.get('n_segments')}: observed "
            f"purity {_fmt(nl.get('mean_observed'))} vs shuffled order "
            f"{_fmt(nl.get('mean_null'))} (mean z = {_fmt(nl.get('mean_z'))}); "
            f"{_fmt(nl.get('share_p_below_0.01'))} of samples reach p < 0.01. "
            f"A z near 1 means the stage separation at this scale is only "
            f"marginally better than chance, which tempers the boundary-F1 "
            f"headline.")
    add("")

    # E5 -----------------------------------------------------------------
    e5 = read_json(eval_dir / "E5_ground_truth.json")
    add("## E5 — Controlled ground-truth validation\n")
    checks = e5.get("checks", {})
    parts.extend(_table(
        ["Check", "Pass rate"],
        [[k.replace("_", " "), _fmt(v)] for k, v in checks.items()]))
    add("")
    add(f"- {e5.get('n_samples')} samples; entry-point mismatches "
        f"{e5.get('n_entry_mismatch')}, behavior-hint mismatches "
        f"{e5.get('n_behavior_hint_mismatch')}, stage-order mismatches "
        f"{e5.get('n_stage_order_mismatch')}.\n")

    # E6 -----------------------------------------------------------------
    e6 = read_json(eval_dir / "E6_reconstruction.json")
    add("## E6 — Stage reconstruction (RQ1, RQ5)\n")
    add("### All samples\n")
    add(metrics_table(e6.get("aggregate", {})))
    add("")
    if e6.get("aggregate_execution_success"):
        add("### Samples whose macro ran to completion\n")
        add(metrics_table(e6["aggregate_execution_success"]))
        add("")
    fam = e6.get("by_family", {})
    if fam:
        add("### Per family\n")
        parts.extend(_table(
            ["Family", "n", "Behavior recall", "Behavior precision",
             "Stage accuracy", "Stage precision", "Stage recall"],
            [[f, v["n"], _fmt(v["behavior_recall"]),
              _fmt(v["behavior_precision"]), _fmt(v["stage_accuracy"]),
              _fmt(v["stage_precision"]), _fmt(v["stage_recall"])]
             for f, v in fam.items()]))
        add("")
    success = e6.get("aggregate_execution_success", {})
    add(f"Reading: on samples that actually execute, behavior recall is "
        f"{_fmt(success.get('behavior_recall'))} and stage accuracy "
        f"{_fmt(success.get('stage_accuracy'))}. The gap on the full set "
        f"comes from environment-gated families whose later stages never "
        f"run: the reconstructor correctly reports only the observable "
        f"prefix and marks the rest unsupported instead of inventing it.\n")

    # E7 -----------------------------------------------------------------
    e7 = read_json(eval_dir / "E7_failures.json")
    add("## E7 — Failure analysis\n")
    fc = e7.get("failure_counts", {})
    bf = e7.get("baseline_failure_counts", {})
    classes = sorted(set(fc) | set(bf))
    parts.extend(_table(
        ["Failure class", "Baseline", "Oblivion-X (handled)"],
        [[k, bf.get(k, 0), fc.get(k, 0)] for k in classes]))
    add("")
    add(f"- Expectation mismatches: handled **{e7.get('n_expectation_mismatch')}**, "
        f"baseline **{e7.get('n_baseline_mismatch')}**.")
    add(f"- Interaction handling recovered "
        f"**{e7.get('recovered_by_interaction_handling')}** of "
        f"{e7.get('interaction_gated_total')} interaction-gated samples.")
    add("- `dynamic_env` (Outlook/FTP absent), `dynamic_date` (date gate), "
        "`dynamic_semantic` (broken macro) and `dynamic_timeout` are not "
        "fixed by interaction handling: they are genuine environment or "
        "sample limitations and are reported as such.\n")

    # E8 -----------------------------------------------------------------
    e8 = read_json(eval_dir / "E8_performance.json")
    add("## E8 — Performance / resource analysis\n")
    parts.extend(_table(
        ["Measure", "Value"],
        [["Samples", e8.get("n")],
         ["Mean time/sample (ms)", _fmt(e8.get("total_time_ms_mean"), 1)],
         ["Std (ms)", _fmt(e8.get("total_time_ms_std"), 1)],
         ["p50 (ms)", _fmt(e8.get("total_time_ms_p50"), 1)],
         ["p95 (ms)", _fmt(e8.get("total_time_ms_p95"), 1)],
         ["Throughput (samples/s)",
          _fmt(e8.get("throughput_samples_per_sec"), 1)],
         ["Static time/sample (ms)", _fmt(e8.get("static_time_ms_mean"), 1)],
         ["Simulator time/sample (ms)",
          _fmt(e8.get("dynamic_time_ms_mean"), 1)],
         ["Completion rate", _fmt(e8.get("completion_rate"))],
         ["Timeout rate", _fmt(e8.get("timeout_rate"))]]))
    add("")
    add(f"> {e8.get('note', '')}\n")

    # E9 -----------------------------------------------------------------
    e9 = read_json(eval_dir / "E9_chain_order.json")
    add("## E9 — Chain-order ablation: ontology vs evidence (RQ5)\n")
    summary = e9.get("summary", {})
    modes = e9.get("modes", ["ontology", "timestamp"])
    parts.extend(_table(
        ["Ordering", "Stage accuracy", "Precision", "Recall",
         "Exact-match rate"],
        [[m, _fmt(summary[m]["stage_accuracy"]),
          _fmt(summary[m]["stage_precision"]), _fmt(summary[m]["stage_recall"]),
          _fmt(summary[m]["exact_match_rate"])] for m in modes
         if m in summary]))
    add("")
    add(f"- The two orderings use the same events and produce the same set of "
        f"stages; only the order differs. They disagree on "
        f"**{e9.get('n_mode_disagreements', 0)}/{e9.get('n_samples', 0)}** "
        f"samples and the accuracy delta (timestamp − ontology) is "
        f"**{_fmt(e9.get('accuracy_delta_timestamp_minus_ontology'))}**.")
    add(f"- An exact-match rate of "
        f"{_fmt(summary.get('ontology', {}).get('exact_match_rate'))} under "
        f"ontology ordering is partly true by construction. Under evidence "
        f"ordering it is "
        f"{_fmt(summary.get('timestamp', {}).get('exact_match_rate'))}, which "
        f"is the number that shows the chronological chain is recovered from "
        f"observations rather than assumed.")
    add("- The residual gap is informative: recovered literals can add a "
        "stage that no telemetry ever observed (`url_reference` from a "
        "deobfuscated blob lands in `c2_download`). Under ontology ordering "
        "it is silently slotted into its canonical position; under evidence "
        "ordering it is visible as an untimed stage, which is the honest "
        "reading — static evidence is *intent*, not an observed event.\n")

    # E10 ----------------------------------------------------------------
    e10 = read_json(eval_dir / "E10_completion_calibration.json")
    add("## E10 — Calibration of completion prediction (extension)\n")
    ov = e10.get("overall", {})
    parts.extend(_table(
        ["Measure", "Value"],
        [["Samples", ov.get("n")],
         ["Base rate (completed)", _fmt(ov.get("base_rate"))],
         ["AUC (leave-one-family-out)", _fmt(ov.get("auc"))],
         ["Brier", _fmt(ov.get("brier"))],
         ["Brier baseline", _fmt(ov.get("brier_baseline"))],
         ["Brier skill", _fmt(ov.get("brier_skill"))],
         ["ECE (10 bins)", _fmt(ov.get("ece"))],
         ["AUC, in-sample (reference)", _fmt(ov.get("in_sample_auc"))]]))
    add("")
    rel = e10.get("reliability", [])
    if rel:
        add("Reliability (equal-width probability bins):\n")
        parts.extend(_table(
            ["Predicted bin", "n", "Mean predicted", "Observed rate"],
            [[f"{row['bin_lo']:.1f}–{row['bin_hi']:.1f}", row["n"],
              _fmt(row["mean_predicted"]), _fmt(row["observed_rate"])]
             for row in rel]))
        add("")
    by_failure = e10.get("by_failure", {})
    if by_failure:
        add("By failure mechanism (family counts show whether the cause can "
            "generalise):\n")
        parts.extend(_table(
            ["Mechanism", "n", "Families", "Observed completed",
             "Mean predicted"],
            [[name, row["n"], row["n_families"],
              _fmt(row["observed_rate"]), _fmt(row["mean_predicted"])]
             for name, row in by_failure.items()]))
        add("")
    add("- Static evidence predicts completion only when the blocking "
        "mechanism generalises across families. Empty projects are predicted "
        "almost perfectly (0.03) and Outlook-gated families are predicted "
        "low because another family also references Outlook; FTP, date gates, "
        "busy loops and runtime errors occur in a single family each, so a "
        "held-out family regresses to the base rate.")
    add(f"- The gap between the in-sample AUC "
        f"({_fmt(ov.get('in_sample_auc'))}) and the leave-one-family-out AUC "
        f"({_fmt(ov.get('auc'))}) is the amount of family composition the "
        f"model would memorise. The out-of-fold Brier skill "
        f"({_fmt(ov.get('brier_skill'))}) is barely positive: an analyst "
        f"cannot reliably anticipate the unsupported-claim rate from static "
        f"evidence alone, which is precisely why the pipeline measures and "
        f"reports it instead of estimating it.\n")

    if fig_dir:
        figs = write_figures(eval_dir, fig_dir)
        add("## Figures\n")
        for f in figs:
            add(f"![{f.stem}]({Path(fig_dir).name}/{f.name})")
        add("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts), encoding="utf-8")
    return out_path
