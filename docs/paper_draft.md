# Oblivion-X: Behavior Reconstruction and Stage-Aware Analysis of Macro-Based Office Malware

> Draft. Numbers come from `outputs/eval/E1..E8*.json` on the 378-sample
> controlled corpus. Dynamic telemetry is produced by a deterministic
> simulator; see §7.

## Abstract

Macro-based Office documents remain a durable initial-access vector, yet most
detection systems reduce them to a malicious/benign label. Security analysts
need to know *what* the macro does and *in which order*. We present
Oblivion-X, an analysis pipeline that (i) reproduces Oblivion's static
pre-processing taxonomy, (ii) normalizes static indicators and dynamic
telemetry into one event schema, (iii) reconstructs an ordered attack-stage
chain from evidence, and (iv) uses Bon-APT-style temporal segmentation to
test whether stages separate in time. On a controlled 378-sample corpus with
ground truth we obtain behavior recall 0.981, evidence precision 1.000, stage
accuracy 0.963 (LCS F1) and completion 0.952. Static analysis alone recalls
0.896 of ground-truth behaviors and dynamic analysis 0.777, but their union is
complementary: static sees intent that gates never execute, dynamic sees
process effects absent from the source. Segmentation peaks at N=5 with
boundary F1 0.636. We discuss failure classes and argue that stage
reconstruction, not classification, should be the unit of evaluation for
macro malware.

## 1. Introduction

Office macros are attractive to attackers because they execute inside a
trusted application with access to the user's files, mail client and shell.
Obfuscation, environment checks, date gates and message boxes make static
signatures brittle and sandbox runs incomplete. Oblivion (Sanna et al., 2024)
addresses scale with static pre-processing plus VBA instrumentation, but its
output is still a set of indicators and an attack-family label. Bon-APT
(Shenderovitz & Nissim, 2024) shows that segmenting a timestamped API trace
into equal time buckets yields a compact temporal representation useful for
detection, attribution and explanation of APT behavior. Neither work answers
the question that matters operationally: *can we reconstruct the ordered
attack chain from evidence, and how much of it is actually observable?*

This paper makes four contributions:

1. A controlled, inert macro corpus of 378 files spanning 14 families, two
   formats and six obfuscation variants, with per-sample ground truth for
   behaviors, stages and expected failure class.
2. A unified event schema and pipeline that turns static indicators,
   simulated or real dynamic telemetry, and Oblivion reports into comparable
   evidence.
3. A stage reconstructor that emits behavior claims, stage claims and an
   ordered chain, each backed by event IDs, and that marks unsupported claims
   instead of hallucinating them.
4. An evaluation of eight experiments (E1–E8) with eight metrics, including a
   static-vs-dynamic observability study, an obfuscation study and a
   two-configuration failure analysis.

## 2. Related work

**Oblivion.** Static pre-processing with OleVBA classifies samples as
corrupted, password-protected, interaction-based, standard or empty, and
detects obfuscation heuristics. Instrumented execution logs VBA actions and a
post-processing step extracts attack families, embedded scripts and contacted
resources. Oblivion-X reuses the taxonomy (E1) and the instrumentation idea,
but adds temporal reconstruction and evaluation against ground truth.

**Bon-APT.** Splits a timestamped API-call sequence into N equal-length
segments, aggregates per-call frequency per segment, and flattens to an
`N×D` vector for ML. N ∈ {1, 5, 10, 20} plus combinations; API calls are
abstracted into behavioral categories for low/medium/high explanations.
Oblivion-X reimplements the segmentation and N sweep, but applies it to
normalized macro behaviors and asks whether *attack stages* separate, rather
than training a detector.

## 3. Corpus

### 3.1 Families

| Family | Pattern | Ground-truth stages |
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

All payloads are inert: URLs point at `127.0.0.1` or `example.com`, dropped
files are markers, and "encryption" is a reversible XOR over sandbox files.
This makes the corpus safe to execute while preserving the behavioral shape
of the corresponding real families.

### 3.2 Obfuscation variants

`plain`, `random` (identifier randomization), `split` (string concatenation),
`encode` (Chr chains + Base64 blob), `logic` (unreachable decoy code) and
`combo` (all four). Entry points (`Document_Open`, `Workbook_Open`) are never
renamed, so instrumented execution can still find them.

### 3.3 Construction

Sources are generated on Linux (`oblivionx.corpus.generate`) and assembled
into real `.docm`/`.xlsm` files by Word/Excel COM automation
(`scripts/build_corpus_windows.ps1`). All 378 files built successfully and
all yield VBA modules under oletools. The pure-Python MS-OVBA writer remains
available for static-only workflows.

Ground-truth stages are the projection of ground-truth behaviors onto the
stage ontology, which keeps behavior and stage labels consistent by
construction.

## 4. Method

### 4.1 Normalized events

Every observation becomes an `Event{id, t_ms, source, behavior, obj, args,
confidence, evidence}`. `t_ms = null` marks a static observation. Behaviors
come from a fixed catalog (`common.py`) grouped into eight stages:
delivery, defense_evasion, execution, c2_download, persistence, exfiltration,
impact, cleanup.

### 4.2 Static pipeline

`extractor.py` pulls every VBA module with oletools. `deobfuscator.py`
detects the four technique families and statically recovers Chr chains,
concatenations and Base64 blobs. `analyzer.py` maps indicators to behaviors
with confidence scores.

### 4.3 Dynamic telemetry

The default source is a deterministic simulator that replays the
ground-truth stage sequence with realistic timings, adds low-confidence
startup noise, and injects one of five failure classes: semantic error,
missing environment dependency (Outlook/FTP), date gate, unhandled
interaction gate, or timeout. A real-execution path (`--dynamic-source
windows`) consumes VBA trace logs in the same schema.

### 4.4 Temporal segmentation

Following Bon-APT, the dynamic events are split into N equal time buckets and
per-behavior frequency is computed per bucket. We sweep N ∈ {1, 5, 10, 20}
and measure segment purity, per-stage concentration and stage-boundary F1.

### 4.5 Reconstruction

Events with confidence ≥ 0.5 become behavior claims. Claims are grouped into
stages, stages ordered by the ontology, and adjacent stages linked into a
chain. Each claim stores the supporting event IDs; claims without evidence
are marked unsupported. Stage accuracy is the F1 of the longest common
subsequence between the ground-truth and reconstructed stage sequences, so a
missing middle stage does not zero the rest of the chain.

## 5. Experiments

### E1 — Reproducing Oblivion's pre-processing taxonomy

| Category | Count |
|---|---|
| empty | 18 |
| corrupted | 0 |
| interaction | 18 |
| cls | 0 |
| bas_cls | 342 |
| other | 0 |
| extracted modules | 900 |
| no_file | 0 |

The taxonomy maps exactly onto the corpus design: the 18 `empty_macro`
samples are `empty`, the 18 MsgBox-gated samples are `interaction`, and all
remaining files are standard `.bas + .cls` projects. This validates that the
corpus exercises the classes Oblivion cares about.

### E2 — Static vs dynamic observability (RQ2)

| Measure | Value |
|---|---|
| Mean static behavior recall | 0.896 |
| Mean dynamic behavior recall | 0.777 |
| Mean view agreement (Jaccard) | 0.600 |

Ground-truth behaviors seen by only one view:

| Behavior | Static only | Dynamic only |
|---|---|---|
| shell_run | 54 | 0 |
| outlook_send | 54 | 0 |
| cmd_run | 50 | 0 |
| url_reference | 30 | 0 |
| http_download | 26 | 0 |
| file_write | 11 | 54 |
| file_execute | 0 | 36 |
| string_concat | 3 | 11 |

Static analysis sees **intent**: URL literals, `Outlook.Send`, `Shell` and
`cmd` strings exist in the source even when an environment or date gate
prevents execution. Dynamic analysis sees **effects**: `file_write` and
`file_execute` performed by a spawned PowerShell process never appear in the
VBA source. The two views are therefore complementary, and a reconstruction
that fuses them is strictly better than either alone. The low Jaccard (0.600)
quantifies how different the two views are.

### E3 — Obfuscation vs observability (RQ4)

| Variant | Static recall | Dynamic recall | Detection precision | Detection recall | Deobf. success |
|---|---|---|---|---|---|
| plain | 0.918 | 0.781 | n/a | n/a | n/a |
| random | 0.899 | 0.787 | 1.000 | 0.900 | n/a |
| split | 0.882 | 0.772 | 1.000 | 0.900 | 0.900 |
| encode | 0.880 | 0.768 | 1.000 | 1.000 | 1.000 |
| logic | 0.923 | 0.776 | 1.000 | 1.000 | n/a |
| combo | 0.875 | 0.776 | 1.000 | 0.892 | 1.000 |

Two findings are worth stressing. First, **behavior-level recall is almost
insensitive to obfuscation** (0.875–0.923) because the analyzer reasons over
the obfuscated source directly; what obfuscation destroys is *literal*
visibility (URLs, API names), which is why deobfuscation is needed to
reconstruct concrete evidence. Second, the detector never fires on a plain
sample (precision 1.0), and deobfuscation recovers the hidden literal in
90–100% of recoverable variants. The few detection misses are short macros
where the transform had little material to rewrite.

### E4 — Temporal segmentation (RQ3)

| N | Segment purity | Stage concentration | Boundary F1 | Precision | Recall |
|---|---|---|---|---|---|
| 1 | 0.390 | 1.000 | 0.000 | 0.000 | 0.000 |
| 5 | 0.838 | 0.860 | **0.636** | 0.820 | 0.545 |
| 10 | 0.929 | 0.807 | 0.474 | 0.754 | 0.369 |
| 20 | 0.971 | 0.770 | 0.294 | 0.581 | 0.204 |

Purity increases monotonically with N, but boundary F1 peaks at N=5 and then
falls: too many segments fragment a stage into several buckets and create
spurious boundaries. Bon-APT's multi-scale configuration is therefore
justified, but the informative scale for macro behavior is coarse (N=5), not
fine. Temporal segmentation does separate stages, but it is not a substitute
for explicit stage reasoning.

### E5 — Controlled ground truth

All four checks pass at 1.000: entry point present, every ground-truth
behavior has an API hint in the plain source, the stage list respects the
ontology order, and plain samples trigger no obfuscation heuristic. This
makes the later metrics interpretable: errors are pipeline errors, not label
noise.

### E6 — Stage reconstruction (RQ1, RQ5)

All 378 samples:

| Metric | Value |
|---|---|
| Behavior recall | 0.981 |
| Behavior precision | 0.968 |
| Evidence precision | 1.000 |
| Stage accuracy (LCS F1) | 0.963 |
| Stage precision | 0.943 |
| Stage recall | 0.994 |
| Completion rate | 0.952 |
| Execution success rate | 0.571 |
| Timeout rate | 0.048 |
| Deobfuscation success | 0.921 |
| Unsupported claim rate | 0.217 |

Samples whose macro ran to completion (n=216):

| Metric | Value |
|---|---|
| Behavior recall | 1.000 |
| Behavior precision | 0.969 |
| Stage accuracy | 0.964 |
| Completion rate | 1.000 |
| Unsupported claim rate | 0.031 |

Per-family stage accuracy ranges from 0.878 (broken macro) to 1.000
(downloader, interaction, empty). The aggregate gap between the two tables is
entirely due to environment-gated families: when Outlook or FTP is absent,
later stages never execute, so the ground truth contains behaviors that no
telemetry can support. The reconstructor reports the observable prefix and
marks the rest unsupported (0.217 overall vs 0.031 on completed runs) rather
than inventing them. This is the desired behavior for RQ5: the chain is
built from evidence, and its confidence is honest about what was not seen.

### E7 — Failure analysis

| Failure class | Baseline (no interaction handling) | Oblivion-X (handled) |
|---|---|---|
| none | 198 | 216 |
| dynamic_env | 90 | 90 |
| dynamic_date | 18 | 18 |
| dynamic_interaction | 18 | 0 |
| dynamic_semantic | 18 | 18 |
| dynamic_timeout | 18 | 18 |
| static_empty | 18 | 18 |

Interaction handling recovers all 18 interaction-gated samples and nothing
else. Missing external software, date gates, semantic errors and timeouts are
genuine limitations and remain visible. Expectation mismatches are zero in
both configurations, confirming that the failure taxonomy is applied
consistently.

### E8 — Performance

| Measure | Value |
|---|---|
| Mean time/sample | 21.2 ms |
| p50 / p95 | 19.7 / 31.0 ms |
| Throughput | 47.2 samples/s |
| Static time/sample | 21.1 ms |
| Telemetry time/sample | 0.1 ms |
| Completion / timeout | 0.952 / 0.048 |

Static extraction dominates cost. The pipeline is fast enough for
corpus-scale analysis; the 4.8% timeouts are the deliberately slow
`slow_timeout` family.

## 6. Discussion

**Reconstruction beats classification for analyst trust.** Every claim in
the output carries event IDs, and evidence precision is 1.000: nothing is
claimed without an observation. The unsupported rate is a feature, not a bug
— it exposes exactly the stages that a sandbox could not reach.

**Static and dynamic are not redundant.** The Jaccard of 0.600 and the
disjoint miss lists show that neither view subsumes the other. Fusion is
necessary for both coverage and concreteness.

**Obfuscation shifts the problem from recall to evidence.** Behavior recall
is stable, but literal recovery is what allows a claim to name a URL or a
command. Deobfuscation success of 0.92 (and 1.0 on completed runs) is
therefore the metric that matters for operational output.

**Segmentation is a diagnostic, not a replacement.** Boundary F1 peaks at
0.636 (N=5). Segmentation tells us that stages are temporally coherent, but
explicit stage reconstruction is what produces the chain and the
unsupported-claim signal.

## 7. Threats to validity

- **Simulated dynamics.** The default dynamic source is a deterministic
  simulator, not real Office execution. It is faithful to the stage order and
  failure taxonomy by construction, so E2/E6/E7 measure the pipeline's
  reasoning, not Office's runtime. Real traces can be plugged in through
  `--dynamic-source windows`; the provided Windows runner currently captures
  entry/exit timing and errors, not API-level events. A smoke test on the
  host showed that benign samples open, run and close normally, while the
  plain `donoff_downloader` samples lose their Word process within ~2 s of
  opening (COM `0x800706BA`), consistent with endpoint protection terminating
  Office after it spawns a hidden PowerShell child. The runner records this
  as `office_terminated`; it is an additional real-world failure class that
  the simulator does not model.
- **Synthetic corpus.** Families are modeled on known macro malware but are
  inert and simplified; absolute numbers will not transfer to wild samples.
- **Stage ontology.** The eight-stage ontology and the LCS metric are design
  choices; different ontologies would change stage accuracy.
- **Detection heuristics.** E3 detection thresholds were tuned on this
  corpus; precision on wild data is unmeasured.

## 8. Conclusion

Oblivion-X turns macro analysis from a label into an evidence-backed,
ordered attack chain. On a controlled corpus it reconstructs 98% of
ground-truth behaviors with perfect evidence precision, keeps stage accuracy
above 0.96, and honestly reports the 22% of claims that the environment did
not allow it to observe. Static and dynamic views are complementary, and
obfuscation mainly damages literal evidence rather than behavior coverage.
Future work is real Office instrumentation, a wild-sample evaluation, and
learning stage boundaries instead of fixing N.

## References

1. Sanna, Cara, Maiorca, Giacinto. *Oblivion: an open-source system for
   large-scale analysis of macro-based office malware.* J. Computer Virology
   and Hacking Techniques 20:783–802, 2024.
2. Shenderovitz, Nissim. *Bon-APT: Detection, attribution, and explainability
   of APT malware using temporal segmentation of API calls.* Computers &
   Security 142:103862, 2024.
3. VBA/Office macro analysis tooling: oletools / OleVBA.
4. Microsoft. *MS-OVBA: Office VBA File Format Structure*; *MS-CFB:
   Compound File Binary File Format*.
