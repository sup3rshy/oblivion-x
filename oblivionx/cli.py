"""Oblivion-X command line interface.

Commands:
  corpus generate   build corpus sources + ground truth (Linux)
  pipeline run      static + dynamic (simulator) + reconstruction
  eval all          experiments E1-E8
  seg demo          temporal segmentation demo for one sample
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _env_from_args(spec: str):
    """Parse ``outlook=0,ftp=1`` into ``{"outlook": False, "ftp": True}``."""
    out = {}
    for item in (spec or "").split(","):
        item = item.strip()
        if not item:
            continue
        name, _, val = item.partition("=")
        out[name.strip()] = val.strip().lower() not in ("0", "false", "no", "")
    return out


def _cmd_corpus(args):
    from oblivionx.corpus.generate import generate_corpus
    r = generate_corpus(Path(args.out), seeds=args.seeds)
    print(f"corpus generated: {r['n_samples']} samples -> {r['out_dir']}")
    print("next: run scripts/build_corpus_windows.ps1 on Windows to build "
          ".docm/.xlsm files (Word/Excel COM)")


def _cmd_pipeline(args):
    from oblivionx.common import read_json
    from oblivionx.pipeline import run_pipeline
    corpus = Path(args.corpus)
    out = Path(args.out)
    gt = read_json(corpus / "ground_truth.json")
    if not (corpus / "samples").exists():
        print("ERROR: corpus/samples missing — run the Windows corpus "
              "builder first", file=sys.stderr)
        sys.exit(1)
    res = run_pipeline(corpus, out, gt,
                       dynamic_source=args.dynamic_source,
                       dynamic_dir=Path(args.dynamic_dir) if
                       args.dynamic_dir else None,
                       interaction_handled=not args.no_interaction,
                       env_available=_env_from_args(args.env))
    print(f"pipeline done: {len(res)} samples -> {out}")


def _cmd_eval(args):
    from oblivionx.eval.experiments import run_all
    reports = run_all(Path(args.corpus), Path(args.analysis),
                      Path(args.out))
    print(f"experiments written -> {args.out}")


def _cmd_report(args):
    from oblivionx.eval.report import write_markdown_report
    out = write_markdown_report(Path(args.eval), Path(args.out),
                                Path(args.figures) if args.figures else None)
    print(f"report written: {out}")


def _cmd_seg(args):
    from oblivionx.telemetry.segmentation import (explainability_profile,
                                                  segment_frequencies)
    from oblivionx.simulate.simulator import simulate_sample
    from oblivionx.common import read_json
    corpus = Path(args.corpus)
    gt = read_json(corpus / "ground_truth.json")
    sid = args.sample
    manifest = {m["id"]: m for m in
                read_json(corpus / "manifest.json")["samples"]}
    m = manifest[sid]
    sa = simulate_sample(sid, gt[sid], m["family"], m["variant"],
                         m["format"])
    freqs, feats = segment_frequencies(sa.dynamic_events(), 10)
    print(f"sample {sid} ({m['family']}/{m['variant']}): "
          f"{len(sa.dynamic_events())} dynamic events")
    for f in feats:
        print(f"  {f:26s} " + " ".join(f"{v:.2f}" for v in freqs[f]))
    prof = explainability_profile(sa.dynamic_events(), 10)
    print("explainability profile (low/medium/high):")
    for cat, vals in prof.items():
        print(f"  {cat:16s} " + " ".join(v[:1].upper() for v in vals))


def main(argv=None):
    p = argparse.ArgumentParser(prog="oblivionx")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("corpus")
    cs = c.add_subparsers(dest="subcmd", required=True)
    cg = cs.add_parser("generate")
    cg.add_argument("--out", default="outputs/corpus")
    cg.add_argument("--seeds", type=int, default=3)
    cg.set_defaults(func=_cmd_corpus)

    pl = sub.add_parser("pipeline")
    pls = pl.add_subparsers(dest="subcmd", required=True)
    pr = pls.add_parser("run")
    pr.add_argument("--corpus", default="outputs/corpus")
    pr.add_argument("--out", default="outputs/analysis")
    pr.add_argument("--dynamic-source", default="simulator",
                    choices=["simulator", "windows"])
    pr.add_argument("--dynamic-dir", default=None)
    pr.add_argument("--no-interaction", action="store_true",
                    help="do not auto-dismiss MsgBox/InputBox gates")
    pr.add_argument("--env", default="outlook=0,ftp=0",
                    help="comma-separated external dependencies and their "
                         "availability, e.g. outlook=0,ftp=1")
    pr.set_defaults(func=_cmd_pipeline)

    ev = sub.add_parser("eval")
    evs = ev.add_subparsers(dest="subcmd", required=True)
    ea = evs.add_parser("all")
    ea.add_argument("--corpus", default="outputs/corpus")
    ea.add_argument("--analysis", default="outputs/analysis")
    ea.add_argument("--out", default="outputs/eval")
    ea.set_defaults(func=_cmd_eval)

    rp = sub.add_parser("report", help="render the markdown report + figures")
    rp.add_argument("--eval", default="outputs/eval")
    rp.add_argument("--out", default="outputs/report.md")
    rp.add_argument("--figures", default="outputs/figures")
    rp.set_defaults(func=_cmd_report)

    sg = sub.add_parser("seg")
    sg.add_argument("--corpus", default="outputs/corpus")
    sg.add_argument("--sample", required=True)
    sg.set_defaults(func=_cmd_seg)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
