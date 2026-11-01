"""Corpus generator (Linux side).

Produces, for every sample:
  * the two VBA module sources (document module + helper module)
  * ground-truth metadata (family, stages, behaviors, obfuscation, expected
    failure mode, environment/date gates)

The actual .docm/.xlsm files are then assembled by
scripts/build_corpus_windows.ps1 (Word/Excel COM automation), which
produces byte-identical-to-Office projects. The pure-Python
package_office_file() in builders.py remains available for offline
static-analysis-only corpora.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

from oblivionx.common import (BEHAVIOR_DEFS, FAMILIES,
                              OBFUSCATION_TECHNIQUES, STAGE_ORDER, write_json)
from oblivionx.corpus.obfuscators import obfuscate_sample
from oblivionx.corpus.vba_sources import build_sample_sources

DEFAULT_SEEDS = 3          # variants per (family, format, obfuscation)
DEFAULT_TECHNIQUES = OBFUSCATION_TECHNIQUES
DEFAULT_FORMATS = ["docm", "xlsm"]


def _sample_id(family: str, fmt: str, variant: str, seed: int) -> str:
    return f"{family}__{fmt}__{variant}__{seed:02d}"


def generate_corpus(out_dir: Path,
                    families: Optional[List[str]] = None,
                    formats: Optional[List[str]] = None,
                    techniques: Optional[List[str]] = None,
                    seeds: int = DEFAULT_SEEDS) -> Dict[str, Any]:
    families = families or list(FAMILIES.keys())
    formats = formats or DEFAULT_FORMATS
    techniques = techniques or DEFAULT_TECHNIQUES
    out_dir = Path(out_dir)
    src_dir = out_dir / "sources"
    src_dir.mkdir(parents=True, exist_ok=True)

    manifest: List[Dict[str, Any]] = []
    for family in families:
        spec = FAMILIES[family]
        for fmt in formats:
            if fmt not in spec.formats:
                continue
            host = "word" if fmt == "docm" else "excel"
            doc_name, doc_src, helper_src = build_sample_sources(family, host)
            for variant in techniques:
                for seed in range(seeds):
                    sid = _sample_id(family, fmt, variant, seed)
                    if family == "empty_macro":
                        # There is no code to obfuscate: an "empty" project
                        # stays empty under every technique label.
                        ob_doc, ob_help = doc_src, helper_src
                    else:
                        ob_doc, ob_help = obfuscate_sample(
                            doc_src, helper_src, variant, seed)
                    doc_path = src_dir / f"{sid}__{doc_name}.vba"
                    helper_path = src_dir / f"{sid}__NewMacros.vba"
                    doc_path.write_text(ob_doc, encoding="latin-1")
                    helper_path.write_text(ob_help, encoding="latin-1")

                    gt_behaviors = list(spec.behaviors)
                    if family != "empty_macro":
                        if variant in ("split", "combo"):
                            gt_behaviors.append("string_concat")
                        if variant in ("encode", "combo"):
                            gt_behaviors.extend(["chr_encode",
                                                 "base64_encode"])
                        if variant in ("logic", "combo"):
                            gt_behaviors.append("dead_code")

                    # Ground-truth stages are the projection of the
                    # ground-truth behaviors onto the stage ontology. This
                    # keeps the behavior and stage ground truths consistent
                    # by construction (E5) and makes stage scoring fair.
                    beh_stages = {BEHAVIOR_DEFS[b].stage
                                  for b in gt_behaviors if b in BEHAVIOR_DEFS}
                    gt_stages = [s for s in STAGE_ORDER if s in beh_stages]

                    manifest.append({
                        "id": sid,
                        "family": family,
                        "format": fmt,
                        "host": host,
                        "variant": variant,
                        "seed": seed,
                        "doc_module": doc_name,
                        "doc_source": doc_path.name,
                        "helper_source": helper_path.name,
                        "ground_truth": {
                            "stages": gt_stages,
                            "intended_stages": spec.stages,
                            "behaviors": sorted(set(gt_behaviors)),
                            "obfuscation": []
                            if variant == "plain" or family == "empty_macro"
                            else [variant],
                            "interaction": spec.interaction,
                            "env_dep": spec.env_dep,
                            "date_trigger": spec.date_trigger,
                            "timeout": spec.timeout,
                            # Failure class in a vanilla sandbox: no MsgBox
                            # handling and no external software (Outlook/FTP).
                            "expected_failure_baseline": _expected_failure(spec),
                            # Failure class with interaction handling enabled
                            # (the Oblivion-X configuration).
                            "expected_failure_handled":
                                _expected_failure(spec, handled=True),
                            # Backwards-compatible alias for the baseline.
                            "expected_failure": _expected_failure(spec),
                        },
                        "sha256_source": hashlib.sha256(
                            (ob_doc + ob_help).encode("latin-1")).hexdigest(),
                    })

    gt_index = {m["id"]: m["ground_truth"] for m in manifest}
    write_json({"samples": manifest}, out_dir / "manifest.json")
    write_json(gt_index, out_dir / "ground_truth.json")
    return {"out_dir": str(out_dir), "n_samples": len(manifest)}


def _expected_failure(spec, handled: bool = False) -> Optional[str]:
    """Expected failure class for a configuration.

    ``handled=False`` is a vanilla sandbox (interaction gates unhandled);
    ``handled=True`` is the Oblivion-X configuration where MsgBox/InputBox
    windows are dismissed automatically. Missing external software (Outlook,
    FTP) is *not* fixed by interaction handling, so ``dynamic_env`` remains.
    """
    if spec.family == "broken_semantic":
        return "dynamic_semantic"
    if spec.family == "empty_macro":
        return "static_empty"
    if spec.family == "slow_timeout":
        return "dynamic_timeout"
    if spec.interaction:
        return None if handled else "dynamic_interaction"
    if spec.env_dep:
        return "dynamic_env"               # dependency missing in both configs
    if spec.date_trigger:
        return "dynamic_date"              # unless run on Dec 13
    return None
