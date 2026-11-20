# Oblivion-X: Behavior Reconstruction and Stage-Aware Analysis of Macro-Based Office Malware

> Draft. Numbers come from `outputs/eval/E1..E10*.json` on the 378-sample
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
ground truth we obtain behavior recall 0.990, evidence precision 1.000, stage
accuracy 0.963 (LCS F1) and completion 0.952. Static analysis alone recalls
0.905 of ground-truth behaviors and dynamic analysis 0.837, but their union is
complementary: static sees intent that gates never execute, dynamic sees
process effects absent from the source. Segmentation peaks at N=5 with
boundary F1 0.629, and stage separation is only modestly better than chance.
Re-ordering the reconstructed chain by observed evidence instead of by the
ontology costs 0.109 stage accuracy (0.854), which quantifies how much of the
headline is prior rather than observation. Finally, static evidence predicts
completion with AUC 0.669 out of family, but only for failure mechanisms
shared across families; unique mechanisms regress to the base rate. We
discuss failure classes and argue that stage reconstruction, and the honest
reporting of unobservable stages, not classification, should be the unit of
evaluation for macro malware.

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
   instead of hallucinating them. The reconstructor can order the chain by
   the ontology or by observed evidence; E9 measures the gap between the two
   so the reported accuracy is not merely the ontology restated.
4. An evaluation of ten experiments (E1–E10) with eight metrics, including a
   static-vs-dynamic observability study, an obfuscation study, a
   chain-ordering ablation, a calibration study of completion prediction,
   and a two-configuration failure analysis.

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
stages, stages ordered into a chain, and adjacent stages linked. Each claim
stores the supporting event IDs; claims without evidence are marked
unsupported. Stage accuracy is the F1 of the longest common subsequence
between the ground-truth and reconstructed stage sequences, so a missing
middle stage does not zero the rest of the chain.

The chain can be ordered two ways, and the difference matters for RQ5:

- **ontology order** — stages follow the fixed attack-stage ontology. This is
  the default and matches what analysts expect from the ontology, but a chain
  that agrees with ground truth is then true *by construction*.
- **evidence order** — stages are ordered by the first timestamp at which
  each stage was actually observed. Stages supported only by static evidence
  carry no timestamp and are appended after the observed ones. Agreement
  under this ordering is evidence that the chronology was recovered from
  observations, not assumed.

E9 reports both orderings on the same events (§5), so its delta isolates how
much of the chain accuracy is ontology prior and how much is observed order.

### 4.6 Predicting analysis completion

The unsupported-claim rate is only operationally useful if an analyst can
anticipate it. E10 tests that directly: a logistic model on static-only
features (behaviour indicators, deobfuscation flags, source length, date-gate
and busy-loop patterns; never the family, variant or format) predicts
`execution_success`, i.e. whether the macro ran without an environment, date
or interaction gate. Evaluation is leave-one-family-out, so each family is
predicted by a model trained on the others; the in-sample score is reported
only as a reference for how much family composition the model would
otherwise memorise. Probabilities are scored with AUC, the Brier score
against a base-rate baseline, and expected calibration error over ten
equal-width bins.

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
| Mean static behavior recall | 0.905 |
| Mean dynamic behavior recall | 0.837 |
| Mean view agreement (Jaccard) | 0.643 |

Ground-truth behaviors seen by only one view:

| Behavior | Static only | Dynamic only |
|---|---|---|
| file_write | 10 | 54 |
| outlook_send | 54 | 0 |
| file_execute | 0 | 36 |
| file_delete | 18 | 0 |
| chr_encode | 18 | 0 |
| base64_encode | 18 | 0 |
| shell_run | 18 | 0 |
| dead_code | 18 | 0 |
| cmd_run | 17 | 0 |
| string_concat | 3 | 11 |
| env_read | 8 | 0 |
| url_reference | 0 | 6 |

Static analysis sees **intent**: URL literals, `Outlook.Send`, `Shell` and
`cmd` strings exist in the source even when an environment or date gate
prevents execution. Dynamic analysis sees **effects**: `file_write` and
`file_execute` performed by a spawned PowerShell process never appear in the
VBA source. The two views are therefore complementary, and a reconstruction
that fuses them is strictly better than either alone. The low Jaccard (0.643)
quantifies how different the two views are.

### E3 — Obfuscation vs observability (RQ4)

| Variant | Static recall | Dynamic recall | Detection precision | Detection recall | Deobf. success |
|---|---|---|---|---|---|
| plain | 0.918 | 0.862 | n/a | n/a | n/a |
| random | 0.899 | 0.854 | 1.000 | 0.900 | n/a |
| split | 0.887 | 0.834 | 1.000 | 0.900 | 0.900 |
| encode | 0.926 | 0.817 | 1.000 | 1.000 | 1.000 |
| logic | 0.923 | 0.835 | 1.000 | 1.000 | n/a |
| combo | 0.879 | 0.818 | 1.000 | 0.892 | 1.000 |

Two findings are worth stressing. First, **behavior-level recall is almost
insensitive to obfuscation** (0.879–0.926) because the analyzer reasons over
the obfuscated source directly; what obfuscation destroys is *literal*
visibility (URLs, API names), which is why deobfuscation is needed to
reconstruct concrete evidence. Second, the detector never fires on a plain
sample (precision 1.0), and deobfuscation recovers the hidden literal in
90–100% of recoverable variants. The few detection misses are short macros
where the transform had little material to rewrite.

### E4 — Temporal segmentation (RQ3)

| N | Segment purity | Stage concentration | Boundary F1 | Precision | Recall | Pk | WindowDiff |
|---|---|---|---|---|---|---|---|
| 1 | 0.393 | 1.000 | 0.000 | 0.000 | 0.000 | 0.870 | 0.643 |
| 5 | 0.815 | 0.842 | **0.629** | 0.845 | 0.525 | 0.299 | 0.291 |
| 10 | 0.922 | 0.793 | 0.505 | 0.783 | 0.395 | 0.133 | 0.151 |
| 20 | 0.962 | 0.760 | 0.290 | 0.587 | 0.201 | 0.053 | 0.079 |

Purity increases monotonically with N, but boundary F1 peaks at N=5 and then
falls: too many segments fragment a stage into several buckets and create
spurious boundaries. Bon-APT's multi-scale configuration is therefore
justified, but the informative scale for macro behavior is coarse (N=5), not
fine. The reference text-segmentation measures tell a complementary story:
Pk and WindowDiff keep improving as N grows, because window-based measures
reward finer approximations of the true boundary positions even when whole
stages no longer fit inside one bucket. A fixed N is thus a trade-off between
"a stage is one segment" (boundary F1) and "boundaries are where the truth
has them" (Pk/WindowDiff), not an optimum.

Two controls guard the conclusion:

- **Change-point estimation.** A greedy likelihood search with a BIC-style
  penalty estimates the number of segments per sample *without seeing the
  ground truth*: mean estimate 2.70 vs mean ground-truth 3.35 stages, exact
  agreement 0.156, mean absolute error 1.79. The segment count can partly be
  found rather than swept, but a fixed N=5 is a better choice than the
  unsupervised estimate on this corpus.
- **Permutation null.** Shuffling the label sequence breaks the temporal
  order while preserving a bucket's label multiset. Observed bucket purity
  (0.744) exceeds the shuffled mean (0.681) with mean z = 0.91, and no sample
  reaches p < 0.01. Stage separation at this scale is therefore real but
  modest: most of the bucket purity is explained by the small label alphabet
  and short traces, not by strong temporal structure. This tempers the
  boundary-F1 headline and is the honest reading of RQ3.

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
| Behavior recall | 0.990 |
| Behavior precision | 0.968 |
| Evidence precision | 1.000 |
| Stage accuracy (LCS F1) | 0.963 |
| Stage precision | 0.943 |
| Stage recall | 0.994 |
| Completion rate | 0.952 |
| Execution success rate | 0.571 |
| Timeout rate | 0.048 |
| Deobfuscation success | 0.967 |
| Unsupported claim rate | 0.151 |

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
marks the rest unsupported (0.151 overall vs 0.031 on completed runs) rather
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
| Mean time/sample | 2.4 ms |
| p50 / p95 | 2.3 / 3.7 ms |
| Throughput | 409.7 samples/s |
| Static time/sample | 2.4 ms |
| Telemetry time/sample | 0.1 ms |
| Completion / timeout | 0.952 / 0.048 |

Static extraction dominates cost. The pipeline is fast enough for
corpus-scale analysis; the 4.8% timeouts are the deliberately slow
`slow_timeout` family. These timings are measured on a warm filesystem cache
(a cold-cache run of the same corpus measured ~21 ms/sample), so they bound
the analysis logic rather than the storage path.

### E9 — Chain-order ablation: ontology vs evidence (RQ5)

The same events are reconstructed twice: once ordered by the attack-stage
ontology (the default) and once ordered by the first timestamp at which each
stage was observed.

| Ordering | Stage accuracy (LCS F1) | Precision | Recall | Exact-match rate |
|---|---|---|---|---|
| ontology | 0.963 | 0.943 | 0.994 | 0.746 |
| evidence (first observation) | 0.854 | 0.836 | 0.882 | 0.508 |

The two orderings disagree on 161/378 samples (delta −0.109). Two readings
follow.

First, a chain accuracy of 0.963 under ontology order is partly true by
construction: the ground-truth stages are projected from ground-truth
behaviors onto the same ontology, so ordering by `STAGE_ORDER` can only be
wrong when a stage is missing. The evidence-ordered number, 0.854 accuracy
and a 0.508 exact-match rate, is the one that shows the chronological chain
is recovered from observation. It is lower, as it must be, and it is the
defensible claim.

Second, the residual disagreements are diagnostic rather than noise. In most
of them the reconstructed *stage set* differs from ground truth only because
deobfuscation recovers a URL literal (`url_reference`) from a blob in a
family that never fetches it; the static claim creates a `c2_download` stage
with no timestamp. Under ontology order the phantom stage is silently slotted
into its canonical position and inflates the score; under evidence order it
is visible as an untimed stage. That is the correct treatment: static
evidence is *intent*, and intent is not an observed event. E9 therefore turns
an assumption in the reconstructor into a measurable quantity and shows that
roughly 11 points of stage accuracy in E6 come from the ontology prior, not
from observed ordering.

### E10 — Predicting analysis completion (extension)

Static-only features predict whether a macro runs to completion, evaluated
leave-one-family-out. Ten static features reach AUC 0.669 out of family,
against 1.000 in sample; the gap is family composition the model would
memorise if the family were an input.

| Measure | Value |
|---|---|
| Samples | 378 |
| Base rate (completed) | 0.571 |
| AUC (leave-one-family-out) | 0.669 |
| AUC, in-sample (reference) | 1.000 |
| Brier | 0.242 |
| Brier baseline | 0.245 |
| Brier skill | 0.014 |
| ECE (10 bins) | 0.234 |

Reliability is poor in the high-probability region: the 0.9–1.0 bin contains
194 samples with mean predicted 0.984 but an observed completion rate of
0.727, while the 0.8–0.9 bin is worse still (0.856 predicted, 0.364
observed). Partitioning by failure mechanism explains why:

| Mechanism | n | Families | Observed completed | Mean predicted |
|---|---|---|---|---|
| none (completed) | 216 | 7 | 1.000 | 0.844 |
| dynamic_env | 90 | 3 | 0.000 | 0.451 |
| dynamic_date | 18 | 1 | 0.000 | 0.892 |
| dynamic_timeout | 18 | 1 | 0.000 | 0.827 |
| dynamic_semantic | 18 | 1 | 0.000 | 0.765 |
| static_empty | 18 | 1 | 0.000 | 0.033 |

Empty projects are predicted almost perfectly (0.033) because the absence of
behaviours is itself a static signal. Outlook-gated families are predicted
low *when another family also references Outlook*: with `metacol_mailer`
held out, `valyria_dual` supplies the signal, and vice versa (per-family
predictions 0.014 and 0.121). FTP upload, the date gate, the busy loop and
the runtime semantic error each occur in exactly one family, so holding that
family out removes the feature from training and the fold regresses to the
base rate or to unrelated proxy features.

The operational conclusion is deliberately negative: an analyst cannot
reliably anticipate the unsupported-claim rate from static evidence alone
across unseen families. That is the argument for measuring and reporting
unobservability, rather than estimating it before execution.

## 6. Discussion

**Reconstruction beats classification for analyst trust.** Every claim in
the output carries event IDs, and evidence precision is 1.000: nothing is
claimed without an observation. The unsupported rate is a feature, not a bug
— it exposes exactly the stages that a sandbox could not reach.

**Static and dynamic are not redundant.** The Jaccard of 0.643 and the
disjoint miss lists show that neither view subsumes the other. Fusion is
necessary for both coverage and concreteness.

**Obfuscation shifts the problem from recall to evidence.** Behavior recall
is stable, but literal recovery is what allows a claim to name a URL or a
command. Deobfuscation success of 0.97 (and 1.0 on completed runs) is
therefore the metric that matters for operational output.

**Segmentation is a diagnostic, not a replacement.** Boundary F1 peaks at
0.629 (N=5), and the permutation null puts the separation only ~1 standard
deviation above shuffled order. Segmentation tells us that stages are
temporally coherent but weakly separated, and explicit stage reconstruction
is what produces the chain and the unsupported-claim signal.

**Chain accuracy has two components.** Under ontology ordering the E6 chain
scores 0.963; ordered by observed evidence it scores 0.854 (E9). The 0.109
difference is the share of the reported accuracy that comes from the
ontology prior rather than from observed chronology. Both numbers belong in
the paper: the first is comparable with ontology-driven systems, the second
is the defensible answer to RQ5.

**Unobservability is measured, not predicted.** Completion prediction from
static evidence generalises only for failure mechanisms that recur across
families (AUC 0.669 out of family; Outlook gates and empty projects are
anticipated, unique gates are not). An analyst therefore cannot estimate the
unsupported-claim rate in advance; the pipeline has to observe it. This is
the strongest argument for reporting missing stages explicitly instead of
collapsing the analysis into a label.

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
- **Completion calibration.** E10 uses one linear model and ten hand-picked
  static features; a richer model or a corpus with more families per failure
  mechanism would change the AUC and ECE. The qualitative split — shared
  mechanisms generalise, unique ones do not — follows from
  leave-one-family-out by construction and is the part we rely on.

## 8. Conclusion

Oblivion-X turns macro analysis from a label into an evidence-backed,
ordered attack chain. On a controlled corpus it reconstructs 99% of
ground-truth behaviors with perfect evidence precision, keeps stage accuracy
above 0.96 under ontology ordering and 0.85 when the chain is ordered by
observed evidence alone, and honestly reports the 15% of claims that the
environment did not allow it to observe. Static and dynamic views are
complementary, obfuscation mainly damages literal evidence rather than
behavior coverage, temporal segmentation separates stages only modestly
above chance, and completion is not reliably anticipable from static
evidence across families. Future work is real Office instrumentation, a
wild-sample evaluation, and learning stage boundaries from evidence instead
of fixing N.

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
