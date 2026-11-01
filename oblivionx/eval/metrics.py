"""The eight metrics from the project plan (Section 5).

 1. Behavior Recall       |reconstructed ∩ GT| / |GT|
 2. Evidence Precision    matched evidence items / claimed evidence items
 3. Stage accuracy        correctly reconstructed stages (ordered)
 4. Analysis completion   fraction of samples with a full analysis
 5. Timeout rate          fraction exceeding the time limit
 6. Deobfuscation success fraction of obfuscated samples whose hidden
                          payloads were recovered
 7. Analysis time/sample  mean ± std of per-sample analysis time
 8. Unsupported behavior  fraction of behavior claims without direct
    claim rate            telemetry evidence
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from oblivionx.common import BEHAVIOR_DEFS, STAGE_ORDER
from oblivionx.telemetry.schema import Reconstruction, SampleAnalysis


@dataclass
class SampleMetrics:
    sample_id: str
    behavior_recall: float = 0.0
    evidence_precision: float = 1.0
    stage_accuracy: float = 0.0
    stage_precision: float = 0.0
    stage_recall: float = 0.0
    completed: bool = True
    timed_out: bool = False
    execution_success: bool = True
    deobfuscation_success: Optional[bool] = None
    analysis_time_ms: float = 0.0
    unsupported_rate: float = 0.0
    behavior_precision: float = 0.0
    failure: Optional[str] = None
    gt_behaviors: int = 0
    rec_behaviors: int = 0
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


def lcs_length(a: List[str], b: List[str]) -> int:
    """Longest common subsequence length (order-preserving alignment)."""
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b, 1):
            cur.append(prev[j - 1] + 1 if x == y else max(prev[j], cur[-1]))
        prev = cur
    return prev[-1]


def _stage_label_scores(gt_stages: List[str], rec: Reconstruction
                        ) -> Tuple[float, float, float]:
    """Ordered stage matching via LCS.

    Exact positional matching is too strict: a reconstruction that misses a
    middle stage but keeps the remaining stages in order should not score 0
    for every later stage. LCS measures how much of the ordered chain is
    preserved; precision/recall are relative to the reconstructed and the
    ground-truth chain respectively, and accuracy is their F1.
    """
    rec_stages = [s.stage for s in rec.stages]
    if not gt_stages and not rec_stages:
        return 1.0, 1.0, 1.0
    if not gt_stages or not rec_stages:
        return 0.0, 0.0, 0.0
    hit = lcs_length(gt_stages, rec_stages)
    precision = hit / len(rec_stages)
    recall = hit / len(gt_stages)
    acc = 2 * precision * recall / (precision + recall + 1e-9)
    return acc, precision, recall


def evaluate_sample(sa: SampleAnalysis, rec: Reconstruction,
                    ground_truth: Dict[str, Any],
                    time_limit_ms: float = 120000.0) -> SampleMetrics:
    gt = ground_truth
    gt_behaviors = set(gt.get("behaviors", []))
    gt_stages = gt.get("stages", [])

    m = SampleMetrics(sample_id=sa.sample_id)
    m.gt_behaviors = len(gt_behaviors)
    m.rec_behaviors = len(rec.behaviors)

    # 1. behavior recall. An empty ground truth is vacuously recalled (the
    # false-positive side is measured by behavior precision).
    rec_behaviors = {b.behavior for b in rec.behaviors}
    if gt_behaviors:
        m.behavior_recall = len(rec_behaviors & gt_behaviors) / len(gt_behaviors)
    else:
        m.behavior_recall = 1.0

    # 2. evidence precision: fraction of behavior claims backed by >=1 event
    if rec.behaviors:
        m.evidence_precision = sum(1 for b in rec.behaviors if b.evidence) \
            / len(rec.behaviors)
        m.behavior_precision = (len(rec_behaviors & gt_behaviors)
                                / len(rec_behaviors))
    else:
        m.behavior_precision = 1.0

    # 3. stage accuracy (ordered)
    acc, prec, recall = _stage_label_scores(gt_stages, rec)
    m.stage_accuracy = acc
    m.stage_precision = prec
    m.stage_recall = recall

    # 4/5. completion, timeout and execution success.
    # A semantic error, a missing dependency, a date gate or an interaction
    # gate are *analysis results*: the pipeline still reconstructs the
    # observable prefix. Only a timeout or a crashed/unreadable sample makes
    # the analysis itself incomplete.
    failure = sa.meta.get("failure")
    m.failure = failure
    m.timed_out = failure == "dynamic_timeout"
    m.completed = failure not in ("dynamic_timeout", "crash", "static_error",
                                  "static_corrupted")
    m.execution_success = failure is None

    # 6. deobfuscation success. Only split/encode/combo hide recoverable
    # payloads; random identifiers and logic dead code do not, so they are
    # not applicable (None) rather than failures.
    variant = sa.variant
    if variant in ("split", "encode", "combo"):
        recovered = sa.meta.get("recovered_payloads", []) or []
        # Success = at least one hidden literal was recovered. This matches
        # the per-variant measure in E3.
        m.deobfuscation_success = bool(recovered)
        m.detail["recovered_count"] = len(recovered)

    # 7. analysis time
    m.analysis_time_ms = sa.meta.get("analysis_time_ms",
                                     sa.meta.get("duration_ms", 0.0))

    # 8. unsupported behavior claim rate
    if rec.behaviors:
        m.unsupported_rate = sum(1 for b in rec.behaviors
                                 if not b.supported) / len(rec.behaviors)
    return m


def aggregate(metrics: List[SampleMetrics]) -> Dict[str, Any]:
    """Aggregate sample metrics into report statistics."""
    if not metrics:
        return {}
    def mean(f): return float(np.mean([getattr(x, f) for x in metrics]))
    def std(f): return float(np.std([getattr(x, f) for x in metrics]))
    times = [m.analysis_time_ms for m in metrics if m.analysis_time_ms > 0]
    out = {
        "n": len(metrics),
        "behavior_recall": mean("behavior_recall"),
        "behavior_precision": mean("behavior_precision"),
        "evidence_precision": mean("evidence_precision"),
        "stage_accuracy": mean("stage_accuracy"),
        "stage_precision": mean("stage_precision"),
        "stage_recall": mean("stage_recall"),
        "completion_rate": mean("completed"),
        "execution_success_rate": mean("execution_success"),
        "timeout_rate": mean("timed_out"),
        "analysis_time_ms_mean": float(np.mean(times)) if times else 0.0,
        "analysis_time_ms_std": float(np.std(times)) if times else 0.0,
        "unsupported_claim_rate": mean("unsupported_rate"),
    }
    deob = [m.deobfuscation_success for m in metrics
            if m.deobfuscation_success is not None]
    out["deobfuscation_success"] = (float(np.mean(deob)) if deob
                                    else None)
    return out
