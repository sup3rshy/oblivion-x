"""Chain ordering: ontology order vs evidence (timestamp) order (E9)."""
import pytest

from oblivionx.reconstruction.reconstruct import reconstruct
from oblivionx.telemetry.schema import Event, SampleAnalysis


def _sample(*events, failure=None):
    sample = SampleAnalysis(sample_id="s1", family="donoff_downloader",
                            variant="plain")
    for i, (source, behavior, t_ms) in enumerate(events, start=1):
        sample.add(Event(id=i, t_ms=t_ms, source=source,
                         behavior=behavior, confidence=0.9))
    sample.meta = {"failure": failure}
    return sample


def test_timestamp_order_follows_observation_time():
    # Events arrive in *id* order delivery, impact, execution, but the
    # observed times put impact first: the chain must follow evidence.
    sample = _sample(("dynamic", "macro_entry", 500),
                     ("dynamic", "file_write", 100),
                     ("dynamic", "shell_run", 200))
    rec = reconstruct(sample, stage_order="timestamp")
    assert [s.stage for s in rec.stages] == ["impact", "execution", "delivery"]
    assert rec.chain == "impact -> execution -> delivery"


def test_ontology_order_is_the_default_and_ignores_time():
    sample = _sample(("dynamic", "macro_entry", 500),
                     ("dynamic", "file_write", 100),
                     ("dynamic", "shell_run", 200))
    rec = reconstruct(sample)
    assert [s.stage for s in rec.stages] == [
        "delivery", "execution", "impact"]
    assert rec.chain == "delivery -> execution -> impact"


def test_stage_claims_carry_first_seen_timestamp():
    sample = _sample(("dynamic", "macro_entry", 500),
                     ("dynamic", "http_download", 900),
                     ("dynamic", "http_download", 700))
    rec = reconstruct(sample, stage_order="timestamp")
    by_stage = {s.stage: s for s in rec.stages}
    assert by_stage["delivery"].first_seen_ms == 500
    assert by_stage["c2_download"].first_seen_ms == 700  # earliest event


def test_static_only_stage_has_no_timestamp_and_is_appended():
    sample = _sample(("dynamic", "macro_entry", 500),
                     ("static", "outlook_send", None))
    rec = reconstruct(sample, stage_order="timestamp")
    by_stage = {s.stage: s for s in rec.stages}
    assert by_stage["exfiltration"].first_seen_ms is None
    # observed stage first, untimed (static-only) stage after it
    assert [s.stage for s in rec.stages] == ["delivery", "exfiltration"]


def test_unknown_stage_order_is_rejected():
    sample = _sample(("dynamic", "macro_entry", 500))
    with pytest.raises(ValueError):
        reconstruct(sample, stage_order="evidence")


def test_reconstruction_roundtrip_keeps_first_seen_ms():
    sample = _sample(("dynamic", "macro_entry", 500))
    rec = reconstruct(sample, stage_order="timestamp")
    restored = type(rec).from_dict(rec.to_dict())
    assert restored.stages[0].first_seen_ms == 500
    assert restored.stages[0].stage == "delivery"


def test_legacy_payload_without_first_seen_ms_still_loads():
    legacy = {
        "sample_id": "old",
        "stages": [{"stage": "delivery", "evidence": [1],
                    "confidence": 0.9, "note": ""}],
        "behaviors": [], "chain": "delivery", "status": "ok",
    }
    restored = type(reconstruct(_sample(("dynamic", "macro_entry", 1)))
                    ).from_dict(legacy)
    assert restored.stages[0].first_seen_ms is None
