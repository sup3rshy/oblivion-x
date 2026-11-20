"""Stage reconstruction: turn normalized evidence into an attack chain.

Answers RQ1 (how many behaviors vs ground truth) and RQ5 (can the attack
chain be reconstructed from evidence instead of a label). The reconstructor
maps observed events to behaviors, groups them into attack stages (per the
stage ontology in common.py), links stages into an ordered chain, and marks
claims as supported/unsupported based on direct telemetry evidence.

The chain can be ordered two ways (``stage_order``):

  * ``"ontology"`` (default): the canonical STAGE_ORDER of the attack-stage
    ontology. Backwards-compatible with earlier results, but the order is
    then true by construction rather than observed.
  * ``"timestamp"``: stages are ordered by the first timestamp at which each
    stage was *observed*. Stages supported only by static evidence have no
    timestamp and are appended in ontology order. This variant answers RQ5
    without rooting for an answer: if the reconstructed chain matches the
    ground truth only because both use the same ontology, the two modes
    agree; if it matches under timestamp ordering too, the order itself was
    recovered from evidence.
"""
from __future__ import annotations

from typing import Dict, List, Literal

from oblivionx.common import BEHAVIOR_DEFS, STAGE_ORDER
from oblivionx.telemetry.schema import (
    BehaviorClaim,
    Event,
    Reconstruction,
    SampleAnalysis,
    StageClaim,
)

# minimum confidence for an event to count as evidence
_MIN_CONF = 0.5


StageOrder = Literal["ontology", "timestamp"]


def reconstruct(sa: SampleAnalysis,
                stage_order: StageOrder = "ontology") -> Reconstruction:
    rec = Reconstruction(sample_id=sa.sample_id)

    # behavior claims: dedupe events by behavior, keep supporting evidence
    by_behavior: Dict[str, List[Event]] = {}
    for e in sa.events:
        if e.confidence >= _MIN_CONF:
            by_behavior.setdefault(e.behavior, []).append(e)

    for behavior, evs in by_behavior.items():
        if behavior not in BEHAVIOR_DEFS:
            rec.behaviors.append(BehaviorClaim(
                behavior=behavior, evidence=[e.id for e in evs],
                confidence=max(e.confidence for e in evs),
                supported=False,
                obj=evs[0].obj))
            continue
        dyn = [e for e in evs if e.source == "dynamic"]
        ev = dyn or evs
        best = max(ev, key=lambda x: x.confidence)
        rec.behaviors.append(BehaviorClaim(
            behavior=behavior,
            evidence=[e.id for e in ev],
            confidence=max(e.confidence for e in ev),
            supported=bool(dyn),
            obj=best.obj))

    # stage claims: behaviors grouped by their stage
    events_by_id: Dict[int, Event] = {e.id: e for e in sa.events}
    stages: Dict[str, StageClaim] = {}
    for claim in rec.behaviors:
        bdef = BEHAVIOR_DEFS.get(claim.behavior)
        if bdef is None:
            continue
        stage = bdef.stage
        if stage is None:
            continue
        if stage not in stages:
            stages[stage] = StageClaim(stage=stage)
        stages[stage].evidence.extend(claim.evidence)
        stages[stage].confidence = max(stages[stage].confidence,
                                       claim.confidence)

    # first observed timestamp per stage (dynamic evidence only)
    for stage_claim in stages.values():
        seen = [events_by_id[i].t_ms for i in stage_claim.evidence
                if i in events_by_id
                and events_by_id[i].t_ms is not None]
        stage_claim.first_seen_ms = min(seen) if seen else None

    rec.stages = _order_stages(stages, stage_order)

    # ordered chain
    rec.chain = " -> ".join(s.stage for s in rec.stages)

    # status: partial if failure flags present
    if sa.meta.get("failure"):
        rec.status = "partial"
    elif not rec.stages and not rec.behaviors:
        rec.status = "failed"
    return rec


def _order_stages(stages: Dict[str, StageClaim],
                  stage_order: StageOrder) -> List[StageClaim]:
    """Order stage claims by the ontology or by observed timestamps."""
    if stage_order == "timestamp":
        # Observed stages by first timestamp; static-only stages (no
        # timestamp) keep their ontology order and follow the observed ones.
        observed = sorted((s for s in stages.values()
                           if s.first_seen_ms is not None),
                          key=lambda s: (s.first_seen_ms,
                                         STAGE_ORDER.index(s.stage)))
        static_only = [stages[s] for s in STAGE_ORDER
                       if s in stages
                       and stages[s].first_seen_ms is None]
        return observed + static_only
    if stage_order != "ontology":
        raise ValueError(f"unknown stage_order: {stage_order!r}")
    return [stages[s] for s in STAGE_ORDER if s in stages]
