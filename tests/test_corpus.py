import hashlib
from pathlib import Path

import pytest

from oblivionx.common import FAMILIES, read_json
from oblivionx.corpus.builders import build_corpus_files, package_office_file
from oblivionx.corpus.generate import _expected_failure, generate_corpus
from oblivionx.corpus.obfuscators import obfuscate, obfuscate_sample
from oblivionx.corpus.vba_sources import build_sample_sources
from oblivionx.static.extractor import extract_modules


def _generate(path: Path, families=("donoff_downloader", "empty_macro",
                                    "thus_wiper"), seeds: int = 2):
    return generate_corpus(path, families=list(families), formats=["docm"],
                           techniques=["plain", "split"], seeds=seeds)


def test_generate_corpus_manifest_and_sources(tmp_path):
    corpus = tmp_path / "corpus"
    result = _generate(corpus)
    assert result["n_samples"] == 12
    manifest = read_json(corpus / "manifest.json")["samples"]
    ground_truth = read_json(corpus / "ground_truth.json")
    assert len(manifest) == 12
    assert set(ground_truth) == {entry["id"] for entry in manifest}
    for entry in manifest:
        assert (corpus / "sources" / entry["doc_source"]).exists()
        assert (corpus / "sources" / entry["helper_source"]).exists()
        gt = ground_truth[entry["id"]]
        assert gt["behaviors"] == sorted(set(gt["behaviors"]))
        if entry["family"] == "empty_macro":
            assert gt["behaviors"] == []
            assert gt["stages"] == []
        else:
            assert gt["stages"]


def test_generate_corpus_is_deterministic(tmp_path):
    first, second = tmp_path / "a", tmp_path / "b"
    _generate(first)
    _generate(second)
    assert read_json(first / "manifest.json") == read_json(
        second / "manifest.json")
    for entry in read_json(first / "manifest.json")["samples"]:
        for key in ("doc_source", "helper_source"):
            assert (first / "sources" / entry[key]).read_bytes() == (
                second / "sources" / entry[key]).read_bytes()


def test_ground_truth_failure_modes(tmp_path):
    corpus = tmp_path / "corpus"
    generate_corpus(corpus, families=["metacol_mailer", "thus_wiper",
                                      "donoff_interaction", "slow_timeout",
                                      "broken_semantic"],
                    formats=["docm"], techniques=["plain"], seeds=1)
    gt = read_json(corpus / "ground_truth.json")
    by_family = {entry["family"]: gt[entry["id"]]
                 for entry in read_json(corpus / "manifest.json")["samples"]}
    assert by_family["metacol_mailer"]["expected_failure_handled"] == \
        "dynamic_env"
    assert by_family["thus_wiper"]["expected_failure_handled"] == \
        "dynamic_date"
    assert by_family["donoff_interaction"][
        "expected_failure_handled"] is None
    assert by_family["donoff_interaction"][
        "expected_failure_baseline"] == "dynamic_interaction"
    assert by_family["slow_timeout"]["expected_failure_handled"] == \
        "dynamic_timeout"
    assert by_family["broken_semantic"]["expected_failure_handled"] == \
        "dynamic_semantic"


def test_build_corpus_files_and_idempotence(tmp_path):
    corpus = tmp_path / "corpus"
    _generate(corpus)
    result = build_corpus_files(corpus, progress=False)
    assert result["n_built"] == 12
    assert result["n_skipped"] == 0
    manifest = read_json(corpus / "manifest.json")["samples"]
    for entry in manifest:
        path = corpus / "samples" / f"{entry['id']}.docm"
        assert path.exists()
        assert len(extract_modules(path)) == 2
    again = build_corpus_files(corpus, progress=False)
    assert again["n_skipped"] == 12
    overwritten = build_corpus_files(corpus, overwrite=True, progress=False)
    assert overwritten["n_built"] == 12


def test_build_corpus_files_are_byte_reproducible(tmp_path):
    first, second = tmp_path / "a", tmp_path / "b"
    _generate(first)
    _generate(second)
    build_corpus_files(first, progress=False)
    build_corpus_files(second, progress=False)
    manifest = read_json(first / "manifest.json")["samples"]
    for entry in manifest:
        name = f"{entry['id']}.docm"
        digest_a = hashlib.sha256((first / "samples" / name).read_bytes())
        digest_b = hashlib.sha256((second / "samples" / name).read_bytes())
        assert digest_a.hexdigest() == digest_b.hexdigest()


def test_offline_xlsm_includes_worksheet_module(tmp_path):
    corpus = tmp_path / "xlsm"
    generate_corpus(corpus, families=["laroux_replicator"],
                    formats=["xlsm"], techniques=["plain"], seeds=1)
    build_corpus_files(corpus, progress=False)
    entry = read_json(corpus / "manifest.json")["samples"][0]
    modules = extract_modules(
        corpus / "samples" / f"{entry['id']}.xlsm")
    assert {module["name"] for module in modules} == {
        "ThisWorkbook", "Sheet1", "NewMacros"}


def test_package_xlsm(tmp_path):
    path = tmp_path / "sample.xlsm"
    package_office_file([("ThisWorkbook", "document",
                          'Attribute VB_Name = "ThisWorkbook"\n'
                          'Private Sub Workbook_Open()\n  MsgBox "x"\n'
                          'End Sub\n'),
                         ("NewMacros", "procedural",
                          'Attribute VB_Name = "NewMacros"\n')],
                        "xlsm", path)
    modules = extract_modules(path)
    assert {module["name"] for module in modules} == {"ThisWorkbook",
                                                      "NewMacros"}


@pytest.mark.parametrize("technique,flag", [
    ("random", "random"),
    ("split", "split"),
    ("encode", "encode"),
    ("logic", "logic"),
])
def test_obfuscators_change_source_and_keep_entry_point(technique, flag):
    _, doc, helper = build_sample_sources("donoff_downloader", "word")
    out_doc, out_helper = obfuscate_sample(doc, helper, technique, seed=0)
    assert out_doc != doc or out_helper != helper
    assert "Document_Open" in out_doc
    from oblivionx.static.deobfuscator import detect_obfuscation
    assert detect_obfuscation(out_doc)[flag] is True


def test_plain_obfuscation_is_identity():
    _, doc, _helper = build_sample_sources("donoff_downloader", "word")
    assert obfuscate(doc, "plain", 0) == doc


def test_expected_failure_helper():
    assert _expected_failure(FAMILIES["empty_macro"]) == "static_empty"
    assert _expected_failure(FAMILIES["donoff_interaction"],
                             handled=True) is None
    assert _expected_failure(FAMILIES["donoff_interaction"],
                             handled=False) == "dynamic_interaction"
