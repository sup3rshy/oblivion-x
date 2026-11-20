"""Oblivion-X command line interface.

Commands:
  corpus generate   build corpus sources + ground truth (Linux)
  corpus build      package sources into .docm/.xlsm files (Linux, offline)
  pipeline run      static + dynamic (simulator) + reconstruction
  eval all          experiments E1-E10
  report            markdown report + figures
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


def _csv(value):
    """Split a comma-separated CLI list, returning None when unset."""
    if not value:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def _cmd_corpus(args):
    from oblivionx.common import FAMILIES, OBFUSCATION_TECHNIQUES
    from oblivionx.corpus.generate import generate_corpus
    families = _csv(args.families)
    formats = _csv(args.formats)
    variants = _csv(args.variants)
    for name in families or []:
        if name not in FAMILIES:
            print(f"ERROR: unknown family {name!r}", file=sys.stderr)
            sys.exit(2)
    for name in formats or []:
        if name not in ("docm", "xlsm"):
            print(f"ERROR: unknown format {name!r}", file=sys.stderr)
            sys.exit(2)
    for name in variants or []:
        if name not in OBFUSCATION_TECHNIQUES:
            print(f"ERROR: unknown variant {name!r}", file=sys.stderr)
            sys.exit(2)
    r = generate_corpus(Path(args.out), families=families, formats=formats,
                        techniques=variants, seeds=args.seeds)
    print(f"corpus generated: {r['n_samples']} samples -> {r['out_dir']}")
    print("next: `python -m oblivionx corpus build` for offline .docm/.xlsm "
          "files, or scripts/build_corpus_windows.ps1 for Office-authored "
          "files (Word/Excel COM)")


def _cmd_corpus_build(args):
    from oblivionx.corpus.builders import build_corpus_files
    r = build_corpus_files(Path(args.corpus),
                           Path(args.out) if args.out else None,
                           overwrite=args.overwrite)
    print(f"corpus built: {r['n_built']} built, {r['n_skipped']} skipped, "
          f"{r['n_failed']} failed -> {r['out_dir']}")
    if r["n_failed"]:
        sys.exit(1)


def _cmd_pipeline(args):
    from oblivionx.common import read_json
    from oblivionx.pipeline import run_pipeline
    corpus = Path(args.corpus)
    out = Path(args.out)
    gt = read_json(corpus / "ground_truth.json")
    if not (corpus / "samples").exists():
        print("ERROR: corpus/samples missing — run `oblivionx corpus build` "
              "(offline) or scripts/build_corpus_windows.ps1 first",
              file=sys.stderr)
        sys.exit(1)
    if args.dynamic_source == "windows" and not args.dynamic_dir:
        print("ERROR: --dynamic-dir is required with --dynamic-source "
              "windows", file=sys.stderr)
        sys.exit(2)
    res = run_pipeline(corpus, out, gt,
                       dynamic_source=args.dynamic_source,
                       dynamic_dir=Path(args.dynamic_dir) if
                       args.dynamic_dir else None,
                       interaction_handled=not args.no_interaction,
                       env_available=_env_from_args(args.env))
    print(f"pipeline done: {len(res)} samples -> {out}")


def _cmd_eval(args):
    from oblivionx.eval.experiments import run_all
    run_all(Path(args.corpus), Path(args.analysis), Path(args.out))
    print(f"experiments written -> {args.out}")


def _cmd_report(args):
    from oblivionx.eval.report import write_markdown_report
    out = write_markdown_report(Path(args.eval), Path(args.out),
                                Path(args.figures) if args.figures else None)
    print(f"report written: {out}")


def _cmd_seg(args):
    from oblivionx.common import read_json
    from oblivionx.simulate.simulator import simulate_sample
    from oblivionx.telemetry.segmentation import explainability_profile, segment_frequencies
    corpus = Path(args.corpus)
    gt = read_json(corpus / "ground_truth.json")
    sid = args.sample
    manifest = {m["id"]: m for m in
                read_json(corpus / "manifest.json")["samples"]}
    if sid not in manifest or sid not in gt:
        print(f"ERROR: unknown sample id {sid!r} in corpus {corpus}",
              file=sys.stderr)
        sys.exit(2)
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
    cg.add_argument("--families", default=None,
                    help="comma-separated family subset (default: all)")
    cg.add_argument("--formats", default=None,
                    help="comma-separated formats: docm,xlsm")
    cg.add_argument("--variants", default=None,
                    help="comma-separated obfuscation variants")
    cg.set_defaults(func=_cmd_corpus)

    cb = cs.add_parser("build", help="package sources into .docm/.xlsm "
                                     "(offline, no Office required)")
    cb.add_argument("--corpus", default="outputs/corpus")
    cb.add_argument("--out", default=None,
                    help="sample directory (default: <corpus>/samples)")
    cb.add_argument("--overwrite", action="store_true",
                    help="rebuild files that already exist")
    cb.set_defaults(func=_cmd_corpus_build)

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
    return 0


if __name__ == "__main__":
    sys.exit(main())
