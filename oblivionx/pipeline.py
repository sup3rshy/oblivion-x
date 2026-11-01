"""End-to-end analysis pipeline for one corpus.

For each sample: static analysis (Linux) + dynamic telemetry (simulator, or
Windows traces when available) + reconstruction, written as JSON artifacts:

  analysis/static/<id>.json
  analysis/dynamic/<id>.json
  analysis/reconstruction/<id>.json
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from oblivionx.common import read_json, write_json
from oblivionx.reconstruction.reconstruct import reconstruct
from oblivionx.simulate.simulator import simulate_sample
from oblivionx.static.analyzer import analyze_static
from oblivionx.static.extractor import file_sha256
from oblivionx.telemetry.normalize import normalize
from oblivionx.telemetry.schema import SampleAnalysis


def run_pipeline(corpus_dir: Path, out_dir: Path,
                 gt: Dict[str, Any],
                 dynamic_source: str = "simulator",
                 dynamic_dir: Optional[Path] = None,
                 interaction_handled: bool = True,
                 env_available: Optional[Dict[str, bool]] = None,
                 progress: bool = True) -> Dict[str, str]:
    """Analyze every sample in the corpus manifest."""
    corpus_dir = Path(corpus_dir)
    out_dir = Path(out_dir)
    manifest = read_json(corpus_dir / "manifest.json")["samples"]
    (out_dir / "static").mkdir(parents=True, exist_ok=True)
    (out_dir / "dynamic").mkdir(parents=True, exist_ok=True)
    (out_dir / "reconstruction").mkdir(parents=True, exist_ok=True)
    results: Dict[str, str] = {}

    for i, m in enumerate(manifest):
        sid = m["id"]
        sample_file = corpus_dir / "samples" / f"{sid}.{m['format']}"
        gt_sample = gt.get(sid, m.get("ground_truth", {}))

        # ---- static -----------------------------------------------------
        t0 = time.time()
        if sample_file.exists():
            sa_static = analyze_static(sample_file, sid, m["family"],
                                       m["variant"], m["format"])
            sa_static.meta["analysis_time_ms"] = (time.time() - t0) * 1000
            sa_static.meta["sha256"] = file_sha256(sample_file)
        else:
            sa_static = SampleAnalysis(sample_id=sid, family=m["family"],
                                       variant=m["variant"], format=m["format"])
            sa_static.meta = {"analysis_time_ms": (time.time() - t0) * 1000,
                              "n_modules": 0, "obfuscation_detected": {},
                              "recovered_payloads": [], "status": "error",
                              "failure": "av_blocked",
                              "note": "corpus build failed (AV file-permission error)"}
        write_json(sa_static.to_dict(), out_dir / "static" / f"{sid}.json")

        # ---- dynamic -----------------------------------------------------
        t0 = time.time()
        if dynamic_source == "simulator":
            sa_dyn = simulate_sample(
                sid, gt_sample, m["family"], m["variant"], m["format"],
                interaction_handled=interaction_handled,
                env_available=env_available)
        else:
            trace_file = (Path(dynamic_dir) / f"{sid}.log")
            if trace_file.exists():
                sa_dyn = normalize(trace_file, "vba_trace", sid,
                                   m["family"], m["variant"])
            else:
                sa_dyn = SampleAnalysis(sample_id=sid, family=m["family"],
                                        variant=m["variant"],
                                        format=m["format"])
                sa_dyn.meta["failure"] = "dynamic_missing_trace"
        sa_dyn.meta["analysis_time_ms"] = (time.time() - t0) * 1000
        write_json(sa_dyn.to_dict(), out_dir / "dynamic" / f"{sid}.json")

        # ---- merge static + dynamic, reconstruct --------------------------
        merged = SampleAnalysis(sample_id=sid, family=m["family"],
                                variant=m["variant"], format=m["format"])
        merged.events = sa_static.events + sa_dyn.events
        merged.meta = {**sa_dyn.meta, "n_static": len(sa_static.events),
                       "n_dynamic": len(sa_dyn.events)}
        rec = reconstruct(merged)
        write_json(rec.to_dict(), out_dir / "reconstruction" / f"{sid}.json")
        results[sid] = "ok"
        if progress and (i + 1) % 50 == 0:
            print(f"  pipeline: {i + 1}/{len(manifest)}")
    return results
