"""Calibration utilities for predicting analysis completion (E10).

The projector-side question behind the unsupported-claim rate is: *before*
running a sample, can static evidence tell us whether the macro will run to
completion, and therefore whether later stages can ever be observed?  E10
fits a small logistic model on static-only features and reports proper
scoring rules:

  * **AUC** — ranking quality;
  * **Brier score** — mean squared error of the probabilities, compared with
    a base-rate baseline (negative skill means the model is worse than always
    predicting the base rate);
  * **ECE / reliability table** — expected calibration error over equal-width
    probability bins, so "0.8" is checked against the observed frequency;
  * **leave-one-family-out** evaluation — a family held out from training is
    predicted by the rest, which prevents the model from memorising the
    family label and shows whether the signal generalises across families.

The implementation is deliberately dependency-free (numpy only) and
deterministic: fixed iteration count, no random initialisation, no shuffling.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

_EPS = 1e-9


def _sigmoid(z: np.ndarray) -> np.ndarray:
    out = np.empty_like(z)
    pos = z >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-z[pos]))
    ez = np.exp(z[~pos])
    out[~pos] = ez / (1.0 + ez)
    return out


class LogisticRegression:
    """L2-regularised logistic regression fitted by gradient descent.

    Features are standardised on the training fold; the intercept is not
    regularised. A single-class training fold degenerates to the base rate
    (intercept only), which is the correct fallback for leave-one-family-out
    folds where every remaining family completed or every one failed.
    """

    def __init__(self, l2: float = 1.0, lr: float = 0.5,
                 iters: int = 3000):
        self.l2 = float(l2)
        self.lr = float(lr)
        self.iters = int(iters)
        self.mean_: Optional[np.ndarray] = None
        self.std_: Optional[np.ndarray] = None
        self.w_: Optional[np.ndarray] = None

    def fit(self, X: Sequence[Sequence[float]],
            y: Sequence[float]) -> "LogisticRegression":
        Xa = np.asarray(X, dtype=float)
        ya = np.asarray(y, dtype=float)
        n, d = Xa.shape
        self.mean_ = Xa.mean(axis=0) if n else np.zeros(d)
        std = Xa.std(axis=0) if n else np.ones(d)
        std = np.where(std < 1e-12, 1.0, std)
        self.std_ = std
        Z = np.hstack([np.ones((n, 1)), (Xa - self.mean_) / std])
        self.w_ = np.zeros(d + 1)
        if n == 0 or len(set(ya.tolist())) < 2:
            p = float(ya.mean()) if n else 0.0
            p = min(max(p, 1e-6), 1 - 1e-6)
            self.w_[0] = float(np.log(p / (1 - p)))
            return self
        for _ in range(self.iters):
            p = _sigmoid(Z @ self.w_)
            grad = Z.T @ (p - ya) / n
            grad[1:] += self.l2 * self.w_[1:] / n
            self.w_ -= self.lr * grad
        return self

    def predict_proba(self, X: Sequence[Sequence[float]]) -> np.ndarray:
        if self.w_ is None:
            raise RuntimeError("model is not fitted")
        Xa = np.asarray(X, dtype=float)
        Z = np.hstack([np.ones((len(Xa), 1)),
                       (Xa - self.mean_) / self.std_])
        return _sigmoid(Z @ self.w_)


def auc(y_true: Sequence[float], scores: Sequence[float]) -> Optional[float]:
    """Rank-based AUC (Mann–Whitney U), ties counted as half."""
    y = np.asarray(y_true, dtype=float)
    s = np.asarray(scores, dtype=float)
    pos, neg = s[y == 1], s[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return None
    greater = float(np.mean(pos[:, None] > neg[None, :]))
    ties = float(np.mean(pos[:, None] == neg[None, :]))
    return greater + 0.5 * ties


def brier(y_true: Sequence[float], probs: Sequence[float]) -> float:
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(probs, dtype=float)
    if len(y) == 0:
        return 0.0
    return float(np.mean((p - y) ** 2))


def brier_baseline(y_true: Sequence[float]) -> float:
    y = np.asarray(y_true, dtype=float)
    if len(y) == 0:
        return 0.0
    base = float(np.mean(y))
    return float(np.mean((base - y) ** 2))


def reliability_table(y_true: Sequence[float], probs: Sequence[float],
                      bins: int = 10) -> List[Dict[str, Any]]:
    """Equal-width probability bins with observed and predicted frequencies."""
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(probs, dtype=float)
    out: List[Dict[str, Any]] = []
    edges = np.linspace(0.0, 1.0, bins + 1)
    for i in range(bins):
        lo, hi = float(edges[i]), float(edges[i + 1])
        if i == bins - 1:
            mask = (p >= lo) & (p <= hi)
        else:
            mask = (p >= lo) & (p < hi)
        n = int(mask.sum())
        if n == 0:
            continue
        out.append({
            "bin_lo": lo, "bin_hi": hi, "n": n,
            "mean_predicted": float(p[mask].mean()),
            "observed_rate": float(y[mask].mean()),
        })
    return out


def expected_calibration_error(y_true: Sequence[float],
                               probs: Sequence[float],
                               bins: int = 10) -> float:
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(probs, dtype=float)
    if len(y) == 0:
        return 0.0
    ece = 0.0
    for row in reliability_table(y, p, bins=bins):
        ece += row["n"] / len(y) * abs(row["observed_rate"]
                                       - row["mean_predicted"])
    return float(ece)


def leave_one_family_out(X: Sequence[Sequence[float]],
                         y: Sequence[float],
                         families: Sequence[str],
                         **model_kwargs: Any
                         ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """Out-of-fold predictions with each family held out in turn.

    Returns the prediction vector (same order as the inputs) and a per-fold
    record. A fold whose training set contains only one class reports
    ``single_class=True`` and predicts the training base rate.
    """
    Xa = np.asarray(X, dtype=float)
    ya = np.asarray(y, dtype=float)
    fam = np.asarray(families)
    preds = np.zeros(len(ya), dtype=float)
    folds: List[Dict[str, Any]] = []
    for f in sorted(set(fam.tolist())):
        test = fam == f
        train = ~test
        model = LogisticRegression(**model_kwargs).fit(Xa[train], ya[train])
        preds[test] = model.predict_proba(Xa[test])
        y_train = ya[train]
        folds.append({
            "family": f,
            "n_test": int(test.sum()),
            "n_train": int(train.sum()),
            "train_base_rate": float(y_train.mean()) if len(y_train) else 0.0,
            "single_class": bool(len(set(y_train.tolist())) < 2),
            "test_observed_rate": float(ya[test].mean()),
            "test_mean_predicted": float(preds[test].mean()),
        })
    return preds, folds


def quartile_rows(y_true: Sequence[float], probs: Sequence[float],
                  extra: Optional[Sequence[float]] = None,
                  name: str = "extra") -> List[Dict[str, Any]]:
    """Aggregate by quartile of the predicted probability.

    ``extra`` is an optional per-sample quantity (here: the unsupported-claim
    rate) averaged within each predicted-probability quartile, which shows
    whether the probability is *actionable* rather than merely calibrated.
    """
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(probs, dtype=float)
    if len(p) == 0:
        return []
    edges = np.quantile(p, [0.0, 0.25, 0.5, 0.75, 1.0])
    rows: List[Dict[str, Any]] = []
    for i in range(4):
        lo, hi = float(edges[i]), float(edges[i + 1])
        mask = (p >= lo) & (p <= hi) if i == 3 else (p >= lo) & (p < hi)
        n = int(mask.sum())
        if n == 0:
            continue
        row = {"quartile": i + 1, "n": n,
               "mean_predicted": float(p[mask].mean()),
               "observed_rate": float(y[mask].mean())}
        if extra is not None:
            row[name] = float(np.mean(np.asarray(extra, dtype=float)[mask]))
        rows.append(row)
    return rows


def coefficient_table(features: Iterable[str],
                      model: LogisticRegression) -> List[Dict[str, Any]]:
    """Per-feature weights on the standardised scale (full-data fit)."""
    if model.w_ is None:
        return []
    return [{"feature": name, "weight": float(model.w_[i + 1])}
            for i, name in enumerate(features)]
