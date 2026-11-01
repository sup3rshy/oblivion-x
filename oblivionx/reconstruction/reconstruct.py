"""Stage reconstruction: turn normalized evidence into an attack chain.

Answers RQ1 (how many behaviors vs ground truth) and RQ5 (can the attack
chain be reconstructed from evidence instead of a label). The reconstructor
maps observed events to behaviors, groups them into attack stages (per the
stage ontology in common.py), links stages into an ordered chain, and marks
claims as supported/unsupported based on direct telemetry evidence.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from oblivionx.common import BEHAVIOR_DEFS, STAGE_ORDER, stage_index
from oblivionx.telemetry.schema import (BehaviorClaim, Event, Reconstruction,
                                        SampleAnalysis, StageClaim)

# minimum confidence for an event to count as evidence
_MIN_CONF = 0.5


def reconstruct(sa: SampleAnalysis) -> Reconstruction:
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
    stages: Dict[str, StageClaim] = {}
    for claim in rec.behaviors:
        stage = BEHAVIOR_DEFS[claim.behavior].stage
        if stage is None:
            continue
        if stage not in stages:
            stages[stage] = StageClaim(stage=stage)
        stages[stage].evidence.extend(claim.evidence)
        stages[stage].confidence = max(stages[stage].confidence,
                                       claim.confidence)
    rec.stages = [stages[s] for s in STAGE_ORDER if s in stages]

    # ordered chain
    rec.chain = " -> ".join(s.stage for s in rec.stages)

    # status: partial if failure flags present
    if sa.meta.get("failure"):
        rec.status = "partial"
    elif not rec.stages and not rec.behaviors:
        rec.status = "failed"
    return rec
