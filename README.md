# Oblivion-X

**Tái dựng chuỗi hành vi của macro malware từ dynamic telemetry**
(Behavior Reconstruction and Stage-Aware Analysis of Macro-Based Office
Malware)

Implementation of the 8-topic malware research plan
(`Ke_hoach_8_de_tai_Malware_Project.pdf`), combining:

| Role | Paper | Venue | Year |
|---|---|---|---|
| Implementation | **Oblivion**: an open-source system for large-scale analysis of macro-based office malware | J. Computer Virology & Hacking Techniques | 2024 |
| Baseline | **Bon-APT**: detection, attribution & explainability of APT malware using temporal segmentation of API calls | Computers & Security | 2024 |

## Research questions

- **RQ1** — Oblivion tái dựng được bao nhiêu behavior so với ground truth?
- **RQ2** — Static và dynamic analysis bỏ sót những gì?
- **RQ3** — Temporal segmentation có giúp tách attack stages không?
- **RQ4** — Obfuscation làm giảm observability bao nhiêu?
- **RQ5** — Có thể tái dựng attack chain từ evidence thay vì chỉ label không?

## Repository layout

```
oblivionx/
  common.py              behavior catalog, stages, family definitions (GT)
  corpus/                Task 1: controlled macro corpus
    vba_sources.py         VBA family templates (safe simulated payloads)
    obfuscators.py         4 obfuscation transforms (random/split/encode/logic)
    msovba.py               MS-OVBA vbaProject.bin + MS-CFB writer (pure Python)
    builders.py             OOXML packaging (static-only mode)
    generate.py             corpus manifest + ground truth (E5)
  static/                Task 2: static pipeline (extraction, obfuscation
    extractor.py            detection, deobfuscation, indicators)
    deobfuscator.py
    analyzer.py
  telemetry/             Task 3: normalization + temporal segmentation
    schema.py               common Event schema
    normalize.py            VBA trace / Oblivion report parsers
    segmentation.py         Bon-APT segmentation (N=1/5/10/20, combos)
  reconstruction/        Task 4: stage reconstruction (RQ1/RQ5)
  simulate/              dynamic telemetry simulator (Linux, deterministic)
  eval/                  metrics (8), experiments E1-E8, markdown report
  pipeline.py            end-to-end analysis pipeline
scripts/
  build_corpus_windows.ps1   Word/Excel COM corpus builder (authoritative)
  dismiss_activation.ps1     background killer for the Office Activation
                             Wizard (unactivated Office blocks COM saves)
  run_dynamic_windows.ps1    real Office execution (entry/exit timing + errors)
third_party/oblivion/    upstream Oblivion repo (E1 reproduction)
outputs/                 corpus, analysis artifacts, experiment reports
docs/                    paper summaries, plan mapping, paper draft
```

## Quickstart (Linux side)

```bash
.venv/bin/python -m oblivionx corpus generate --out outputs/corpus
.venv/bin/python -m oblivionx pipeline run --corpus outputs/corpus --out outputs/analysis
.venv/bin/python -m oblivionx eval all --corpus outputs/corpus \
    --analysis outputs/analysis --out outputs/eval
.venv/bin/python -m oblivionx report          # markdown report + figures
```

Building the real `.docm`/`.xlsm` corpus requires Windows + Office
(this repo's machine qualifies):

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\dismiss_activation.ps1 -Seconds 3600   # background
powershell.exe -ExecutionPolicy Bypass -File scripts\build_corpus_windows.ps1 `
    -ManifestPath D:\oblivion\outputs\corpus\manifest.json `
    -OutDir D:\oblivion\outputs\corpus\samples
```

The pure-Python `msovba.py` writer also produces files that oletools parses
correctly (usable for static-only workflows); Word-authored files are used
for anything that must actually execute.

## Corpus (controlled ground truth — E5)

378 samples = 14 families × 2 formats × 6 obfuscation variants × 3 seeds.
All "malicious" families are **simulated, inert** (URLs point at
127.0.0.1, payloads are markers, "encryption" is reversible XOR on a
sandbox folder) so the corpus is safe to execute anywhere.

| Family | Type | Stages |
|---|---|---|
| donoff_downloader | PowerShell download + run | delivery → defense_evasion → execution → c2_download → impact |
| donoff_interaction | MsgBox-gated downloader | delivery → defense_evasion → execution → c2_download → impact |
| metacol_mailer | Outlook mass-mail | delivery → exfiltration |
| laroux_replicator | template/XLSTART infection | delivery → execution → persistence → impact |
| locky_ransom | registry + XOR "encryption" | delivery → execution → persistence → impact |
| vba_dropper | write and run an executable | delivery → execution → impact |
| marker_ftp | FTP log upload | delivery → execution → exfiltration → impact |
| thus_wiper | date-gated deletion | delivery → execution → impact |
| valyria_dual | download + exfiltrate | delivery → c2_download → exfiltration |
| slow_timeout | busy loop, then shell | delivery → execution |
| broken_semantic | undefined call (failure control) | delivery |
| empty_macro | project with no code | — |
| benign_formatting / benign_report | benign controls | delivery |

Obfuscation variants: `plain`, `random`, `split`, `encode`, `logic`, `combo`.

## Metrics (plan Section 5)

Behavior Recall · Evidence Precision · Stage accuracy · Analysis completion
rate · Timeout rate · Deobfuscation success · Analysis time/sample ·
Unsupported behavior claim rate — implemented in `oblivionx/eval/metrics.py`.

## Experiments (plan Section 4)

| ID | Experiment | Answers |
|---|---|---|
| E1 | Reproduce Oblivion | pre-processing taxonomy on the corpus |
| E2 | Static vs dynamic | RQ2 |
| E3 | Unobfuscated vs obfuscated | RQ4 |
| E4 | Temporal segmentation | RQ3 |
| E5 | Controlled ground truth | corpus self-check |
| E6 | Stage reconstruction | RQ1, RQ5 |
| E7 | Failure analysis | failure taxonomy |
| E8 | Performance / resource analysis | time per sample, timeouts |
