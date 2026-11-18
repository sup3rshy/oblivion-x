from pathlib import Path

from oblivionx.corpus.builders import package_office_file
from oblivionx.corpus.msovba import build_vba_project_bin
from oblivionx.corpus.obfuscators import obfuscate
from oblivionx.eval.experiments import _has_executable_code
from oblivionx.static.analyzer import analyze_static
from oblivionx.static.extractor import all_sources, extract_modules, file_sha256, has_macros

SOURCE = '''Attribute VB_Name = "ThisDocument"
Private Sub Document_Open()
    Dim sh As Object
    Set sh = CreateObject("WScript.Shell")
    sh.Run "powershell.exe -NoProfile -WindowStyle Hidden -Command calc", 0
    MsgBox "Enable content?"
    Open "C:\\temp\\marker.txt" For Output As #1
    Print #1, "marker"
    Close #1
End Sub
'''


def _build(tmp_path: Path, source: str = SOURCE) -> Path:
    path = tmp_path / "sample.docm"
    package_office_file([("ThisDocument", "document", source),
                         ("NewMacros", "procedural",
                          'Attribute VB_Name = "NewMacros"\n')],
                        "docm", path)
    return path


def test_extract_modules_reads_document_and_procedural_modules(tmp_path):
    path = _build(tmp_path)
    modules = extract_modules(path)
    assert {module["name"] for module in modules} == {"ThisDocument",
                                                      "NewMacros"}
    assert {module["kind"] for module in modules} == {"document",
                                                      "procedural"}
    assert "Document_Open" in all_sources(modules)
    assert has_macros(path) is True


def test_extract_modules_handles_files_without_macros(tmp_path):
    plain = tmp_path / "plain.docm"
    plain.write_bytes(b"not an office file")
    assert extract_modules(plain) == []
    assert has_macros(plain) is False

    import zipfile
    empty_zip = tmp_path / "empty.docm"
    with zipfile.ZipFile(empty_zip, "w") as archive:
        archive.writestr("word/document.xml", "<doc/>")
    assert extract_modules(empty_zip) == []


def test_extract_modules_reads_legacy_ole_file(tmp_path):
    data = build_vba_project_bin(
        [("ThisDocument", "document", SOURCE),
         ("NewMacros", "procedural",
          'Attribute VB_Name = "NewMacros"\n')],
        host="word")
    path = tmp_path / "legacy.doc"
    path.write_bytes(data)
    assert has_macros(path) is True
    assert "Document_Open" in all_sources(extract_modules(path))


def test_file_sha256(tmp_path):
    path = tmp_path / "x.bin"
    path.write_bytes(b"abc")
    assert file_sha256(path) == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


def test_analyze_static_maps_indicators(tmp_path):
    path = _build(tmp_path)
    sample = analyze_static(path, "s1", "donoff_downloader", "plain", "docm")
    behaviors = {event.behavior for event in sample.events}
    assert {"macro_entry", "shell_run", "powershell_run", "window_hide",
            "msgbox_gate", "file_write"} <= behaviors
    assert sample.meta["n_modules"] == 2
    assert sample.meta["status"] == "ok"
    assert all(event.source == "static" for event in sample.events)
    assert all(event.t_ms is None for event in sample.events)


def test_analyze_static_detects_and_recovers_split_obfuscation(tmp_path):
    source = obfuscate(SOURCE, "split", 0)
    path = _build(tmp_path, source)
    sample = analyze_static(path, "s1", "donoff_downloader", "split", "docm")
    assert sample.meta["obfuscation_detected"]["split"] is True
    assert sample.meta["recovered_payloads"]
    assert sample.meta["deobfuscation_applied"] is True


def test_analyze_static_detects_encode_obfuscation(tmp_path):
    source = obfuscate(SOURCE, "encode", 0)
    path = _build(tmp_path, source)
    sample = analyze_static(path, "s1", "donoff_downloader", "encode", "docm")
    flags = sample.meta["obfuscation_detected"]
    assert flags["encode"] is True
    behaviors = {event.behavior for event in sample.events}
    assert "chr_encode" in behaviors


def test_has_executable_code_ignores_metadata_and_empty_scaffolding():
    assert _has_executable_code(
        'Attribute VB_Name = "ThisDocument"\nPrivate Sub Document_Open()\n'
        'End Sub\n') is False
    assert _has_executable_code(
        'Private Sub Document_Open()\n    MsgBox "x"\nEnd Sub\n') is True
    assert _has_executable_code(
        'Attribute VB_Name = "X"\n\' only a comment\nRem another\n'
    ) is False
