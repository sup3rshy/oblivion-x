import subprocess
import sys

import pytest

from oblivionx.cli import _env_from_args, main
from oblivionx.common import read_json


def test_env_from_args():
    assert _env_from_args("outlook=0,ftp=1") == {
        "outlook": False, "ftp": True}
    assert _env_from_args("") == {}
    assert _env_from_args("x=yes,y=no,z=") == {
        "x": True, "y": False, "z": False}


def test_module_entry_point():
    result = subprocess.run([sys.executable, "-m", "oblivionx", "--help"],
                            capture_output=True, text=True)
    assert result.returncode == 0
    assert "corpus" in result.stdout


def test_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "corpus" in capsys.readouterr().out


def test_corpus_generate_and_build(tmp_path, capsys):
    corpus = tmp_path / "corpus"
    assert main(["corpus", "generate", "--out", str(corpus),
                 "--families", "donoff_downloader", "--formats", "docm",
                 "--variants", "plain", "--seeds", "1"]) == 0
    assert (corpus / "manifest.json").exists()
    assert main(["corpus", "build", "--corpus", str(corpus)]) == 0
    manifest = read_json(corpus / "manifest.json")["samples"]
    assert (corpus / "samples" /
            f"{manifest[0]['id']}.{manifest[0]['format']}").exists()
    assert "corpus built" in capsys.readouterr().out


def test_pipeline_eval_and_report_cli(tiny_corpus, tiny_eval, tmp_path,
                                      capsys):
    analysis = tmp_path / "analysis"
    assert main(["pipeline", "run", "--corpus", str(tiny_corpus),
                 "--out", str(analysis)]) == 0
    sid = read_json(tiny_corpus / "manifest.json")["samples"][0]["id"]
    assert (analysis / "reconstruction" / f"{sid}.json").exists()

    out = tmp_path / "report.md"
    figures = tmp_path / "figures"
    assert main(["report", "--eval", str(tiny_eval), "--out", str(out),
                 "--figures", str(figures)]) == 0
    assert out.exists()
    assert "report written" in capsys.readouterr().out


def test_windows_source_requires_trace_directory(tiny_corpus, tmp_path,
                                                 capsys):
    with pytest.raises(SystemExit) as exc:
        main(["pipeline", "run", "--corpus", str(tiny_corpus),
              "--out", str(tmp_path / "analysis"),
              "--dynamic-source", "windows"])
    assert exc.value.code == 2
    assert "dynamic-dir" in capsys.readouterr().err


def test_seg_cli(tiny_corpus, capsys):
    sid = read_json(tiny_corpus / "manifest.json")["samples"][0]["id"]
    assert main(["seg", "--corpus", str(tiny_corpus), "--sample", sid]) == 0
    assert "dynamic events" in capsys.readouterr().out


def test_seg_cli_unknown_sample(tiny_corpus, capsys):
    with pytest.raises(SystemExit) as exc:
        main(["seg", "--corpus", str(tiny_corpus), "--sample", "nope"])
    assert exc.value.code == 2
    assert "unknown sample" in capsys.readouterr().err
