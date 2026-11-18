"""Shared fixtures for the Oblivion-X test suite.

The end-to-end fixtures build a small, fully offline corpus with the pure
Python MS-OVBA writer, so the tests do not require Windows, Office or the
versioned 378-sample corpus.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from oblivionx.common import read_json  # noqa: E402
from oblivionx.corpus.builders import build_corpus_files  # noqa: E402
from oblivionx.corpus.generate import generate_corpus  # noqa: E402

TINY_FAMILIES = [
    "donoff_downloader",
    "donoff_interaction",
    "metacol_mailer",
    "thus_wiper",
    "broken_semantic",
    "empty_macro",
    "slow_timeout",
    "benign_formatting",
]


@pytest.fixture(scope="session")
def tiny_corpus(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A 16-sample corpus with real, oletools-readable Office files."""
    corpus = tmp_path_factory.mktemp("tiny") / "corpus"
    generate_corpus(corpus, families=TINY_FAMILIES, formats=["docm"],
                    techniques=["plain", "split"], seeds=1)
    result = build_corpus_files(corpus, progress=False)
    assert result["n_failed"] == 0
    assert result["n_built"] == 16
    return corpus


@pytest.fixture(scope="session")
def tiny_analysis(tiny_corpus: Path, tmp_path_factory: pytest.TempPathFactory
                  ) -> Path:
    from oblivionx.pipeline import run_pipeline

    out = tmp_path_factory.mktemp("analysis")
    gt = read_json(tiny_corpus / "ground_truth.json")
    run_pipeline(tiny_corpus, out, gt, env_available={"outlook": False,
                                                      "ftp": False},
                 progress=False)
    return out


@pytest.fixture(scope="session")
def tiny_eval(tiny_corpus: Path, tiny_analysis: Path,
              tmp_path_factory: pytest.TempPathFactory) -> Path:
    from oblivionx.eval.experiments import run_all

    out = tmp_path_factory.mktemp("eval")
    run_all(tiny_corpus, tiny_analysis, out)
    return out
