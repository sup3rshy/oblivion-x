from collections import Counter

import pytest

from oblivionx.common import read_json
from oblivionx.eval.experiments import _top, experiment_E2


def test_all_experiment_files_are_written(tiny_eval):
    for name in ("E1_reproduce_oblivion", "E2_static_vs_dynamic",
                 "E3_obfuscation", "E4_temporal_segmentation",
                 "E5_ground_truth", "E6_reconstruction", "E7_failures",
                 "E8_performance"):
        assert (tiny_eval / f"{name}.json").exists(), name


def test_top_ties_are_broken_alphabetically():
    counter = Counter({"z": 1, "a": 1, "m": 1})
    assert [key for key, _ in _top(counter, 2)] == ["a", "m"]


def test_e1_taxonomy_covers_every_sample(tiny_eval):
    report = read_json(tiny_eval / "E1_reproduce_oblivion.json")
    assert report["n_samples"] == 16
    assert report["n_files"] == 16
    assert report["counts"]["no_file"] == 0
    assert report["counts"]["empty"] == 2
    assert report["counts"]["interaction"] == 2
    assert report["counts"]["bas_cls"] == 12


def test_e2_reports_both_observability_views(tiny_eval):
    report = read_json(tiny_eval / "E2_static_vs_dynamic.json")
    assert 0 <= report["mean_static_recall"] <= 1
    assert 0 <= report["mean_dynamic_recall"] <= 1
    assert 0 <= report["mean_view_jaccard"] <= 1
    assert report["per_sample"]
    assert all(len(item) == 2 for item in report["static_only"])
    assert all(len(item) == 2 for item in report["most_static_missed"])


def test_e2_is_stable_when_reexecuted(tiny_corpus, tiny_analysis, tmp_path):
    first = experiment_E2(tiny_corpus, tiny_analysis, tmp_path / "a")
    second = experiment_E2(tiny_corpus, tiny_analysis, tmp_path / "b")
    assert first["static_only"] == second["static_only"]
    assert first["dynamic_only"] == second["dynamic_only"]
    assert first["most_static_missed"] == second["most_static_missed"]


def test_e4_sweep_reports_best_scale(tiny_eval):
    report = read_json(tiny_eval / "E4_temporal_segmentation.json")
    assert report["best_n_by_boundary_f1"] in {str(n) for n in (1, 5, 10, 20)}
    assert set(report["by_n"]) == {"1", "5", "10", "20"}
    assert report["per_sample"]


def test_e5_ground_truth_checks_pass(tiny_eval):
    report = read_json(tiny_eval / "E5_ground_truth.json")
    assert report["n_samples"] == 16
    assert report["checks"]["entry_point"] == 1.0
    assert report["checks"]["behavior_hints"] == 1.0
    assert report["checks"]["stage_order"] == 1.0
    assert report["checks"]["obfuscation_label"] == 1.0


def test_e6_reconstruction_aggregate(tiny_eval):
    report = read_json(tiny_eval / "E6_reconstruction.json")
    assert report["aggregate"]["n"] == 16
    assert 0 <= report["aggregate"]["behavior_recall"] <= 1
    assert 0 <= report["aggregate"]["stage_accuracy"] <= 1
    assert report["aggregate"]["analysis_time_ms_mean"] > 0


def test_e7_failure_expectations_match(tiny_eval):
    report = read_json(tiny_eval / "E7_failures.json")
    assert report["n_expectation_mismatch"] == 0
    assert report["n_baseline_mismatch"] == 0
    assert report["n_stored_mismatch"] == 0
    assert report["recovered_by_interaction_handling"] == \
        report["interaction_gated_total"] == 2


def test_e8_performance(tiny_eval):
    report = read_json(tiny_eval / "E8_performance.json")
    assert report["n"] == 16
    assert report["total_time_ms_mean"] > 0
    assert report["completion_rate"] + report["timeout_rate"] == \
        pytest.approx(1.0)
