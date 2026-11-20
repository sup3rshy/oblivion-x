"""Reference segmentation metrics: Pk, WindowDiff, change points, null test."""
import pytest

from oblivionx.telemetry.segment_metrics import (
    bic_penalty,
    bucket_purity,
    estimate_change_points,
    null_purity_score,
    pk,
    windowdiff,
)


# ---- Pk / WindowDiff ------------------------------------------------------
def test_perfect_segmentation_scores_zero():
    ref = ["a", "a", "a", "b", "b", "b"]
    assert pk(ref, ref, k=2) == 0.0
    assert windowdiff(ref, ref, k=2) == 0.0


def test_no_boundaries_scores_half():
    # truth has one boundary, hypothesis has none: only the windows that
    # straddle the true boundary at index 3 disagree.
    ref = ["a", "a", "a", "b", "b", "b"]
    hyp = ["a"] * 6
    assert pk(ref, hyp, k=2) == pytest.approx(2 / 4)
    assert windowdiff(ref, hyp, k=2) == pytest.approx(2 / (4 * 2))


def test_moved_boundary_is_penalized():
    ref = ["a", "a", "b", "b", "b", "b"]
    hyp = ["a", "a", "a", "b", "b", "b"]
    assert pk(ref, hyp, k=2) > 0.0
    assert windowdiff(ref, hyp, k=2) > 0.0


def test_mismatched_lengths_are_rejected():
    with pytest.raises(ValueError):
        pk(["a", "b"], ["a"], k=2)
    with pytest.raises(ValueError):
        windowdiff(["a", "b"], ["a"], k=2)


def test_short_sequence_is_vacuously_perfect():
    assert pk(["a"], ["a"], k=2) == 0.0
    assert windowdiff(["a", "a"], ["a", "b"], k=2) == 0.0


# ---- change-point estimation ---------------------------------------------
def test_change_point_found_at_the_true_boundary():
    labels = ["a"] * 3 + ["b"] * 3 + ["c"] * 4
    cuts = estimate_change_points(labels, penalty=1.0)
    assert cuts == [3, 6]


def test_uniform_sequence_has_no_change_points():
    assert estimate_change_points(["a"] * 10, penalty=1.0) == []


def test_penalty_suppresses_weak_change_points():
    # one noise event in the middle gives a gain of 1; a penalty of 2
    # must reject it.
    labels = ["a"] * 5 + ["b"] + ["a"] * 5
    assert estimate_change_points(labels, penalty=3.0) == []


def test_change_points_are_returned_in_order():
    labels = ["a"] * 4 + ["b"] * 4 + ["c"] * 4 + ["d"] * 4
    cuts = estimate_change_points(labels, penalty=1.0)
    assert cuts == sorted(cuts)
    assert len(cuts) == 3


def test_bic_penalty_grows_with_length():
    assert bic_penalty(100) > bic_penalty(10) > 0


# ---- bucket purity and permutation null ----------------------------------
def test_bucket_purity_is_one_for_a_pure_partition():
    assert bucket_purity(["a", "a", "b", "b"], 2) == 1.0


def test_bucket_purity_reflects_dominant_label_share():
    # n=10, 2 buckets of 5: each bucket has 3 "a" + 2 "b" (or vice versa),
    # so mean purity is 3/5.
    assert bucket_purity(["a", "b"] * 5, 2) == pytest.approx(0.6)


def test_order_information_beats_the_shuffled_null():
    labels = ["a"] * 10 + ["b"] * 10 + ["c"] * 10
    result = null_purity_score(labels, n_segments=3, n_perm=200, seed=0)
    assert result["observed"] == 1.0
    assert result["z"] > 3
    assert result["p_value"] < 0.01


def test_orderless_labels_are_indistinguishable_from_the_null():
    labels = ["a", "b", "c"] * 10
    result = null_purity_score(labels, n_segments=3, n_perm=200, seed=0)
    # observed purity equals any permutation's purity up to sampling noise
    assert abs(result["observed"] - result["null_mean"]) < 0.15
    assert result["p_value"] > 0.05
