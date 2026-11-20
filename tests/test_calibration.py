"""Calibration utilities used by E10."""
import numpy as np
import pytest

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


def test_logistic_learns_a_separable_direction():
    X = [[0.0], [0.0], [1.0], [1.0]]
    y = [0.0, 0.0, 1.0, 1.0]
    model = LogisticRegression(l2=0.0, lr=1.0, iters=5000).fit(X, y)
    probs = model.predict_proba([[0.0], [1.0]])
    assert probs[0] < 0.5 < probs[1]
    assert probs[0] < 0.05 and probs[1] > 0.95


def test_single_class_fold_predicts_the_base_rate():
    model = LogisticRegression().fit([[0.0], [1.0], [2.0]], [1.0, 1.0, 1.0])
    assert model.predict_proba([[0.0], [9.0]]) == \
        pytest.approx([1.0, 1.0], abs=1e-4)
    model = LogisticRegression().fit([[0.0], [1.0]], [0.0, 0.0])
    assert model.predict_proba([[9.0]])[0] < 1e-4


def test_unfitted_model_is_rejected():
    with pytest.raises(RuntimeError):
        LogisticRegression().predict_proba([[0.0]])


def test_auc_bounds_and_ties():
    assert auc([0, 1], [0.1, 0.9]) == 1.0
    assert auc([0, 1], [0.9, 0.1]) == 0.0
    assert auc([0, 1], [0.5, 0.5]) == 0.5
    assert auc([0, 1], [0.2, 0.8]) == pytest.approx(1.0)


def test_auc_is_none_with_a_single_class():
    assert auc([1, 1], [0.2, 0.7]) is None


def test_brier_and_baseline():
    y = [0.0, 1.0]
    assert brier(y, [0.0, 1.0]) == 0.0
    assert brier(y, [1.0, 0.0]) == 1.0
    # the base-rate predictor is the reference the skill score uses
    assert brier_baseline(y) == pytest.approx(0.25)


def test_ece_is_zero_for_a_perfect_forecast():
    y = [0.0] * 10 + [1.0] * 10
    p = [0.0] * 10 + [1.0] * 10
    assert expected_calibration_error(y, p, bins=10) == 0.0


def test_ece_detects_overconfidence():
    # all predictions say 0.9, only half the cases are positive
    y = [1.0] * 50 + [0.0] * 50
    p = [0.9] * 100
    assert expected_calibration_error(y, p, bins=10) == pytest.approx(0.4)


def test_reliability_bins_cover_every_sample_once():
    y = [0.0, 0.0, 1.0, 1.0]
    p = [0.05, 0.2, 0.8, 0.95]
    table = reliability_table(y, p, bins=10)
    assert sum(row["n"] for row in table) == 4
    assert all(row["bin_lo"] <= row["mean_predicted"] <= row["bin_hi"]
               for row in table)


def test_leave_one_family_out_predicts_each_sample_once():
    X = [[0.0], [1.0], [2.0], [3.0], [4.0], [5.0]]
    y = [1.0, 0.0, 1.0, 0.0, 1.0, 0.0]
    families = ["a", "a", "b", "b", "c", "c"]
    preds, folds = leave_one_family_out(X, y, families, iters=200)
    assert len(preds) == len(y)
    assert sum(f["n_test"] for f in folds) == len(y)
    assert {f["family"] for f in folds} == {"a", "b", "c"}
    assert all(0.0 <= p <= 1.0 for p in preds)


def test_leave_one_family_out_records_single_class_folds():
    X = [[0.0], [1.0], [2.0], [3.0], [4.0]]
    y = [1.0, 1.0, 0.0, 0.0, 1.0]
    families = ["majority", "majority", "rare", "rare", "other"]
    _, folds = leave_one_family_out(X, y, families, iters=100)
    by_family = {f["family"]: f for f in folds}
    # holding out "rare" leaves [1, 1, 1] in training: one class only
    assert by_family["rare"]["single_class"] is True
    assert by_family["majority"]["single_class"] is False
    assert by_family["other"]["single_class"] is False


def test_quartiles_partition_the_samples():
    y = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    p = [0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9]
    rows = quartile_rows(y, p, extra=[1.0] * 8, name="unsupported")
    assert sum(row["n"] for row in rows) == 8
    assert all("unsupported" in row for row in rows)
    assert rows == sorted(rows, key=lambda r: r["quartile"])


def test_coefficient_table_matches_the_feature_count():
    model = LogisticRegression().fit([[0.0, 1.0], [1.0, 0.0]],
                                     [0.0, 1.0])
    table = coefficient_table(["a", "b"], model)
    assert [row["feature"] for row in table] == ["a", "b"]
    assert np.isfinite([row["weight"] for row in table]).all()
