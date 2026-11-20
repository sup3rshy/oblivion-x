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
| RQ1 | How many behaviors does the system reconstruct vs ground truth? | E6 | behavior recall **0.990** (1.000 on completed runs) |
| RQ2 | What do static and dynamic analysis each miss? | E2 | static recall **0.905**, dynamic **0.837**, view Jaccard **0.643** |
| RQ3 | Does temporal segmentation separate attack stages? | E4 | boundary F1 **0.629** at N=5, purity **0.922** at N=10; permutation null mean z **0.91** |
| RQ4 | How much does obfuscation reduce observability? | E3 | static recall 0.879–0.926 across variants; detection precision 1.0 |
| RQ5 | Can the attack chain be reconstructed from evidence instead of a label? | E6, E9 | stage accuracy **0.963** (ontology order) / **0.854** (evidence order), evidence precision **1.000** |
| RQ5 (support) | Can an analyst anticipate which stages will be unobservable? | E10 | AUC **0.669** out of family; shared mechanisms predict, unique mechanisms do not |

## 4. Mandatory experiments E1–E10

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
| E9 | Chain-order ablation (extension) | `experiment_E9` | `E9_chain_order.json` |
| E10 | Completion calibration (extension) | `experiment_E10` | `E10_completion_calibration.json` |

Run with `./.venv/bin/python -m oblivionx eval all`. The markdown report is
`outputs/report.md` (regenerate with `./.venv/bin/python -m oblivionx report`).

## 5. Metrics (8)

| # | Metric | Definition in code | Value (all / completed runs) |
|---|---|---|---|
| 1 | Behavior Recall | `metrics.py:evaluate_sample` | 0.990 / 1.000 |
| 2 | Evidence Precision | claims with ≥1 event / claims | 1.000 / 1.000 |
| 3 | Stage accuracy | LCS F1 of ordered stage chain | 0.963 / 0.964 |
| 4 | Analysis completion rate | not timeout/crash | 0.952 / 1.000 |
| 5 | Timeout rate | `dynamic_timeout` | 0.048 / 0.000 |
| 6 | Deobfuscation success | hidden literal recovered (split/encode/combo) | 0.967 / 1.000 |
| 7 | Analysis time/sample | static + telemetry ms | 2.4 ms mean, p95 3.7 ms (warm cache) |
| 8 | Unsupported behavior claim rate | claims without direct evidence | 0.151 / 0.031 |

Two auxiliary rates are reported alongside: **behavior precision** (0.968)
and **execution success** (0.571 — the macro ran without an environment/date/
interaction gate).

## 6. Four main tasks

| Task | Scope | Code |
|---|---|---|
| 1. Office/macro corpus | 378 safe samples, 14 families (docm/xlsm where applicable) × 6 variants × 3 seeds | `corpus/` + `scripts/build_corpus_windows.ps1` |
| 2. Oblivion reproduction | pre-processing taxonomy, static extraction/deobfuscation | `static/`, E1 |
| 3. Telemetry + temporal segmentation | normalized event schema, Bon-APT segmentation | `telemetry/`, `simulate/` |
| 4. Reconstruction / evaluation / error analysis | stage chain, 8 metrics, E1–E10 | `reconstruction/`, `eval/` |

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
- E9 shows that ontology ordering accounts for ~0.11 of the E6 stage
  accuracy; the evidence-ordered score (0.854) is the defensible RQ5 number.
- E10 is a negative result by design: completion prediction on static
  features reaches AUC 0.669 out of family and is only reliable for failure
  mechanisms shared across families. Unique gates (FTP, date, timeout,
  semantic error) regress to the base rate, so the unsupported-claim rate
  must be measured, not predicted.

## 10. Reproducibility and engineering quality

- **Offline corpus build.** `python -m oblivionx corpus build` assembles the
  generated sources into oletools-readable `.docm`/`.xlsm` files with the
  pure-Python MS-OVBA/CFB writer. A full 378-sample offline build reproduces
  the same taxonomy and metrics as the Word/Excel-authored corpus, without
  Windows or Office. Files are byte-reproducible (fixed project IDs and zip
  timestamps); existing samples are skipped unless `--overwrite` is passed.
- **Determinism.** The simulator uses a fixed analysis date
  (`2024-01-01`) so date-gated samples do not change behaviour on December
  13; JSON tie-breaking is explicit (`_top` in `eval/experiments.py`); corpus
  source generation is seeded.
- **Tests.** `tests/` contains 100+ offline unit and end-to-end tests
  covering extraction, deobfuscation, schema, segmentation, simulation,
  reconstruction, metrics, experiments, report generation and the CLI.
  `make test` runs them; `make lint` runs ruff; CI runs both on Python 3.10,
  3.11 and 3.12.
- **Packaging.** `pyproject.toml` declares dependencies, package data
  (`oblivionx/resources/*`), the `oblivionx` console script and the
  pytest/ruff configuration.
