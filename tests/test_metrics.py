import pytest

from oblivionx.eval.metrics import _stage_label_scores, aggregate, evaluate_sample, lcs_length
from oblivionx.telemetry.schema import (
    BehaviorClaim,
    Event,
    Reconstruction,
    SampleAnalysis,
    StageClaim,
)


def _analysis(behaviors=(), stages=(), failure=None, variant="plain",
              family="donoff_downloader", recovered=None,
              analysis_time_ms=12.5):
    sample = SampleAnalysis(sample_id="s1", family=family, variant=variant)
    for i, behavior in enumerate(behaviors, start=1):
        sample.add(Event(id=i, t_ms=i * 10, source="dynamic",
                         behavior=behavior, confidence=0.9))
    sample.meta = {"failure": failure,
                   "analysis_time_ms": analysis_time_ms}
    if recovered is not None:
        sample.meta["recovered_payloads"] = recovered
    rec = Reconstruction(sample_id="s1")
    for behavior in behaviors:
        rec.behaviors.append(BehaviorClaim(
            behavior=behavior, evidence=[1], confidence=0.9, supported=True))
    for stage in stages:
        rec.stages.append(StageClaim(stage=stage, evidence=[1],
                                     confidence=0.9))
    return sample, rec


def test_lcs_length():
    assert lcs_length([], []) == 0
    assert lcs_length(["a"], []) == 0
    assert lcs_length(["a", "b", "c"], ["a", "b", "c"]) == 3
    assert lcs_length(["a", "b", "c"], ["a", "c"]) == 2
    assert lcs_length(["a", "b"], ["b", "a"]) == 1


def test_stage_scores_exact_chain():
    _, rec = _analysis(stages=("delivery", "execution", "impact"))
    accuracy, precision, recall = _stage_label_scores(
        ["delivery", "execution", "impact"], rec)
    assert (accuracy, precision, recall) == (1.0, 1.0, 1.0)


def test_stage_scores_missing_middle_stage():
    _, rec = _analysis(stages=("delivery", "impact"))
    accuracy, precision, recall = _stage_label_scores(
        ["delivery", "execution", "impact"], rec)
    assert precision == 1.0
    assert recall == pytest.approx(2 / 3)
    assert accuracy == pytest.approx(0.8)


def test_stage_scores_extra_stage():
    _, rec = _analysis(stages=("delivery", "execution"))
    accuracy, precision, recall = _stage_label_scores(["delivery"], rec)
    assert precision == 0.5
    assert recall == 1.0
    assert accuracy == pytest.approx(2 / 3)


def test_stage_scores_empty_chains():
    _, rec = _analysis()
    assert _stage_label_scores([], rec) == (1.0, 1.0, 1.0)
    rec.stages = [StageClaim(stage="delivery")]
    assert _stage_label_scores([], rec) == (0.0, 0.0, 0.0)


def test_evaluate_sample_perfect_reconstruction():
    sample, rec = _analysis(behaviors=("shell_run",),
                            stages=("execution",))
    metrics = evaluate_sample(sample, rec, {
        "behaviors": ["shell_run"], "stages": ["execution"]})
    assert metrics.behavior_recall == 1.0
    assert metrics.behavior_precision == 1.0
    assert metrics.evidence_precision == 1.0
    assert metrics.stage_accuracy == 1.0
    assert metrics.unsupported_rate == 0.0
    assert metrics.analysis_time_ms == 12.5
    assert metrics.completed is True


def test_evaluate_sample_counts_unsupported_and_missing_evidence():
    sample, rec = _analysis(behaviors=("shell_run", "outlook_send"),
                            stages=("execution",))
    rec.behaviors[1].evidence = []
    rec.behaviors[1].supported = False
    metrics = evaluate_sample(sample, rec, {
        "behaviors": ["shell_run"], "stages": ["execution"]})
    assert metrics.behavior_recall == 1.0
    assert metrics.behavior_precision == 0.5
    assert metrics.evidence_precision == 0.5
    assert metrics.unsupported_rate == 0.5


def test_empty_ground_truth_is_vacuously_recalled():
    sample, rec = _analysis()
    metrics = evaluate_sample(sample, rec, {"behaviors": [], "stages": []})
    assert metrics.behavior_recall == 1.0
    assert metrics.behavior_precision == 1.0
    assert metrics.stage_accuracy == 1.0


def test_deobfuscation_is_not_applicable_to_empty_projects():
    sample, rec = _analysis(variant="split", family="empty_macro",
                            recovered=[])
    metrics = evaluate_sample(sample, rec, {"behaviors": [], "stages": []})
    assert metrics.deobfuscation_success is None


def test_deobfuscation_success_uses_recovered_payloads():
    sample, rec = _analysis(variant="split", recovered=["payload"])
    metrics = evaluate_sample(sample, rec, {"behaviors": [], "stages": []})
    assert metrics.deobfuscation_success is True


@pytest.mark.parametrize("failure,completed", [
    (None, True),
    ("dynamic_env", True),
    ("dynamic_date", True),
    ("dynamic_semantic", True),
    ("dynamic_timeout", False),
    ("dynamic_missing_trace", False),
    ("static_av_blocked", False),
])
def test_completion_semantics(failure, completed):
    sample, rec = _analysis(failure=failure)
    metrics = evaluate_sample(sample, rec, {"behaviors": [], "stages": []})
    assert metrics.completed is completed
    assert metrics.timed_out is (failure == "dynamic_timeout")


def test_aggregate():
    perfect, rec = _analysis(behaviors=("shell_run",),
                             stages=("execution",))
    m1 = evaluate_sample(perfect, rec, {"behaviors": ["shell_run"],
                                        "stages": ["execution"]})
    missing, rec2 = _analysis()
    m2 = evaluate_sample(missing, rec2, {"behaviors": ["shell_run"],
                                         "stages": ["execution"]})
    result = aggregate([m1, m2])
    assert result["n"] == 2
    assert result["behavior_recall"] == 0.5
    assert result["completion_rate"] == 1.0
    assert result["analysis_time_ms_mean"] == 12.5
    assert aggregate([]) == {}
