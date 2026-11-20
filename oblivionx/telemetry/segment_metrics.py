"""Reference metrics for temporal segmentation (E4).

The boundary F1 in ``eval.experiments`` gives credit for a predicted boundary
within one bucket of a true one, which is convenient but not comparable with
the text-segmentation literature and is not corrected for chance. This module
adds the standard measures:

  * **Pk** (Beeferman et al., 1999): probability that a probe window of width
    k straddles a boundary in one segmentation but not the other. 0 is
    perfect; lower is better.
  * **WindowDiff** (Pevzner & Hearst, 2002): like Pk but compares the number
    of boundaries inside the window instead of just their presence. Lower is
    better.
  * **Change-point estimation** (``estimate_change_points``): a greedy
    likelihood search with an MDL penalty, used to answer "how many stages
    does this trace actually contain?" rather than sweeping a fixed N.
  * **Permutation null** (``null_boundary_f1``): shuffles event order and
    recomputes a boundary score, so an observed score can be compared with
    what the same segmentation procedure earns on orderless data.

All functions operate on a 1-D label sequence (one label per event); the
caller is responsible for turning events into labels.
"""
from __future__ import annotations

import random
from collections import Counter
from math import log
from typing import Dict, List, Sequence

_EPS = 1e-12


def _boundaries(labels: Sequence[str]) -> List[int]:
    """Indices i (1 <= i < n) where labels[i] != labels[i-1]."""
    return [i for i in range(1, len(labels)) if labels[i] != labels[i - 1]]


def _count_in_window(boundaries: Sequence[int], start: int,
                     end: int) -> int:
    """Number of boundaries b with start < b <= end (window semantics of
    Pevzner & Hearst: a boundary belongs to the window spanning positions
    [start, end])."""
    return sum(1 for b in boundaries if start < b <= end)


def pk(ref: Sequence[str], hyp: Sequence[str], k: int = 2) -> float:
    """Pk: proportion of windows whose boundary presence disagrees."""
    n = len(ref)
    if n != len(hyp):
        raise ValueError("label sequences must have equal length")
    if n <= k:
        return 0.0
    rb, hb = _boundaries(ref), _boundaries(hyp)
    errors = 0
    for i in range(n - k):
        # a boundary "exists" in [i, i+k] iff one of its indices is in
        # (i, i+k]; with 0-based labels a boundary at j separates j-1 and j
        r_has = _count_in_window(rb, i, i + k) > 0
        h_has = _count_in_window(hb, i, i + k) > 0
        errors += int(r_has != h_has)
    return errors / (n - k)


def windowdiff(ref: Sequence[str], hyp: Sequence[str], k: int = 2) -> float:
    """WindowDiff: mean |#boundaries in window| discrepancy, normalized by k."""
    n = len(ref)
    if n != len(hyp):
        raise ValueError("label sequences must have equal length")
    if n <= k:
        return 0.0
    rb, hb = _boundaries(ref), _boundaries(hyp)
    errors = 0
    for i in range(n - k):
        errors += abs(_count_in_window(rb, i, i + k)
                      - _count_in_window(hb, i, i + k))
    return errors / ((n - k) * k)


def estimate_change_points(labels: Sequence[str],
                           penalty: float = 2.0,
                           max_points: int = 12,
                           grid: int = 16) -> List[int]:
    """Greedy maximum-likelihood change-point search with an MDL penalty.

    Segment score is ``#events in the segment belonging to its dominant
    label`` (purity count); a split adds
    ``purity(left) + purity(right) - purity(whole)``. A split is accepted only
    if that gain exceeds ``penalty``, and the best split is added at each
    round until no split improves the score by more than the penalty.
    ``len(result) + 1`` is the estimated segment count.

    Candidate cuts are restricted to ``grid`` evenly spaced positions, which
    keeps the search linear in the number of events and avoids fitting
    artefact boundaries at individual events. Noise events carry a low
    confidence weight: the caller should drop them before labelling (the
    label sequence this function sees is the one used by the rest of E4).
    """
    n = len(labels)
    if n <= 1:
        return []
    step = max(1, n // max(grid, 1))
    candidates = sorted(set(range(step, n, step)) | {n - 1})

    def purity(start: int, end: int) -> int:
        if end <= start:
            return 0
        return Counter(labels[start:end]).most_common(1)[0][1]

    cuts: List[int] = []
    bounds = [0, n]
    for _ in range(max_points):
        best_gain, best_cut = penalty, None
        for si in range(len(bounds) - 1):
            s, e = bounds[si], bounds[si + 1]
            base = purity(s, e)
            for cut in candidates:
                if not s < cut < e:
                    continue
                gain = purity(s, cut) + purity(cut, e) - base
                if gain > best_gain:
                    best_gain, best_cut = gain, cut
        if best_cut is None:
            break
        cuts.append(best_cut)
        bounds = sorted(bounds + [best_cut])
    return sorted(cuts)


def null_purity_score(labels: Sequence[str],
                      n_segments: int,
                      n_perm: int = 50,
                      seed: int = 0) -> Dict[str, float]:
    """Permutation null for bucket purity.

    The observed statistic is the mean purity of ``n_segments`` equal-count
    buckets over the real label order. The null is built by shuffling the
    *label sequence* (keeping bucket sizes and the label multiset) so the
    comparison isolates order information: if stages did not separate in
    time, shuffled and real traces would score the same.

    Returns observed purity, null mean/std, z-score and the one-sided
    empirical p-value ``(1 + #{null >= observed}) / (1 + n_perm)``.
    """
    observed = bucket_purity(labels, n_segments)
    rng = random.Random(seed)
    shuffled = list(labels)
    null: List[float] = []
    for _ in range(n_perm):
        rng.shuffle(shuffled)
        null.append(bucket_purity(shuffled, n_segments))
    mean = sum(null) / len(null) if null else 0.0
    var = (sum((x - mean) ** 2 for x in null) / len(null)) if null else 0.0
    std = var ** 0.5
    z = (observed - mean) / std if std > _EPS else 0.0
    exceed = sum(1 for x in null if x >= observed)
    return {"observed": observed, "null_mean": mean, "null_std": std,
            "z": z, "p_value": (1 + exceed) / (1 + n_perm),
            "n_permutations": n_perm}


def bucket_purity(labels: Sequence[str], n_segments: int) -> float:
    """Mean purity of ``n_segments`` equal-count buckets (event order)."""
    n = len(labels)
    if n == 0 or n_segments <= 0:
        return 0.0
    step = n / n_segments
    total = 0.0
    for i in range(n_segments):
        start = int(round(i * step))
        end = int(round((i + 1) * step))
        if end <= start:
            continue
        segment = labels[start:end]
        total += Counter(segment).most_common(1)[0][1] / len(segment)
    return total / n_segments


def bic_penalty(n_events: int) -> float:
    """BIC-style MDL penalty for one change point (0.5 * log n)."""
    return 0.5 * log(max(n_events, 2))
