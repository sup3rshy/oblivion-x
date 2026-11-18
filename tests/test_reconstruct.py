from oblivionx.reconstruction.reconstruct import reconstruct
from oblivionx.telemetry.schema import Event, SampleAnalysis


def _sample(*events, failure=None):
    sample = SampleAnalysis(sample_id="s1", family="donoff_downloader",
                            variant="plain")
    for i, (source, behavior, confidence) in enumerate(events, start=1):
        sample.add(Event(id=i, t_ms=i * 10 if source == "dynamic" else None,
                         source=source, behavior=behavior,
                         confidence=confidence))
    sample.meta = {"failure": failure}
    return sample


def test_reconstruct_orders_stages_and_builds_chain():
    sample = _sample(("dynamic", "file_write", 0.9),
                     ("dynamic", "macro_entry", 0.9),
                     ("dynamic", "http_download", 0.9),
                     ("dynamic", "shell_run", 0.9))
    rec = reconstruct(sample)
    assert [stage.stage for stage in rec.stages] == [
        "delivery", "execution", "c2_download", "impact"]
    assert rec.chain == "delivery -> execution -> c2_download -> impact"
    assert rec.status == "ok"


def test_low_confidence_events_are_not_claims():
    sample = _sample(("dynamic", "shell_run", 0.3))
    rec = reconstruct(sample)
    assert rec.behaviors == []
    assert rec.stages == []
    assert rec.status == "failed"


def test_static_claim_is_unsupported_dynamic_claim_is_supported():
    sample = _sample(("static", "outlook_send", 0.9),
                     ("dynamic", "shell_run", 0.9))
    rec = reconstruct(sample)
    by_behavior = {claim.behavior: claim for claim in rec.behaviors}
    assert by_behavior["outlook_send"].supported is False
    assert by_behavior["shell_run"].supported is True


def test_duplicate_events_are_merged_with_all_evidence_ids():
    sample = _sample(("dynamic", "file_write", 0.9),
                     ("static", "file_write", 0.85),
                     ("dynamic", "file_write", 0.95))
    rec = reconstruct(sample)
    assert len(rec.behaviors) == 1
    claim = rec.behaviors[0]
    assert claim.behavior == "file_write"
    assert claim.evidence == [1, 3]
    assert claim.confidence == 0.95


def test_unknown_behavior_is_reported_not_fatal():
    sample = _sample(("dynamic", "future_behavior", 0.9))
    rec = reconstruct(sample)
    assert [claim.behavior for claim in rec.behaviors] == ["future_behavior"]
    assert rec.behaviors[0].supported is False
    assert rec.stages == []


def test_failure_marks_reconstruction_partial():
    sample = _sample(("dynamic", "macro_entry", 0.9),
                     failure="dynamic_env")
    rec = reconstruct(sample)
    assert rec.status == "partial"
    assert rec.chain == "delivery"
