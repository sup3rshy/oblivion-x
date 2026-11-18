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
    assert sample.events == []


def test_obfuscation_behaviors_are_replayed():
    gt = _gt("donoff_downloader")
    gt["behaviors"] = gt["behaviors"] + ["string_concat", "chr_encode",
                                         "dead_code"]
    sample = simulate_sample("s", gt, "donoff_downloader", "combo", "docm")
    behaviors = {event.behavior for event in sample.events}
    assert {"string_concat", "chr_encode", "dead_code"} <= behaviors
