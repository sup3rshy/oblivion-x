import pytest

from oblivionx.telemetry.normalize import (
    _map_action,
    normalize,
    parse_oblivion_report,
    parse_vba_trace,
)

TRACE = """Shell\tcmd /c calc\t0.5
powershell\tsomething\t1.25
http_open\thttp://127.0.0.1/x\t2
nonsense\tx\t3
regwrite\tHKCU\\\\Run\t4
"""

OBLIVION = """### Shell Actions ###
powershell.exe -EncodedCommand AAAA
### Executable Files ###
Nothing Found
### Domain Traces ###
example.com
### System File Writes ###
C:\\temp\\marker.txt
### External Calls ###
cmd.exe
### Auto Exec Methods ###
Document_Open
### Environment Variables ###
%TEMP%
### Deobfuscated Powershell ###
Write-Host hello
"""


def test_parse_vba_trace_maps_actions_and_timestamps():
    sample = parse_vba_trace(TRACE, "s1", family="f", variant="plain")
    assert sample.sample_id == "s1"
    assert sample.family == "f"
    assert sample.variant == "plain"
    assert [(event.behavior, event.t_ms) for event in sample.events] == [
        ("shell_run", 500),
        ("powershell_run", 1250),
        ("http_download", 2000),
        ("registry_write", 4000),
    ]
    assert all(event.source == "dynamic" for event in sample.events)
    assert all(event.confidence == pytest.approx(0.99)
               for event in sample.events)


def test_parse_vba_trace_handles_missing_and_invalid_time():
    sample = parse_vba_trace("Shell\tcmd\nShell\tcmd\tnot-a-number\n", "s")
    assert len(sample.events) == 2
    assert [event.t_ms for event in sample.events] == [None, None]


def test_map_action_handles_prefixes_and_unknown():
    assert _map_action("powershell.exe", "") == "powershell_run"
    assert _map_action("shell", "") == "shell_run"
    assert _map_action("unknown", "") is None


def test_parse_oblivion_report_sections():
    sample = parse_oblivion_report(OBLIVION, "s1")
    behaviors = [event.behavior for event in sample.events]
    assert behaviors == ["powershell_run", "url_reference", "file_write",
                         "shell_run", "macro_entry", "env_read",
                         "powershell_run"]
    assert all(event.t_ms is None for event in sample.events)
    assert all(event.evidence == "oblivion-report" for event in sample.events)


def test_parse_oblivion_report_ignores_nothing_found():
    sample = parse_oblivion_report("### Shell Actions ###\nNothing Found\n",
                                   "s1")
    assert sample.events == []


def test_normalize_dispatch_and_meta(tmp_path):
    path = tmp_path / "trace.log"
    path.write_text(TRACE, encoding="utf-8")
    sample = normalize(path, "vba_trace", "s1", meta={"x": 1})
    assert sample.meta["x"] == 1
    assert sample.events
    with pytest.raises(ValueError, match="unknown source"):
        normalize(path, "nope", "s1")
