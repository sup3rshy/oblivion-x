"""Experiments E1-E8 drivers (per the project plan, Section 4)."""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from oblivionx.common import BEHAVIOR_DEFS, STAGE_ORDER, read_json, write_json
from oblivionx.eval.metrics import aggregate, evaluate_sample
from oblivionx.reconstruction.reconstruct import reconstruct
from oblivionx.telemetry.schema import Event, SampleAnalysis


def _load_manifest(corpus_dir: Path) -> List[Dict[str, Any]]:
    return read_json(Path(corpus_dir) / "manifest.json")["samples"]


def _load_gt(corpus_dir: Path) -> Dict[str, Any]:
    return read_json(Path(corpus_dir) / "ground_truth.json")


def _top(counter: Dict[str, int], n: int) -> List[Any]:
    """Deterministic ``Counter.most_common``: ties broken by name.

    Plain ``most_common`` preserves insertion order, and the insertion order
    of counters built from sets varies with Python's hash seed.
    """
    return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:n]


def _has_executable_code(source: str) -> bool:
    """True if a module contains statements, not just Attribute metadata
    and empty Sub/End Sub scaffolding."""
    for line in source.splitlines():
        s = line.strip()
        if (not s or s.lower().startswith("attribute")
                or s.startswith("'") or s.lower().startswith("rem ")):
            continue
        low = s.lower()
        if re.fullmatch(r"(public |private |friend )?(sub|function)\s+\w+.*", low):
            continue
        if low in ("end sub", "end function", "option explicit"):
            continue
        return True
    return False


# ---------------------------------------------------------------------------
# E1 — Reproduce Oblivion
# ---------------------------------------------------------------------------

def experiment_E1(corpus_dir: Path, analysis_dir: Path,
                  out_dir: Path) -> Dict[str, Any]:
    """Reproduce Oblivion's pre-processing taxonomy on the corpus:
    empty / corrupted / interaction-based / standard (.cls, .bas+.cls)
    (paper Table 1), plus extraction coverage."""
    from oblivionx.static.extractor import extract_modules
    out_dir = Path(out_dir)
    counts = {"empty": 0, "corrupted": 0, "interaction": 0,
              "cls": 0, "bas_cls": 0, "other": 0, "extracted": 0,
              "no_file": 0}
    per_sample = {}
    gt_all = _load_gt(corpus_dir)
    for m in _load_manifest(corpus_dir):
        sid = m["id"]
        f = corpus_dir / "samples" / f"{sid}.{m['format']}"
        if not f.exists():
            counts["no_file"] += 1
            per_sample[sid] = "no_file"
            continue
        mods = extract_modules(f)
        gt = gt_all.get(sid, m.get("ground_truth", {}))
        has_code = any(_has_executable_code(x["source"]) for x in mods)
        if not mods or not has_code:
            label = "empty"
        elif gt.get("interaction"):
            label = "interaction"
        else:
            kinds = sorted({x["kind"] for x in mods})
            label = "bas_cls" if kinds == ["document", "procedural"] \
                else ("cls" if kinds == ["document"] else "other")
        counts[label] += 1
        counts["extracted"] += len(mods)
        per_sample[sid] = label
    report = {
        "experiment": "E1",
        "title": "Reproduce Oblivion (pre-processing taxonomy)",
        "n_samples": len(per_sample),
        "n_files": sum(counts[k] for k in
                       ("empty", "corrupted", "interaction", "cls",
                        "bas_cls", "other")),
        "counts": counts,
        "per_sample": per_sample,
    }
    write_json(report, out_dir / "E1_reproduce_oblivion.json")
    return report


# ---------------------------------------------------------------------------
# E2 — Static vs dynamic observability (RQ2)
# ---------------------------------------------------------------------------

def experiment_E2(corpus_dir: Path, analysis_dir: Path,
                  out_dir: Path) -> Dict[str, Any]:
    gt = _load_gt(corpus_dir)
    rows = []
    for m in _load_manifest(corpus_dir):
        sid = m["id"]
        sta = read_json(analysis_dir / "static" / f"{sid}.json")
        dyn = read_json(analysis_dir / "dynamic" / f"{sid}.json")
        s_beh = {e["behavior"] for e in sta["events"]}
        d_beh = {e["behavior"] for e in dyn["events"] if e["t_ms"] is not None}
        g_beh = set(gt[sid]["behaviors"])
        rows.append({
            "id": sid,
            "family": m["family"],
            "variant": m["variant"],
            "static_observed": sorted(s_beh),
            "dynamic_observed": sorted(d_beh),
            "gt": sorted(g_beh),
            "static_missed": sorted(g_beh - s_beh),
            "dynamic_missed": sorted(g_beh - d_beh),
            "static_only": sorted(s_beh - d_beh),
            "static_recall": len(g_beh & s_beh) / max(len(g_beh), 1),
            "dynamic_recall": len(g_beh & d_beh) / max(len(g_beh), 1),
        })
    # aggregate static misses (RQ2: what does each miss?)
    from collections import Counter
    static_miss = Counter(b for r in rows for b in r["static_missed"])
    dynamic_miss = Counter(b for r in rows for b in r["dynamic_missed"])
    # unique *ground-truth* behaviors: seen by one view but not the other
    static_only = Counter(
        b for r in rows
        for b in ((set(r["gt"]) & set(r["static_observed"]))
                  - set(r["dynamic_observed"])))
    dynamic_only = Counter(
        b for r in rows
        for b in ((set(r["gt"]) & set(r["dynamic_observed"]))
                  - set(r["static_observed"])))
    static_recall = float(np.mean([r["static_recall"] for r in rows])) if rows else 0
    dynamic_recall = float(np.mean([r["dynamic_recall"] for r in rows])) if rows else 0

    by_family: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        f = by_family.setdefault(r["family"], {"n": 0, "static": [], "dynamic": []})
        f["n"] += 1
        f["static"].append(r["static_recall"])
        f["dynamic"].append(r["dynamic_recall"])
    family_table = {
        fam: {"n": v["n"],
              "static_recall": float(np.mean(v["static"])),
              "dynamic_recall": float(np.mean(v["dynamic"])),
              "gap": float(np.mean(v["dynamic"]) - np.mean(v["static"]))}
        for fam, v in sorted(by_family.items())}

    # agreement between the two views
    jaccard = []
    for r in rows:
        s, d = set(r["static_observed"]), set(r["dynamic_observed"])
        jaccard.append(len(s & d) / max(len(s | d), 1))
    report = {
        "experiment": "E2",
        "title": "Static vs dynamic observability (RQ2)",
        "mean_static_recall": static_recall,
        "mean_dynamic_recall": dynamic_recall,
        "mean_view_jaccard": float(np.mean(jaccard)) if jaccard else 0.0,
        "most_static_missed": _top(static_miss, 15),
        "most_dynamic_missed": _top(dynamic_miss, 15),
        "static_only": _top(static_only, 15),
        "dynamic_only": _top(dynamic_only, 15),
        "by_family": family_table,
        "per_sample": rows,
    }
    write_json(report, out_dir / "E2_static_vs_dynamic.json")
    return report


# ---------------------------------------------------------------------------
# E3 — Unobfuscated vs obfuscated (RQ4)
# ---------------------------------------------------------------------------

# Behaviors performed by a spawned process rather than by VBA itself: their
# ground truth is the dynamic trace, so the static hint check skips them.
_RUNTIME_ONLY = {
    "donoff_downloader": {"file_write", "file_execute"},
    "donoff_interaction": {"file_write", "file_execute"},
}

_VARIANT_TECHNIQUES = {
    "plain": set(),
    "random": {"random"},
    "split": {"split"},
    "encode": {"encode"},
    "logic": {"logic"},
    "combo": {"random", "split", "encode", "logic"},
}


def experiment_E3(corpus_dir: Path, analysis_dir: Path,
                  out_dir: Path) -> Dict[str, Any]:
    """RQ4: how much does obfuscation reduce observability?

    Three measurements per variant:
      * static/dynamic behavior recall against ground truth;
      * obfuscation *detection* (heuristics vs the known variant label);
      * static deobfuscation success (payload recovery).
    """
    gt = _load_gt(corpus_dir)
    by_variant: Dict[str, List[float]] = {}
    by_variant_dyn: Dict[str, List[float]] = {}
    by_family: Dict[str, Dict[str, List[float]]] = {}
    detection: Dict[str, Dict[str, int]] = {}
    deob: Dict[str, List[bool]] = {}
    per_sample = []
    for m in _load_manifest(corpus_dir):
        sid = m["id"]
        if not gt.get(sid):
            continue
        sta = read_json(analysis_dir / "static" / f"{sid}.json")
        dyn = read_json(analysis_dir / "dynamic" / f"{sid}.json")
        s_beh = {e["behavior"] for e in sta["events"]}
        d_beh = {e["behavior"] for e in dyn["events"]}
        g_beh = set(gt[sid]["behaviors"])
        s_recall = len(g_beh & s_beh) / max(len(g_beh), 1)
        d_recall = len(g_beh & d_beh) / max(len(g_beh), 1)
        variant = m["variant"]
        by_variant.setdefault(variant, []).append(s_recall)
        by_variant_dyn.setdefault(variant, []).append(d_recall)
        by_family.setdefault(m["family"], {}).setdefault(
            variant, []).append(s_recall)

        # obfuscation detection vs the variant actually applied. Empty
        # projects have no code to obfuscate, so their variant label is
        # nominal and they are excluded from detection/deobfuscation stats.
        flags = sta.get("meta", {}).get("obfuscation_detected", {}) or {}
        detected = {k for k, v in flags.items() if v}
        expected = _VARIANT_TECHNIQUES[variant]
        if m["family"] != "empty_macro":
            d = detection.setdefault(variant, {"tp": 0, "fp": 0, "fn": 0})
            d["tp"] += len(detected & expected)
            d["fp"] += len(detected - expected)
            d["fn"] += len(expected - detected)

            # deobfuscation: were hidden payloads recovered? Only the
            # recoverable techniques (split/encode/combo) are applicable.
            if variant in ("split", "encode", "combo"):
                recovered = sta.get("meta", {}).get("recovered_payloads", [])
                deob.setdefault(variant, []).append(bool(recovered))

        per_sample.append({
            "id": sid, "family": m["family"], "variant": variant,
            "static_recall": s_recall, "dynamic_recall": d_recall,
            "detected": sorted(detected), "expected": sorted(expected),
            "recovered_payloads": len(sta.get("meta", {})
                                       .get("recovered_payloads", []) or []),
        })

    detection_table = {}
    for var, d in sorted(detection.items()):
        tp, fp, fn = d["tp"], d["fp"], d["fn"]
        detection_table[var] = {
            "precision": tp / max(tp + fp, 1),
            "recall": tp / max(tp + fn, 1),
            "tp": tp, "fp": fp, "fn": fn,
        }
    report = {
        "experiment": "E3",
        "title": "Obfuscation vs observability (RQ4)",
        "static_recall_by_variant": {
            k: {"mean": float(np.mean(v)), "std": float(np.std(v)), "n": len(v)}
            for k, v in sorted(by_variant.items())},
        "dynamic_recall_by_variant": {
            k: {"mean": float(np.mean(v)), "std": float(np.std(v)), "n": len(v)}
            for k, v in sorted(by_variant_dyn.items())},
        "detection_by_variant": detection_table,
        "deobfuscation_success_by_variant": {
            k: {"mean": float(np.mean(v)), "n": len(v)}
            for k, v in sorted(deob.items())},
        "static_recall_by_family_variant": {
            fam: {var: {"mean": float(np.mean(v))}
                  for var, v in sorted(vars.items())}
            for fam, vars in sorted(by_family.items())},
        "per_sample": per_sample,
    }
    write_json(report, out_dir / "E3_obfuscation.json")
    return report


# ---------------------------------------------------------------------------
# E4 — Temporal segmentation (RQ3)
# ---------------------------------------------------------------------------

def _bucket_labels(dom: List[str], buckets: List[List[Event]],
                   labels: List[str]) -> List[str]:
    """Expand per-bucket dominant labels back to one label per event.

    Pk / WindowDiff compare segmentations over the *same* index space, so the
    predicted segmentation (bucket dominance) is expanded to the event level
    where each event carries the dominant label of its bucket. ``labels``
    (the per-event truth) is only used for its length.
    """
    out: List[str] = []
    for i, b in enumerate(buckets):
        out.extend([dom[i] if dom[i] is not None else "benign"] * len(b))
    return out


def _segment_quality(events: List[Event], stage_of: Dict[str, str],
                     n_seg: int) -> Dict[str, float]:
    """Purity, stage concentration, boundary F1 and reference segmentation
    metrics (Pk, WindowDiff) for one segmentation."""
    from collections import Counter

    from oblivionx.telemetry.segment_metrics import pk, windowdiff
    from oblivionx.telemetry.segmentation import segment_events
    labels = [stage_of.get(e.behavior, "benign") for e in events]
    buckets = segment_events(events, n_seg)

    purities, dom = [], []
    for b in buckets:
        if not b:
            dom.append(None)
            continue
        counts = Counter(stage_of.get(e.behavior, "benign") for e in b)
        top_label, top_n = counts.most_common(1)[0]
        purities.append(top_n / len(b))
        dom.append(top_label)

    # stage concentration: share of a stage's events inside its best bucket
    conc = []
    for stage in sorted(set(labels) - {"benign"}):
        per_bucket = [sum(1 for e in b
                          if stage_of.get(e.behavior, "benign") == stage)
                      for b in buckets]
        total = sum(per_bucket)
        if total:
            conc.append(max(per_bucket) / total)

    # boundaries: predicted = dominant label changes between adjacent
    # non-empty buckets; true = segment index of the first event of a stage.
    pred = {i + 1 for i in range(len(dom) - 1)
            if dom[i] is not None and dom[i + 1] is not None
            and dom[i] != dom[i + 1]}
    true = set()
    seg_of_event = []
    for i, b in enumerate(buckets):
        seg_of_event.extend([i] * len(b))
    for i in range(1, len(labels)):
        if labels[i] != labels[i - 1]:
            true.add(seg_of_event[i])

    def _match(predicted, truth, tol=1):
        used, hits = set(), 0
        for p in sorted(predicted):
            for t in sorted(truth):
                if t in used:
                    continue
                if abs(p - t) <= tol:
                    used.add(t)
                    hits += 1
                    break
        return hits

    hits = _match(pred, true)
    precision = hits / max(len(pred), 1)
    recall = hits / max(len(true), 1)
    f1 = 2 * precision * recall / (precision + recall + 1e-9)

    # Reference segmentation metrics over the same event index space.
    hyp = _bucket_labels(dom, buckets, labels)
    k = 2
    return {
        "purity": float(np.mean(purities)) if purities else 0.0,
        "concentration": float(np.mean(conc)) if conc else 0.0,
        "boundary_precision": precision,
        "boundary_recall": recall,
        "boundary_f1": f1,
        "n_true_boundaries": len(true),
        "n_pred_boundaries": len(pred),
        "pk": pk(labels, hyp, k=k),
        "windowdiff": windowdiff(labels, hyp, k=k),
        "window_k": k,
    }


def experiment_E4(corpus_dir: Path, analysis_dir: Path,
                  out_dir: Path) -> Dict[str, Any]:
    """RQ3: does Bon-APT-style temporal segmentation separate stages?

    Sweeps the segment count N (Bon-APT uses 1/5/10/20 and combinations) and
    measures (i) segment purity, (ii) temporal concentration of each attack
    stage, and (iii) F1 of stage-boundary detection against the true stage
    sequence.
    """
    from oblivionx.telemetry.segment_metrics import (
        bic_penalty,
        estimate_change_points,
        null_purity_score,
    )
    from oblivionx.telemetry.segmentation import BONAPT_CONFIGS
    stage_of = {b: BEHAVIOR_DEFS[b].stage for b in BEHAVIOR_DEFS
                if BEHAVIOR_DEFS[b].stage}
    gt = _load_gt(corpus_dir)
    configs = sorted(set(BONAPT_CONFIGS) | {1, 5, 10, 20})
    per_n: Dict[str, List[Dict[str, float]]] = {str(n): [] for n in configs}
    per_sample = []
    cp_rows = []
    for m in _load_manifest(corpus_dir):
        sid = m["id"]
        dyn = read_json(analysis_dir / "dynamic" / f"{sid}.json")
        events = [Event.from_dict(e) for e in dyn["events"]
                  if e.get("t_ms") is not None]
        if len(events) < 2:
            continue
        labels = [stage_of.get(e.behavior, "benign") for e in events]
        row = {"id": sid, "family": m["family"], "variant": m["variant"],
               "n_events": len(events), "by_n": {}}
        for n in configs:
            q = _segment_quality(events, stage_of, n)
            per_n[str(n)].append(q)
            row["by_n"][str(n)] = q
        per_sample.append(row)

        # Change-point estimate of the number of segments, per sample, at
        # the BIC-style penalty. The null distribution is computed once at
        # the informative scale (the best-by-boundary-F1 N, chosen below) so
        # this loop stores only the estimate here.
        pen = bic_penalty(len(events))
        cuts = estimate_change_points(labels, penalty=pen)
        gt_stages = gt.get(sid, {}).get("stages", [])
        cp_rows.append({
            "id": sid, "family": m["family"], "n_events": len(events),
            "n_true_stages": len(gt_stages),
            "n_estimated_segments": len(cuts) + 1,
            "penalty": pen,
        })

    def agg(qs, key):
        return float(np.mean([q[key] for q in qs])) if qs else 0.0

    by_n = {n: {"purity": agg(qs, "purity"),
                "concentration": agg(qs, "concentration"),
                "boundary_f1": agg(qs, "boundary_f1"),
                "boundary_precision": agg(qs, "boundary_precision"),
                "boundary_recall": agg(qs, "boundary_recall"),
                "pk": agg(qs, "pk"),
                "windowdiff": agg(qs, "windowdiff")}
            for n, qs in per_n.items()}
    best_n = max(by_n, key=lambda k: by_n[k]["boundary_f1"])

    # Change-point estimate of the segment count vs the ground-truth stage
    # count (held-out: the estimator never sees the ground truth).
    cp_summary = {}
    if cp_rows:
        err = [abs(r["n_estimated_segments"] - r["n_true_stages"])
               for r in cp_rows]
        cp_summary = {
            "mean_abs_error": float(np.mean(err)),
            "exact_rate": float(np.mean([e == 0 for e in err])),
            "mean_estimated": float(np.mean(
                [r["n_estimated_segments"] for r in cp_rows])),
            "mean_true": float(np.mean([r["n_true_stages"]
                                        for r in cp_rows])),
        }

    # Permutation null for bucket purity at the informative scale: is the
    # observed stage separation better than the same segmentation procedure
    # applied to an order-scrambled trace?
    nulls = []
    for m in _load_manifest(corpus_dir):
        sid = m["id"]
        dyn = read_json(analysis_dir / "dynamic" / f"{sid}.json")
        events = [Event.from_dict(e) for e in dyn["events"]
                  if e.get("t_ms") is not None]
        if len(events) < 2:
            continue
        labels = [stage_of.get(e.behavior, "benign") for e in events]
        nulls.append(null_purity_score(labels, int(best_n), n_perm=50))
    null_summary = {
        "n": len(nulls),
        "mean_observed": float(np.mean([x["observed"] for x in nulls]))
        if nulls else 0.0,
        "mean_null": float(np.mean([x["null_mean"] for x in nulls]))
        if nulls else 0.0,
        "mean_z": float(np.mean([x["z"] for x in nulls])) if nulls else 0.0,
        "share_p_below_0.01": float(np.mean(
            [x["p_value"] < 0.01 for x in nulls])) if nulls else 0.0,
        "n_permutations": 50,
        "n_segments": int(best_n),
    }
    report = {
        "experiment": "E4",
        "title": "Temporal segmentation stage separation (RQ3)",
        "configs": configs,
        "by_n": by_n,
        "best_n_by_boundary_f1": best_n,
        "mean_segment_purity": by_n[best_n]["purity"],
        "change_point_estimate": cp_summary,
        "null_purity": null_summary,
        "per_sample": per_sample,
        "change_points": cp_rows,
    }
    write_json(report, out_dir / "E4_temporal_segmentation.json")
    return report


# ---------------------------------------------------------------------------
# E5 — Controlled ground truth validation
# ---------------------------------------------------------------------------

def experiment_E5(corpus_dir: Path, analysis_dir: Path,
                  out_dir: Path) -> Dict[str, Any]:
    """Controlled ground-truth validation.

    Four independent checks per sample:
      * entry point present in the source (unless the family is empty);
      * every ground-truth behavior has one of its API hints in the source;
      * the ground-truth stage list is a subsequence of the stage ontology;
      * the obfuscation variant is the one the detector recovers.
    """
    from oblivionx.static.deobfuscator import detect_obfuscation
    gt = _load_gt(corpus_dir)
    rows = []
    for m in _load_manifest(corpus_dir):
        sid = m["id"]
        src = corpus_dir / "sources" / m["doc_source"]
        helper = corpus_dir / "sources" / m["helper_source"]
        code = src.read_text(encoding="latin-1", errors="replace") \
            if src.exists() else ""
        if helper.exists():
            code += "\n" + helper.read_text(encoding="latin-1",
                                            errors="replace")
        g = gt[sid]
        entry_ok = ("Sub Document_Open" in code
                    or "Sub Workbook_Open" in code
                    or m["family"] == "empty_macro")

        # Behavior hints are checked on the *plain* template only: the
        # obfuscation transforms deliberately hide literals, and how well
        # they do that is measured by E3, not by a ground-truth check.
        # Behaviors performed by a spawned process (file_write/file_execute
        # in a PowerShell downloader) are intentionally not in the VBA
        # source: the dynamic trace, not the source, is their ground truth.
        missing_hint = []
        if m["variant"] == "plain":
            runtime_only = _RUNTIME_ONLY.get(m["family"], set())
            for b in g["behaviors"]:
                if b in runtime_only:
                    continue
                hints = BEHAVIOR_DEFS[b].vba_hints
                if not hints:
                    continue
                if not any(h.lower() in code.lower() for h in hints):
                    missing_hint.append(b)

        # stage ontology order
        idx = [STAGE_ORDER.index(s) for s in g["stages"]
               if s in STAGE_ORDER]
        stage_order_ok = idx == sorted(idx) and len(idx) == len(g["stages"])

        # obfuscation: a plain sample must not trip any technique. For
        # obfuscated samples the detected set is reported by E3.
        flags = detect_obfuscation(code)
        detected = {k for k, v in flags.items() if v}
        obf_ok = (detected == set()) if m["variant"] == "plain" else True

        rows.append({
            "id": sid, "family": m["family"], "variant": m["variant"],
            "gt_stages": g["stages"], "gt_behaviors": g["behaviors"],
            "entry_point_present": entry_ok,
            "missing_behavior_hints": missing_hint,
            "hint_checked": m["variant"] == "plain",
            "stage_order_ok": stage_order_ok,
            "obfuscation_ok": obf_ok,
            "detected_obfuscation": sorted(detected),
            "source_chars": len(code),
        })

    def rate(key):
        return float(np.mean([bool(r[key]) for r in rows])) if rows else 0.0

    report = {
        "experiment": "E5",
        "title": "Controlled ground truth validation",
        "n_samples": len(rows),
        "checks": {
            "entry_point": rate("entry_point_present"),
            "behavior_hints": float(np.mean(
                [not r["missing_behavior_hints"]
                 for r in rows if r["hint_checked"]]))
            if any(r["hint_checked"] for r in rows) else 0.0,
            "stage_order": rate("stage_order_ok"),
            "obfuscation_label": rate("obfuscation_ok"),
        },
        "n_entry_mismatch": sum(1 for r in rows
                                if not r["entry_point_present"]),
        "n_behavior_hint_mismatch": sum(1 for r in rows
                                        if r["missing_behavior_hints"]),
        "n_stage_order_mismatch": sum(1 for r in rows
                                      if not r["stage_order_ok"]),
        "n_obfuscation_mismatch": sum(1 for r in rows
                                      if not r["obfuscation_ok"]),
        "mismatches": [r for r in rows
                       if not (r["entry_point_present"] and r["stage_order_ok"]
                               and not r["missing_behavior_hints"]
                               and r["obfuscation_ok"])][:20],
        "per_sample": rows,
    }
    write_json(report, out_dir / "E5_ground_truth.json")
    return report


# ---------------------------------------------------------------------------
# E6 — Stage reconstruction (RQ1, RQ5)
# ---------------------------------------------------------------------------

def experiment_E6(corpus_dir: Path, analysis_dir: Path,
                  out_dir: Path) -> Dict[str, Any]:
    gt = _load_gt(corpus_dir)
    metrics = []
    families: Dict[str, List[Dict[str, Any]]] = {}
    for m in _load_manifest(corpus_dir):
        sid = m["id"]
        merged = _merge(analysis_dir, sid, m)
        rec = reconstruct(merged)
        sm = evaluate_sample(merged, rec, gt[sid])
        d = sm.to_dict()
        d["family"] = m["family"]
        d["variant"] = m["variant"]
        metrics.append(d)
        families.setdefault(m["family"], []).append(d)
    sms = [_dict_to_sm(x) for x in metrics]
    success = [_dict_to_sm(x) for x in metrics if x["execution_success"]]
    report = {
        "experiment": "E6",
        "title": "Stage reconstruction (RQ1, RQ5)",
        "aggregate": aggregate(sms),
        "aggregate_execution_success": aggregate(success),
        "by_family": {
            fam: aggregate([_dict_to_sm(x) for x in xs])
            for fam, xs in sorted(families.items())},
        "per_sample": metrics,
    }
    write_json(report, out_dir / "E6_reconstruction.json")
    return report


def _merge(analysis_dir: Path, sid: str, m: Dict[str, Any]) -> SampleAnalysis:
    sta = read_json(analysis_dir / "static" / f"{sid}.json")
    dyn = read_json(analysis_dir / "dynamic" / f"{sid}.json")
    merged = SampleAnalysis(sample_id=sid, family=m["family"],
                            variant=m["variant"], format=m["format"])
    merged.events = [Event.from_dict(e) for e in sta["events"]] + \
        [Event.from_dict(e) for e in dyn["events"]]
    merged.meta = {**sta.get("meta", {}), **dyn.get("meta", {})}
    merged.meta["analysis_time_ms"] = (
        sta.get("meta", {}).get("analysis_time_ms", 0.0)
        + dyn.get("meta", {}).get("analysis_time_ms", 0.0))
    if (sta.get("meta", {}).get("failure")
            and not dyn.get("meta", {}).get("failure")):
        merged.meta["failure"] = sta["meta"]["failure"]
    return merged


def _dict_to_sm(d: Dict[str, Any]):
    from oblivionx.eval.metrics import SampleMetrics
    return SampleMetrics(**{k: d.get(k) for k in SampleMetrics.__dataclass_fields__})


# ---------------------------------------------------------------------------
# E7 — Failure analysis
# ---------------------------------------------------------------------------

def experiment_E7(corpus_dir: Path, analysis_dir: Path,
                  out_dir: Path) -> Dict[str, Any]:
    """Failure analysis: classify why dynamic analysis stops.

    Two configurations are compared against their own ground truth:
      * ``baseline`` — vanilla sandbox: MsgBox gates are not dismissed and
        external software (Outlook, FTP) is unavailable;
      * ``handled``  — Oblivion-X configuration: interaction windows are
        dismissed automatically, external software is still missing.
    The difference isolates failures that interaction handling can recover.
    """
    from collections import Counter

    from oblivionx.simulate.simulator import simulate_sample
    gt = _load_gt(corpus_dir)
    env = {"outlook": False, "ftp": False}

    def run(sid, m, handled):
        return simulate_sample(
            sid, gt[sid], m["family"], m["variant"], m["format"],
            interaction_handled=handled, env_available=env)

    def confusion(rows, expected_key, observed_key="observed_failure"):
        conf: Dict[str, Counter] = {}
        for r in rows:
            exp = r[expected_key] or "none"
            obs = r[observed_key] or "none"
            conf.setdefault(exp, Counter())[obs] += 1
        return {k: dict(v) for k, v in sorted(conf.items())}

    rows = []
    for m in _load_manifest(corpus_dir):
        sid = m["id"]
        base = run(sid, m, handled=False)
        hand = run(sid, m, handled=True)
        stored = read_json(analysis_dir / "dynamic" / f"{sid}.json")
        rows.append({
            "id": sid, "family": m["family"], "variant": m["variant"],
            "observed_failure": hand.meta.get("failure"),
            "baseline_failure": base.meta.get("failure"),
            "stored_failure": stored.get("meta", {}).get("failure"),
            "expected_failure": gt[sid].get("expected_failure_handled"),
            "expected_failure_baseline":
                gt[sid].get("expected_failure_baseline"),
            "expected_failure_handled":
                gt[sid].get("expected_failure_handled"),
            "missing_dependency": hand.meta.get("missing_dependency"),
        })
    for r in rows:
        r["matches_expectation"] = (
            (r["observed_failure"] or "none")
            == (r["expected_failure_handled"] or "none"))
        r["baseline_matches"] = (
            (r["baseline_failure"] or "none")
            == (r["expected_failure_baseline"] or "none"))
        r["stored_matches"] = (
            (r["stored_failure"] or "none")
            == (r["observed_failure"] or "none"))

    recovered = [r for r in rows
                 if (r["baseline_failure"] or "none") != "none"
                 and (r["observed_failure"] or "none") == "none"]
    mism = [r for r in rows if not r["matches_expectation"]]
    failures = Counter(r["observed_failure"] or "none" for r in rows)
    baseline_failures = Counter(r["baseline_failure"] or "none" for r in rows)
    report = {
        "experiment": "E7",
        "title": "Failure analysis",
        "config": {
            "baseline": {"interaction_handled": False,
                         "env_available": env},
            "handled": {"interaction_handled": True,
                        "env_available": env},
        },
        "failure_counts": dict(failures),
        "baseline_failure_counts": dict(baseline_failures),
        "confusion_handled": confusion(rows, "expected_failure_handled"),
        "confusion_baseline": confusion(rows, "expected_failure_baseline",
                                        "baseline_failure"),
        "n_expectation_mismatch": len(mism),
        "n_baseline_mismatch": sum(1 for r in rows
                                   if not r["baseline_matches"]),
        "n_stored_mismatch": sum(1 for r in rows
                                 if not r["stored_matches"]),
        "recovered_by_interaction_handling": len(recovered),
        "interaction_gated_total": sum(
            1 for r in rows
            if (r["expected_failure_baseline"] or "") ==
            "dynamic_interaction"),
        "mismatches": mism[:20],
        "per_sample": rows,
    }
    write_json(report, out_dir / "E7_failures.json")
    return report


# ---------------------------------------------------------------------------
# E8 — Performance / resource analysis
# ---------------------------------------------------------------------------

def experiment_E8(corpus_dir: Path, analysis_dir: Path,
                  out_dir: Path) -> Dict[str, Any]:
    rows = []
    for m in _load_manifest(corpus_dir):
        sid = m["id"]
        sta = read_json(analysis_dir / "static" / f"{sid}.json")
        dyn = read_json(analysis_dir / "dynamic" / f"{sid}.json")
        rows.append({
            "id": sid,
            "family": m["family"],
            "variant": m["variant"],
            "static_time_ms": sta.get("meta", {}).get("analysis_time_ms", 0),
            "dynamic_time_ms": dyn.get("meta", {}).get("analysis_time_ms", 0),
            "total_time_ms": (sta.get("meta", {}).get("analysis_time_ms", 0)
                              + dyn.get("meta", {}).get("analysis_time_ms", 0)),
            "failure": dyn.get("meta", {}).get("failure"),
        })
    times = [r["total_time_ms"] for r in rows]
    n_timeout = sum(1 for r in rows if r["failure"] == "dynamic_timeout")
    by_family: Dict[str, List[float]] = {}
    for r in rows:
        by_family.setdefault(r["family"], []).append(r["total_time_ms"])
    report = {
        "experiment": "E8",
        "title": "Performance / resource analysis",
        "n": len(rows),
        "total_time_ms_mean": float(np.mean(times)) if times else 0,
        "total_time_ms_std": float(np.std(times)) if times else 0,
        "total_time_ms_p50": float(np.percentile(times, 50)) if times else 0,
        "total_time_ms_p95": float(np.percentile(times, 95)) if times else 0,
        "throughput_samples_per_sec": (1000.0 / float(np.mean(times)))
        if times and np.mean(times) > 0 else 0.0,
        "static_time_ms_mean": float(np.mean([r["static_time_ms"] for r in rows])),
        "dynamic_time_ms_mean": float(np.mean([r["dynamic_time_ms"] for r in rows])),
        "by_family_ms_mean": {
            fam: float(np.mean(v)) for fam, v in sorted(by_family.items())},
        "completion_rate": 1 - n_timeout / max(len(rows), 1),
        "timeout_rate": n_timeout / max(len(rows), 1),
        "note": ("dynamic_time_ms is the cost of the deterministic telemetry "
                 "simulator; real Office execution time is reported separately "
                 "when --dynamic-source windows traces are used."),
        "per_sample": rows,
    }
    write_json(report, out_dir / "E8_performance.json")
    return report


# ---------------------------------------------------------------------------
# E9 — Chain-order ablation: ontology order vs evidence (timestamp) order
# ---------------------------------------------------------------------------

def experiment_E9(corpus_dir: Path, analysis_dir: Path,
                  out_dir: Path) -> Dict[str, Any]:
    """RQ5 ablation: is the reconstructed chain ordered by evidence?

    The default reconstructor orders stages by ``STAGE_ORDER``, so a chain
    that matches the ground truth is true by construction. This experiment
    rebuilds every chain from the same events with ``stage_order="timestamp"``
    (stages ordered by the first time each stage was observed) and compares
    the two orderings against the ground-truth chain.

    Reported per mode: stage accuracy (LCS F1), precision, recall, and the
    share of samples whose chain is *identical* to the ground truth (exact
    match). Also reported: how often the two modes disagree, and the family
    breakdown, so the degradation (if any) is attributable.
    """
    gt = _load_gt(corpus_dir)
    modes = ("ontology", "timestamp")
    rows = []
    for m in _load_manifest(corpus_dir):
        sid = m["id"]
        merged = _merge(analysis_dir, sid, m)
        g_stages = list(gt[sid].get("stages", []))
        row = {"id": sid, "family": m["family"], "variant": m["variant"],
               "gt_stages": g_stages, "by_mode": {}}
        for mode in modes:
            rec = reconstruct(merged, stage_order=mode)
            sm = evaluate_sample(merged, rec, gt[sid])
            row["by_mode"][mode] = {
                "chain": rec.chain,
                "stage_accuracy": sm.stage_accuracy,
                "stage_precision": sm.stage_precision,
                "stage_recall": sm.stage_recall,
                "exact_match": rec.chain == " -> ".join(g_stages),
                "n_stages": len(rec.stages),
            }
        row["modes_agree"] = (
            row["by_mode"]["ontology"]["chain"]
            == row["by_mode"]["timestamp"]["chain"])
        rows.append(row)

    def agg(mode: str, key: str) -> float:
        return float(np.mean([r["by_mode"][mode][key] for r in rows])) \
            if rows else 0.0

    summary = {mode: {
        "stage_accuracy": agg(mode, "stage_accuracy"),
        "stage_precision": agg(mode, "stage_precision"),
        "stage_recall": agg(mode, "stage_recall"),
        "exact_match_rate": agg(mode, "exact_match"),
        "mean_stages": agg(mode, "n_stages"),
    } for mode in modes}

    by_family: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        f = by_family.setdefault(r["family"], {"n": 0})
        f["n"] += 1
        for mode in modes:
            f.setdefault(mode, {"stage_accuracy": [], "exact_match": []})
            f[mode]["stage_accuracy"].append(
                r["by_mode"][mode]["stage_accuracy"])
            f[mode]["exact_match"].append(r["by_mode"][mode]["exact_match"])
    family_table = {
        fam: {"n": v["n"], **{
            mode: {
                "stage_accuracy": float(np.mean(v[mode]["stage_accuracy"])),
                "exact_match_rate": float(np.mean(v[mode]["exact_match"])),
            } for mode in modes}}
        for fam, v in sorted(by_family.items())}

    disagreements = [r for r in rows if not r["modes_agree"]]
    report = {
        "experiment": "E9",
        "title": "Chain-order ablation: ontology vs evidence (RQ5)",
        "modes": list(modes),
        "summary": summary,
        "accuracy_delta_timestamp_minus_ontology":
            summary["timestamp"]["stage_accuracy"]
            - summary["ontology"]["stage_accuracy"],
        "n_samples": len(rows),
        "n_mode_disagreements": len(disagreements),
        "mode_disagreements": [
            {"id": r["id"], "family": r["family"],
             "gt": " -> ".join(r["gt_stages"]),
             "ontology": r["by_mode"]["ontology"]["chain"],
             "timestamp": r["by_mode"]["timestamp"]["chain"]}
            for r in disagreements[:40]],
        "by_family": family_table,
        "per_sample": rows,
    }
    write_json(report, out_dir / "E9_chain_order.json")
    return report


# ---------------------------------------------------------------------------
# E10 — Calibration of analysis-completion prediction from static evidence
# ---------------------------------------------------------------------------

# Static-only features. Nothing here names the family, the variant or the
# file format: those are the labels being predicted, so using them would make
# the calibration circular.
E10_FEATURES = [
    "has_outlook_access", "has_outlook_send", "has_ftp_upload",
    "has_msgbox_gate", "has_shell_run", "has_powershell_run",
    "has_http_download", "has_file_execute", "has_registry_write",
    "has_file_encrypt", "has_env_read", "n_obfuscation_behaviors",
    "n_static_events", "log_source_chars", "has_date_gate",
    "has_busy_loop", "n_modules",
]

_OBFUSCATION_BEHAVIORS = ("string_concat", "chr_encode", "base64_encode",
                          "dead_code")


def _static_features(sta: Dict[str, Any], corpus_dir: Path,
                     sample: Dict[str, Any]) -> Dict[str, float]:
    """Features that the static pipeline can compute before any execution."""
    behaviors = {e["behavior"] for e in sta.get("events", [])}
    meta = sta.get("meta", {})

    source = ""
    for key in ("doc_source", "helper_source"):
        rel = sample.get(key)
        if not rel:
            continue
        path = Path(corpus_dir) / "sources" / rel
        if path.exists():
            source += "\n" + path.read_text(encoding="latin-1",
                                            errors="replace")

    has_date_gate = bool(re.search(
        r"(?:Day|Month)\s*\(\s*(?:Date|Now)\s*\)|"
        r"\bDate\s*(?:=|<|>)", source, re.IGNORECASE))
    has_busy_loop = bool(re.search(
        r"For\s+\w+\s*=\s*\d+\s+To\s+\d{5,}|Do\s+While|Loop\s+Until|"
        r"\bSleep\b|\bTimer\b", source, re.IGNORECASE))

    feats: Dict[str, float] = {
        name: float(name.removeprefix("has_") in behaviors)
        for name in E10_FEATURES if name.startswith("has_")}
    feats["n_obfuscation_behaviors"] = float(
        sum(1 for b in _OBFUSCATION_BEHAVIORS if b in behaviors))
    feats["n_static_events"] = float(len(sta.get("events", [])))
    feats["log_source_chars"] = float(np.log1p(len(source)))
    feats["has_date_gate"] = float(has_date_gate)
    feats["has_busy_loop"] = float(has_busy_loop)
    feats["n_modules"] = float(meta.get("n_modules", 0))
    return feats


def experiment_E10(corpus_dir: Path, analysis_dir: Path,
                   out_dir: Path) -> Dict[str, Any]:
    """Can static evidence predict whether the macro will run to completion?

    The unsupported-claim rate is only useful if an analyst can anticipate
    it. This experiment uses *static-only* features (no family, variant or
    format) to predict ``execution_success`` — the macro ran without an
    environment, date or interaction gate — and reports proper scoring rules
    under leave-one-family-out evaluation.

    The honest reading is a two-part result: environment gates are visible in
    the source (Outlook/FTP references) and should calibrate well, while a
    date gate that occurs in exactly one family cannot generalise to unseen
    families and will regress to the base rate. Reporting that split is the
    point of the experiment, not a defect.
    """
    from oblivionx.eval.calibration import (
        LogisticRegression,
        auc,
        brier,
        brier_baseline,
        coefficient_table,
        expected_calibration_error,
        leave_one_family_out,
        quartile_rows,
        reliability_table,
    )

    rows = []
    for m in _load_manifest(corpus_dir):
        sid = m["id"]
        sta = read_json(analysis_dir / "static" / f"{sid}.json")
        dyn = read_json(analysis_dir / "dynamic" / f"{sid}.json")
        rec = read_json(analysis_dir / "reconstruction" / f"{sid}.json")
        feats = _static_features(sta, corpus_dir, m)
        failure = dyn.get("meta", {}).get("failure")
        claims = rec.get("behaviors", [])
        unsupported = (sum(1 for b in claims if not b.get("supported", True))
                       / len(claims)) if claims else 0.0
        rows.append({
            "id": sid,
            "family": m["family"],
            "variant": m["variant"],
            "failure": failure,
            "execution_success": failure is None,
            "unsupported_rate": float(unsupported),
            **{f"f:{name}": feats[name] for name in E10_FEATURES},
        })

    X = [[r[f"f:{name}"] for name in E10_FEATURES] for r in rows]
    y = [1.0 if r["execution_success"] else 0.0 for r in rows]
    families = [r["family"] for r in rows]
    unsupported = [r["unsupported_rate"] for r in rows]

    preds, folds = leave_one_family_out(X, y, families)
    full = LogisticRegression().fit(X, y)
    in_sample = full.predict_proba(X)
    overall = {
        "n": len(rows),
        "base_rate": float(np.mean(y)) if y else 0.0,
        "auc": auc(y, preds.tolist()),
        "brier": brier(y, preds.tolist()),
        "brier_baseline": brier_baseline(y),
        "ece": expected_calibration_error(y, preds.tolist(), bins=10),
        "in_sample_auc": auc(y, in_sample.tolist()),
        "in_sample_brier": brier(y, in_sample.tolist()),
        "bins": 10,
    }
    base = overall["brier_baseline"]
    overall["brier_skill"] = (1.0 - overall["brier"] / base) if base else None
    overall["in_sample_brier_skill"] = (
        1.0 - overall["in_sample_brier"] / base) if base else None

    # Per-family: does the fold's prediction match its observed rate? The
    # family is a diagnostic grouping here, never a model input.
    by_family: Dict[str, Dict[str, Any]] = {}
    fold_of = {f["family"]: f for f in folds}
    for row in rows:
        fam = row["family"]
        entry = by_family.setdefault(fam, {
            "n": 0, "observed_rate": 0.0, "mean_predicted": 0.0,
            "mean_unsupported_rate": 0.0, "failure_counts": {}})
        entry["n"] += 1
        entry["observed_rate"] += (1.0 if row["execution_success"] else 0.0)
        entry["mean_unsupported_rate"] += row["unsupported_rate"]
        key = row["failure"] or "none"
        entry["failure_counts"][key] = entry["failure_counts"].get(key, 0) + 1
    for fam, entry in by_family.items():
        n = entry["n"]
        entry["observed_rate"] /= n
        entry["mean_unsupported_rate"] /= n
        entry["mean_predicted"] = fold_of.get(fam, {}).get(
            "test_mean_predicted", 0.0)

    # Aggregate by failure mechanism. A mechanism that occurs in only one
    # family cannot be learned when that family is held out, so this table
    # separates "predictable because it generalises" from "unique to one
    # family" — the two-part result the experiment is designed to expose.
    by_failure: Dict[str, Dict[str, Any]] = {}
    for row, pred in zip(rows, preds, strict=True):
        key = row["failure"] or "none"
        entry = by_failure.setdefault(key, {
            "n": 0, "families": set(), "observed_rate": 0.0,
            "mean_predicted": 0.0})
        entry["n"] += 1
        entry["families"].add(row["family"])
        entry["observed_rate"] += 1.0 if row["execution_success"] else 0.0
        entry["mean_predicted"] += float(pred)
    for entry in by_failure.values():
        entry["observed_rate"] /= entry["n"]
        entry["mean_predicted"] /= entry["n"]
        entry["n_families"] = len(entry["families"])
        entry["families"] = sorted(entry["families"])

    coefficients = sorted(coefficient_table(E10_FEATURES, full),
                          key=lambda c: (-abs(c["weight"]), c["feature"]))

    report = {
        "experiment": "E10",
        "title": ("Calibration of analysis-completion prediction from "
                  "static evidence"),
        "label": ("execution_success: the macro ran without an "
                  "environment/date/interaction gate"),
        "features": E10_FEATURES,
        "evaluation": "leave-one-family-out (family never a model input)",
        "overall": overall,
        "reliability": reliability_table(y, preds.tolist(), bins=10),
        "by_family": dict(sorted(by_family.items())),
        "by_failure": dict(sorted(by_failure.items())),
        "folds": folds,
        "unsupported_rate_by_predicted_quartile": quartile_rows(
            y, preds.tolist(), extra=unsupported,
            name="mean_unsupported_rate"),
        "coefficients": coefficients,
        "per_sample": [dict(row, predicted_completion=float(pred))
                       for row, pred in zip(rows, preds, strict=True)],
    }
    write_json(report, out_dir / "E10_completion_calibration.json")
    return report


EXPERIMENTS = {
    "E1": experiment_E1,
    "E2": experiment_E2,
    "E3": experiment_E3,
    "E4": experiment_E4,
    "E5": experiment_E5,
    "E6": experiment_E6,
    "E7": experiment_E7,
    "E8": experiment_E8,
    "E9": experiment_E9,
    "E10": experiment_E10,
}


def run_all(corpus_dir: Path, analysis_dir: Path,
            out_dir: Path) -> Dict[str, Dict[str, Any]]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, fn in EXPERIMENTS.items():
        t0 = time.time()
        report = fn(corpus_dir, analysis_dir, out_dir)
        report["wall_time_s"] = time.time() - t0
        results[name] = report
        print(f"  {name}: {report.get('title')} ({report['wall_time_s']:.1f}s)")
    return results
