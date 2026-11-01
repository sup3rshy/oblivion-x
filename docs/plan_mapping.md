# Plan → implementation mapping

This document maps every requirement of `Ke_hoach_8_de_tai_Malware_Project.pdf`
to concrete code, artifacts and results.

## 1. Paper implementation and baseline

| Role | Paper | Where |
|---|---|---|
| Implementation | Oblivion (J. Computer Virology & Hacking Techniques, 2024) | `oblivionx/`, upstream clone in `third_party/oblivion/` |
| Baseline | Bon-APT (Computers & Security, 2024) | `oblivionx/telemetry/segmentation.py`, summary in `docs/papers/bonapt_summary.md` |
| Oblivion summary | — | `docs/papers/oblivion_summary.md` |

## 2. Problem and research gap

Implemented gap statement: existing systems return a malicious/benign label;
Oblivion-X reconstructs **stages** from evidence, compares static vs dynamic
observability, and uses Bon-APT-style temporal segmentation to test whether
stages separate in time.

## 3. Research questions → experiments

| RQ | Question | Experiment | Result |
|---|---|---|---|
| RQ1 | How many behaviors does the system reconstruct vs ground truth? | E6 | behavior recall **0.981** (1.000 on completed runs) |
| RQ2 | What do static and dynamic analysis each miss? | E2 | static recall **0.896**, dynamic **0.777**, view Jaccard **0.600** |
| RQ3 | Does temporal segmentation separate attack stages? | E4 | boundary F1 **0.636** at N=5, purity **0.929** at N=10 |
| RQ4 | How much does obfuscation reduce observability? | E3 | static recall 0.875–0.923 across variants; detection precision 1.0 |
| RQ5 | Can the attack chain be reconstructed from evidence instead of a label? | E6 | stage accuracy **0.963**, evidence precision **1.000**, chain built from event IDs |

## 4. Mandatory experiments E1–E8

| ID | Experiment | Driver | Output |
|---|---|---|---|
| E1 | Reproduce Oblivion | `experiment_E1` | `outputs/eval/E1_reproduce_oblivion.json` |
| E2 | Static vs dynamic | `experiment_E2` | `E2_static_vs_dynamic.json` |
| E3 | Unobfuscated vs obfuscated | `experiment_E3` | `E3_obfuscation.json` |
| E4 | Temporal segmentation | `experiment_E4` | `E4_temporal_segmentation.json` |
| E5 | Controlled ground truth | `experiment_E5` | `E5_ground_truth.json` |
| E6 | Stage reconstruction | `experiment_E6` | `E6_reconstruction.json` |
| E7 | Failure analysis | `experiment_E7` | `E7_failures.json` |
| E8 | Performance / resource | `experiment_E8` | `E8_performance.json` |

Run with `./.venv/bin/python -m oblivionx eval all`. The markdown report is
`outputs/report.md` (regenerate with `./.venv/bin/python -m oblivionx report`).

## 5. Metrics (8)

| # | Metric | Definition in code | Value (all / completed runs) |
|---|---|---|---|
| 1 | Behavior Recall | `metrics.py:evaluate_sample` | 0.981 / 1.000 |
| 2 | Evidence Precision | claims with ≥1 event / claims | 1.000 / 1.000 |
| 3 | Stage accuracy | LCS F1 of ordered stage chain | 0.963 / 0.964 |
| 4 | Analysis completion rate | not timeout/crash | 0.952 / 1.000 |
| 5 | Timeout rate | `dynamic_timeout` | 0.048 / 0.000 |
| 6 | Deobfuscation success | hidden literal recovered (split/encode/combo) | 0.921 / 1.000 |
| 7 | Analysis time/sample | static + telemetry ms | 21.2 ms mean, p95 31.0 ms |
| 8 | Unsupported behavior claim rate | claims without direct evidence | 0.217 / 0.031 |

Two auxiliary rates are reported alongside: **behavior precision** (0.968)
and **execution success** (0.571 — the macro ran without an environment/date/
interaction gate).

## 6. Four main tasks

| Task | Scope | Code |
|---|---|---|
| 1. Office/macro corpus | 378 safe samples, 14 families × 2 formats × 6 variants × 3 seeds | `corpus/` + `scripts/build_corpus_windows.ps1` |
| 2. Oblivion reproduction | pre-processing taxonomy, static extraction/deobfuscation | `static/`, E1 |
| 3. Telemetry + temporal segmentation | normalized event schema, Bon-APT segmentation | `telemetry/`, `simulate/` |
| 4. Reconstruction / evaluation / error analysis | stage chain, 8 metrics, E1–E8 | `reconstruction/`, `eval/` |

## 7. Eleven-week schedule

| Week | Plan item | Status | Evidence |
|---|---|---|---|
| 1 | Oblivion study/setup | done | `docs/papers/oblivion_summary.md`, `third_party/oblivion/` |
| 2 | Controlled corpus | done | 378 samples, `outputs/corpus/samples/build_report.json` (378 ok) |
| 3 | Static pipeline | done | `static/`, E1 |
| 4 | Dynamic instrumentation | done (simulator) + Windows runner | `simulate/`, `scripts/run_dynamic_windows.ps1` |
| 5 | Reproduce Oblivion | done | E1 |
| 6 | Telemetry normalization | done | `telemetry/normalize.py`, `schema.py` |
| 7 | Temporal segmentation | done | E4 |
| 8 | Behavior reconstruction | done | E6 |
| 9 | Obfuscation study | done | E3 |
| 10 | Ablation/error analysis | done | E7, E8, per-family tables |
| 11 | Artifact/paper | done | `outputs/report.md`, `docs/paper_draft.md` |

## 8. Minimum outputs

| Output | Location |
|---|---|
| Controlled macro corpus | `outputs/corpus/` (manifest, ground truth, 378 files, sources) |
| Oblivion reproduction | E1 + `oblivionx/static/` |
| Telemetry normalization | `oblivionx/telemetry/` |
| Temporal stage reconstruction | `oblivionx/reconstruction/`, E4/E6 |
| Static vs dynamic comparison | E2, `docs/report` tables |
| Paper draft | `docs/paper_draft.md` |

## 9. Honest limitations

- **Dynamic telemetry is simulated** by default (`simulate/simulator.py`,
  deterministic, seeded by SHA-256 of the sample id). It models stage order,
  timings, benign noise and the five failure classes, but it is not real
  Office execution. `--dynamic-source windows` consumes real traces in the
  same schema; `scripts/run_dynamic_windows.ps1` currently captures
  entry/exit timing and errors only. Smoke test (3 downloader samples):
  Word is terminated shortly after the macro spawns PowerShell
  (`office_terminated`), most likely by endpoint protection; benign
  samples run normally. A full real-execution run was not performed.
- The corpus is **inert by construction** (127.0.0.1 / example.com, marker
  payloads, XOR-only "encryption").
- The E1 `empty` class is defined as "VBA project with no executable
  statements", which includes the `empty_macro` family only.
- Stage accuracy uses an order-preserving LCS F1, not exact positional
  equality, because a missed middle stage should not zero the whole chain.
