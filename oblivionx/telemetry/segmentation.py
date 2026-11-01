"""Bon-APT temporal segmentation (reimplementation).

Splits the timestamped event stream of a sample into N equal-length time
segments and aggregates per-feature (behavior/API) frequencies per segment:

    freq(feature, seg) = count(feature, seg) / count(feature, total)

The flattened N*D vector is the representation Bon-APT feeds to ML, and the
per-segment behavior distribution powers the stage-separation analysis
(RQ3/E4) and the explainability output (low/medium/high discretization).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

from oblivionx.telemetry.schema import Event, SampleAnalysis


def segment_events(events: List[Event], n_segments: int,
                   t0: Optional[int] = None,
                   t_end: Optional[int] = None) -> List[List[Event]]:
    """Split timestamped events into n equal-length time buckets."""
    timed = [e for e in events if e.t_ms is not None]
    if not timed:
        return [[] for _ in range(n_segments)]
    lo = t0 if t0 is not None else min(e.t_ms for e in timed)
    hi = t_end if t_end is not None else max(e.t_ms for e in timed)
    span = max(hi - lo, 1)
    buckets: List[List[Event]] = [[] for _ in range(n_segments)]
    for e in timed:
        idx = int((e.t_ms - lo) / span * n_segments)
        if idx >= n_segments:
            idx = n_segments - 1
        if idx < 0:
            idx = 0
        buckets[idx].append(e)
    return buckets


def segment_frequencies(events: List[Event], n_segments: int,
                        features: Optional[List[str]] = None
                        ) -> Tuple[Dict[str, np.ndarray], List[str]]:
    """Return {feature: array(n) of segment frequencies} and the feature
    list. Frequency = count in segment / total count of the feature
    (Bon-APT's normalization)."""
    if features is None:
        features = sorted({e.behavior for e in events if e.t_ms is not None})
    total: Dict[str, int] = {}
    per_seg: List[Dict[str, int]] = [{} for _ in range(n_segments)]
    for e in events:
        if e.t_ms is None:
            continue
        total[e.behavior] = total.get(e.behavior, 0) + 1
    buckets = segment_events(events, n_segments)
    for i, bucket in enumerate(buckets):
        for e in bucket:
            per_seg[i][e.behavior] = per_seg[i].get(e.behavior, 0) + 1
    out: Dict[str, np.ndarray] = {}
    for f in features:
        tot = total.get(f, 0)
        arr = np.zeros(n_segments)
        if tot > 0:
            for i in range(n_segments):
                arr[i] = per_seg[i].get(f, 0) / tot
        out[f] = arr
    return out, features


def flatten(freqs: Dict[str, np.ndarray], features: List[str],
            n_segments: int) -> np.ndarray:
    """Flatten to the N*D feature vector (Bon-APT representation)."""
    vec = np.zeros(n_segments * len(features))
    for j, f in enumerate(features):
        vec[j * n_segments:(j + 1) * n_segments] = freqs[f]
    return vec


BONAPT_CONFIGS = [1, 5, 10, 20]


def build_bonapt_features(sa: SampleAnalysis,
                          configs: Optional[List[int]] = None,
                          combos: Optional[List[Tuple[int, int]]] = None
                          ) -> Dict[str, np.ndarray]:
    """Build Bon-APT segmentation features for a sample analysis.

    Returns {config_label: flattened vector}. Default: single configs 1, 5,
    10, 20 plus the 1+5, 1+10, 1+20 combinations (paper Section 6.4).
    """
    configs = configs or BONAPT_CONFIGS
    combos = combos or [(1, 5), (1, 10), (1, 20)]
    events = sa.dynamic_events() or sa.events
    features = sorted({e.behavior for e in events if e.t_ms is not None})
    out: Dict[str, np.ndarray] = {}
    for n in configs:
        freqs, _ = segment_frequencies(events, n, features)
        out[str(n)] = flatten(freqs, features, n)
    for a, b in combos:
        fa, _ = segment_frequencies(events, a, features)
        fb, _ = segment_frequencies(events, b, features)
        out[f"{a}+{b}"] = np.concatenate([flatten(fa, features, a),
                                          flatten(fb, features, b)])
    return out


def explainability_profile(events: List[Event], n_segments: int = 10,
                           behavior_categories: Optional[Dict[str, str]] = None
                           ) -> Dict[str, List[str]]:
    """Bon-APT-style explainability: per behavior category, per segment,
    sum frequencies -> min-max scale -> equal-width discretize into
    low/medium/high (paper Section 7.4)."""
    if behavior_categories is None:
        from oblivionx.common import behavior_bonapt
        behavior_categories = {b: behavior_bonapt(b) for b in
                               {e.behavior for e in events}}
    categories = sorted(set(behavior_categories.values()))
    freqs, _ = segment_frequencies(events, n_segments)
    profile: Dict[str, List[str]] = {}
    for cat in categories:
        cat_features = [f for f in freqs if behavior_categories.get(f) == cat]
        if not cat_features:
            profile[cat] = ["low"] * n_segments
            continue
        summed = np.zeros(n_segments)
        for f in cat_features:
            summed += freqs[f]
        mn, mx = summed.min(), summed.max()
        if mx - mn < 1e-12:
            profile[cat] = ["low"] * n_segments
            continue
        # equal-width discretization into 3 bins
        width = (mx - mn) / 3
        profile[cat] = [
            "low" if v < mn + width else
            "medium" if v < mn + 2 * width else "high"
            for v in summed]
    return profile
