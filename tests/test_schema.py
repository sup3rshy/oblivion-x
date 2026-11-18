from oblivionx.telemetry.schema import (
    BehaviorClaim,
    Event,
    Reconstruction,
    SampleAnalysis,
    StageClaim,
)


def test_event_roundtrip():
    event = Event(id=3, t_ms=120, source="dynamic", behavior="shell_run",
                  obj="cmd /c whoami", args={"pid": 4}, confidence=0.9,
                  evidence="trace:shell")
    restored = Event.from_dict(event.to_dict())
    assert restored == event


def test_event_from_dict_uses_defaults():
    event = Event.from_dict({"id": 1, "t_ms": None, "source": "static",
                             "behavior": "macro_entry"})
    assert event.obj == ""
    assert event.args == {}
    assert event.confidence == 1.0


def test_sample_analysis_assigns_monotonic_ids():
    sample = SampleAnalysis(sample_id="s1")
    sample.add(Event(id=0, t_ms=1, source="dynamic", behavior="macro_entry"))
    sample.add(Event(id=0, t_ms=2, source="dynamic", behavior="shell_run"))
    assert [event.id for event in sample.events] == [1, 2]
    assert sample.behaviors() == ["macro_entry", "shell_run"]
    assert sample.behaviors("static") == []
    assert sample.dynamic_events() == sample.events


def test_sample_analysis_provided_id_is_kept():
    sample = SampleAnalysis(sample_id="s1")
    sample.add(Event(id=42, t_ms=1, source="static", behavior="macro_entry"))
    assert sample.events[0].id == 42


def test_sample_analysis_roundtrip():
    sample = SampleAnalysis(sample_id="s1", format="docm", family="f",
                            variant="plain")
    sample.add(Event(id=0, t_ms=10, source="dynamic", behavior="shell_run"))
    sample.meta["failure"] = None
    restored = SampleAnalysis.from_dict(sample.to_dict())
    assert restored.sample_id == sample.sample_id
    assert restored.format == sample.format
    assert restored.family == sample.family
    assert restored.variant == sample.variant
    assert restored.events == sample.events
    assert restored.meta == sample.meta


def test_reconstruction_roundtrip():
    record = Reconstruction(
        sample_id="s1",
        stages=[StageClaim(stage="execution", evidence=[1], confidence=0.9)],
        behaviors=[BehaviorClaim(behavior="shell_run", evidence=[1],
                                 confidence=0.9, supported=True,
                                 obj="cmd")],
        chain="execution",
        status="partial",
    )
    restored = Reconstruction.from_dict(record.to_dict())
    assert restored.sample_id == record.sample_id
    assert restored.chain == record.chain
    assert restored.status == record.status
    assert restored.stages == record.stages
    assert restored.behaviors == record.behaviors
