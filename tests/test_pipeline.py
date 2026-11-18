from pathlib import Path

from oblivionx.common import read_json
from oblivionx.corpus.builders import build_corpus_files
from oblivionx.corpus.generate import generate_corpus
from oblivionx.pipeline import run_pipeline


def _run(corpus: Path, out: Path, **kwargs):
    gt = read_json(corpus / "ground_truth.json")
    return run_pipeline(corpus, out, gt, progress=False, **kwargs)


def test_pipeline_writes_all_artifacts(tiny_corpus, tmp_path):
    out = tmp_path / "analysis"
    result = _run(tiny_corpus, out)
    manifest = read_json(tiny_corpus / "manifest.json")["samples"]
    assert len(result) == len(manifest)
    for entry in manifest:
        sid = entry["id"]
        for kind in ("static", "dynamic", "reconstruction"):
            assert (out / kind / f"{sid}.json").exists()
        static = read_json(out / "static" / f"{sid}.json")
        dynamic = read_json(out / "dynamic" / f"{sid}.json")
        assert static["sample_id"] == sid
        assert dynamic["sample_id"] == sid


def test_pipeline_merged_analysis_time_includes_static_work(tiny_corpus,
                                                           tmp_path):
    out = tmp_path / "analysis"
    _run(tiny_corpus, out)
    sid = read_json(tiny_corpus / "manifest.json")["samples"][0]["id"]
    static = read_json(out / "static" / f"{sid}.json")
    dynamic = read_json(out / "dynamic" / f"{sid}.json")
    # Re-running the merged view is what E6 consumes.
    from oblivionx.eval.experiments import _merge
    merged = _merge(out, sid, {"family": "x", "variant": "plain",
                               "format": "docm"})
    expected = (static["meta"]["analysis_time_ms"]
                + dynamic["meta"]["analysis_time_ms"])
    assert merged.meta["analysis_time_ms"] == expected
    assert merged.meta["analysis_time_ms"] >= static["meta"][
        "analysis_time_ms"]


def test_missing_corpus_file_is_a_static_failure(tmp_path):
    corpus = tmp_path / "corpus"
    generate_corpus(corpus, families=["donoff_downloader"], formats=["docm"],
                    techniques=["plain"], seeds=1)
    build_corpus_files(corpus, progress=False)
    manifest = read_json(corpus / "manifest.json")["samples"]
    sid = manifest[0]["id"]
    (corpus / "samples" / f"{sid}.docm").unlink()

    out = tmp_path / "analysis"
    _run(corpus, out)
    static = read_json(out / "static" / f"{sid}.json")
    assert static["meta"]["failure"] == "static_av_blocked"

    from oblivionx.eval.experiments import _merge
    from oblivionx.eval.metrics import evaluate_sample
    from oblivionx.reconstruction.reconstruct import reconstruct
    merged = _merge(out, sid, manifest[0])
    rec = reconstruct(merged)
    metrics = evaluate_sample(merged, rec,
                              read_json(corpus / "ground_truth.json")[sid])
    assert metrics.completed is False


def test_missing_windows_trace_is_reported(tiny_corpus, tmp_path):
    out = tmp_path / "analysis"
    _run(tiny_corpus, out, dynamic_source="windows",
         dynamic_dir=tmp_path / "no-traces")
    sid = read_json(tiny_corpus / "manifest.json")["samples"][0]["id"]
    dynamic = read_json(out / "dynamic" / f"{sid}.json")
    assert dynamic["meta"]["failure"] == "dynamic_missing_trace"

    from oblivionx.eval.experiments import _merge
    from oblivionx.eval.metrics import evaluate_sample
    from oblivionx.reconstruction.reconstruct import reconstruct
    merged = _merge(out, sid, {"family": "x", "variant": "plain",
                               "format": "docm"})
    rec = reconstruct(merged)
    metrics = evaluate_sample(merged, rec,
                              read_json(tiny_corpus / "ground_truth.json")[sid])
    assert metrics.completed is False
