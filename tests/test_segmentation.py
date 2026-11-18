import numpy as np

from oblivionx.telemetry.schema import Event, SampleAnalysis
from oblivionx.telemetry.segmentation import (
    BONAPT_CONFIGS,
    build_bonapt_features,
    explainability_profile,
    flatten,
    segment_events,
    segment_frequencies,
)


def _events(n=10, behaviors=("a", "b")):
    return [Event(id=i + 1, t_ms=i * 10, source="dynamic",
                  behavior=behaviors[i % len(behaviors)])
            for i in range(n)]


def test_segment_events_equal_time_buckets():
    events = _events(10)
    buckets = segment_events(events, 5)
    assert len(buckets) == 5
    assert [len(bucket) for bucket in buckets] == [2, 2, 2, 2, 2]
    assert [event.t_ms for event in buckets[0]] == [0, 10]
    assert [event.t_ms for event in buckets[-1]] == [80, 90]


def test_segment_events_clamps_last_instant():
    events = [Event(id=1, t_ms=0, source="dynamic", behavior="a"),
              Event(id=2, t_ms=100, source="dynamic", behavior="a")]
    buckets = segment_events(events, 2)
    assert [event.id for event in buckets[-1]] == [2]


def test_segment_events_without_timestamps_returns_empty_buckets():
    events = [Event(id=1, t_ms=None, source="static", behavior="a")]
    assert segment_events(events, 3) == [[], [], []]


def test_segment_frequencies_sum_to_one_per_feature():
    events = _events(10, ("a", "b", "a"))
    freqs, features = segment_frequencies(events, 5)
    assert features == ["a", "b"]
    for feature in features:
        assert freqs[feature].shape == (5,)
        assert np.isclose(freqs[feature].sum(), 1.0)


def test_segment_frequencies_unknown_feature_is_zero():
    freqs, _ = segment_frequencies(_events(), 5, features=["missing"])
    assert np.allclose(freqs["missing"], 0)


def test_flatten_shape_and_order():
    freqs = {"a": np.array([0.5, 0.5]), "b": np.array([1.0, 0.0])}
    vector = flatten(freqs, ["a", "b"], 2)
    assert vector.shape == (4,)
    assert np.allclose(vector, [0.5, 0.5, 1.0, 0.0])


def test_build_bonapt_features_cover_documented_configs():
    sample = SampleAnalysis(sample_id="s")
    sample.events = _events(20)
    features = build_bonapt_features(sample)
    expected = {str(n) for n in BONAPT_CONFIGS} | {"1+5", "1+10", "1+20"}
    assert expected <= set(features)
    # One feature per behavior in this stream, so the "5" vector is 5*2.
    assert features["5"].shape == (5 * 2,)
    assert features["1+5"].shape == (1 * 2 + 5 * 2,)


def test_explainability_profile_discretizes_to_three_levels():
    events = [Event(id=i + 1, t_ms=i * 10, source="dynamic",
                    behavior=("shell_run", "http_download")[i % 2])
              for i in range(30)]
    profile = explainability_profile(events, 5)
    assert profile
    for values in profile.values():
        assert len(values) == 5
        assert set(values) <= {"low", "medium", "high"}
