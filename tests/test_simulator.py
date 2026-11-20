import datetime

from oblivionx.common import FAMILIES
from oblivionx.corpus.generate import _expected_failure
from oblivionx.simulate.simulator import ANALYSIS_DATE, simulate_sample


def _gt(family, handled=True):
    spec = FAMILIES[family]
    return {
        "stages": spec.stages,
        "behaviors": spec.behaviors,
        "interaction": spec.interaction,
        "env_dep": spec.env_dep,
        "date_trigger": spec.date_trigger,
        "expected_failure": _expected_failure(spec, handled=handled),
    }


def test_simulator_is_deterministic():
    gt = _gt("donoff_downloader")
    first = simulate_sample("sample-1", gt, "donoff_downloader", "plain",
                            "docm")
    second = simulate_sample("sample-1", gt, "donoff_downloader", "plain",
                             "docm")
    assert first.to_dict() == second.to_dict()


def test_default_analysis_date_is_fixed():
    assert ANALYSIS_DATE == datetime.date(2024, 1, 1)


def test_successful_run_follows_ground_truth_chain():
    gt = _gt("donoff_downloader")
    sample = simulate_sample("s", gt, "donoff_downloader", "plain", "docm")
    assert sample.meta["failure"] is None
    behaviors = {event.behavior for event in sample.events}
    assert {"macro_entry", "powershell_run", "shell_run", "http_download",
            "file_execute"} <= behaviors
    assert sample.events[0].confidence < 0.5  # startup noise, not a claim


def test_interaction_gate_failure():
    gt = _gt("donoff_interaction", handled=False)
    sample = simulate_sample("s", gt, "donoff_interaction", "plain", "docm",
                             interaction_handled=False)
    assert sample.meta["failure"] == "dynamic_interaction"
    assert "msgbox_gate" in {event.behavior for event in sample.events}


def test_interaction_handled_continues():
    gt = _gt("donoff_interaction", handled=True)
    sample = simulate_sample("s", gt, "donoff_interaction", "plain", "docm",
                             interaction_handled=True)
    assert sample.meta["failure"] is None
    assert "http_download" in {event.behavior for event in sample.events}


def test_missing_environment_dependency():
    gt = _gt("metacol_mailer")
    sample = simulate_sample("s", gt, "metacol_mailer", "plain", "docm",
                             env_available={"outlook": False})
    assert sample.meta["failure"] == "dynamic_env"
    assert sample.meta["missing_dependency"] == "outlook"
    assert "outlook_access" in {event.behavior for event in sample.events}


def test_date_gate_blocks_by_default():
    gt = _gt("thus_wiper")
    sample = simulate_sample("s", gt, "thus_wiper", "plain", "docm")
    assert sample.meta["failure"] == "dynamic_date"
    assert "file_delete" not in {event.behavior for event in sample.events}


def test_date_gate_fires_on_injected_date():
    gt = _gt("thus_wiper")
    sample = simulate_sample("s", gt, "thus_wiper", "plain", "docm",
                             date_now=datetime.date(2024, 12, 13))
    assert sample.meta["failure"] is None
    assert "file_delete" in {event.behavior for event in sample.events}


def test_semantic_failure():
    gt = _gt("broken_semantic")
    sample = simulate_sample("s", gt, "broken_semantic", "plain", "docm")
    assert sample.meta["failure"] == "dynamic_semantic"
    claimed = [event.behavior for event in sample.events
               if event.confidence >= 0.5]
    assert claimed == ["macro_entry"]


def test_empty_project():
    gt = _gt("empty_macro")
    sample = simulate_sample("s", gt, "empty_macro", "plain", "docm")
    assert sample.meta["failure"] == "static_empty"
    assert [event for event in sample.events if event.confidence >= 0.5] == []


def test_deliberate_timeout():
    gt = _gt("slow_timeout")
    sample = simulate_sample("s", gt, "slow_timeout", "plain", "docm")
    assert sample.meta["failure"] == "dynamic_timeout"
    assert sample.meta["duration_ms"] == 120000


def test_short_timeout_budget():
    gt = _gt("donoff_downloader")
    sample = simulate_sample("s", gt, "donoff_downloader", "plain", "docm",
                             timeout_ms=10)
    assert sample.meta["failure"] == "dynamic_timeout"
    # Nothing macro-related is observed, but OS-level startup noise may
    # precede the macro and is recorded (never above the claim threshold).
    assert all(event.source == "os" for event in sample.events)
    assert [event for event in sample.events if event.confidence >= 0.5] == []


def test_startup_noise_is_os_level_and_never_a_claim():
    gt = _gt("donoff_downloader")
    sample = simulate_sample("s", gt, "donoff_downloader", "plain", "docm")
    noise = [e for e in sample.events if e.obj == "startup-noise"]
    assert noise, "the simulator always injects some startup noise"
    assert all(e.source == "os" for e in noise)
    assert all(e.confidence < 0.5 for e in noise)


def test_missing_dependency_attempt_happens_at_the_exfiltration_stage():
    gt = _gt("metacol_mailer")
    sample = simulate_sample("s", gt, "metacol_mailer", "plain", "docm",
                             env_available={"outlook": False})
    claimed = [e for e in sample.events if e.confidence >= 0.5]
    # entry point comes first, the failed Outlook attempt after it
    assert claimed[0].behavior == "macro_entry"
    assert claimed[-1].behavior == "outlook_access"
    assert sample.events.index(claimed[0]) < sample.events.index(claimed[-1])


def test_obfuscation_behaviors_are_replayed_after_the_entry_point():
    gt = _gt("laroux_replicator")
    gt["behaviors"] = gt["behaviors"] + ["string_concat", "chr_encode"]
    sample = simulate_sample("s", gt, "laroux_replicator", "combo", "docm")
    claimed = [e for e in sample.events if e.confidence >= 0.5]
    assert claimed[0].behavior == "macro_entry"
    assert {"string_concat", "chr_encode"} <= {e.behavior for e in claimed}
