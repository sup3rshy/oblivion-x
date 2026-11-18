from oblivionx.common import (
    BEHAVIOR_DEFS,
    BONAPT_CATEGORIES,
    FAMILIES,
    OBFUSCATION_TECHNIQUES,
    STAGE_ORDER,
    read_json,
    stage_index,
    write_json,
)


def test_behavior_catalog_is_internally_consistent():
    assert len(BEHAVIOR_DEFS) >= 25
    for behavior_id, definition in BEHAVIOR_DEFS.items():
        assert definition.id == behavior_id
        if definition.stage is not None:
            assert definition.stage in STAGE_ORDER
        assert definition.bonapt_category in BONAPT_CATEGORIES
        assert isinstance(definition.vba_hints, list)
        assert isinstance(definition.ps_hints, list)


def test_stage_order_is_unique_and_ordered():
    assert STAGE_ORDER[0] == "delivery"
    assert STAGE_ORDER[-1] == "cleanup"
    assert len(STAGE_ORDER) == len(set(STAGE_ORDER))
    assert stage_index("delivery") == 0
    assert stage_index("does-not-exist") == -1


def test_families_reference_known_stages_and_behaviors():
    assert len(FAMILIES) == 14
    for name, spec in FAMILIES.items():
        assert spec.family == name
        assert spec.formats
        assert set(spec.formats) <= {"docm", "xlsm"}
        for behavior in spec.behaviors:
            assert behavior in BEHAVIOR_DEFS
        for stage in spec.stages:
            assert stage in STAGE_ORDER
        assert spec.stages == sorted(spec.stages, key=STAGE_ORDER.index)
        if spec.interaction:
            assert "msgbox_gate" in spec.behaviors


def test_obfuscation_taxonomy():
    assert OBFUSCATION_TECHNIQUES == [
        "plain", "random", "split", "encode", "logic", "combo"]


def test_json_helpers_roundtrip(tmp_path):
    payload = {"a": [1, 2, 3], "b": "xin chào", "c": None}
    path = tmp_path / "nested" / "data.json"
    write_json(payload, path)
    assert path.exists()
    assert read_json(path) == payload
