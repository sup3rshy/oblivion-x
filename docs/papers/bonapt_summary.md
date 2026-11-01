# Bon-APT — paper summary (baseline paper)

> Shenderovitz, Nissim. *Bon-APT: Detection, attribution, and explainability
> of APT malware using temporal segmentation of API calls.* Computers &
> Security 142 (2024) 103862. doi:10.1016/j.cose.2024.103862

## Problem
- APTs are nation-backed, long-running, heavily evasive campaigns. Classic
  static/dynamic detectors either miss them or return only a label.
- Existing work gives no *temporal* view of what the malware does, and no
  human-comprehensible explanation of why a sample was attributed to a
  group/nation.
- Scope: Windows `.exe` PE files, dynamic analysis in Cuckoo Sandbox,
  timestamped API-call traces.

## Core idea — temporal segmentation
1. Take the timestamped sequence of API calls (a Multivariate Time Series,
   MTSD).
2. Split the execution timeline into **N equal-length segments**.
3. Map every call to its segment by timestamp.
4. Aggregate per (feature, segment): here the **frequency** of each API call
   in the segment, i.e. `count(call, segment) / count(call, whole run)`.
5. Flatten to an `N × D` vector (or keep the 2-D matrix for sequence models).

N values studied: **1, 5, 10, 20**, plus the combinations `{1,5}`, `{1,10}`,
`{1,20}`. The best configuration is chosen per learning task. This is the
configuration sweep reproduced in Oblivion-X experiment E4.

## Detection / attribution
- The flattened segmentation vector feeds standard ML (random forest is the
  strong baseline; LSTM/XGBoost are compared).
- Tasks: APT vs non-APT detection, APT **group** attribution, APT **nation**
  attribution.
- Dataset: 12,655 APT samples, 188 groups, 17 nations (largest of its kind
  at publication).

## Explainability
- API calls are abstracted into ~10 behavioural categories (file, registry,
  network, process/thread, memory, ...).
- Per-segment category intensity is discretized into **low / medium / high**,
  producing a compact human-readable profile of how behaviour evolves.
- Because the representation is built from segments rather than model
  internals, explanations are *meta-explainable*: the same structure works at
  sample, family, group and nation granularity, and is independent of the
  classifier.

## What Oblivion-X takes from Bon-APT
- The segmentation definition (N equal time buckets, frequency aggregation,
  `N*D` flattening) is reimplemented in
  `oblivionx/telemetry/segmentation.py`.
- The N ∈ {1, 5, 10, 20} sweep and the low/medium/high explainability profile
  are reused.
- **Difference:** Bon-APT segments *API calls of PE files*; Oblivion-X
  segments *normalized VBA/Office telemetry* (behaviours, not raw Win32
  APIs), and uses the segments to test whether attack **stages** separate in
  time (E4/RQ3), not to train a detector.
- Bon-APT is used purely as the methodological baseline; no APT corpus is
  involved. Oblivion-X's corpus is a controlled, inert macro corpus with
  ground truth.
