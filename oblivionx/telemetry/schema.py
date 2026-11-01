"""Normalized telemetry schema for Oblivion-X.

Every observation produced by any pipeline (static extraction, dynamic
instrumentation traces, Oblivion reports, simulator) is normalized into an
EVENT with a common schema, so temporal segmentation, reconstruction and
evaluation are source-agnostic.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Event schema
# ---------------------------------------------------------------------------
# {
#   "id": 17,                    # per-sample monotonic event id
#   "t_ms": 12345,               # time since analysis start (ms); null=static
#   "source": "dynamic",         # static | dynamic
#   "behavior": "shell_run",     # behavior id from common.BEHAVIOR_DEFS
#   "obj": "powershell.exe ...", # observed object / argument string
#   "args": {...},               # structured arguments
#   "confidence": 0.9,           # 0..1
#   "evidence": "vba#12"         # source artifact reference (optional)
# }
# ---------------------------------------------------------------------------

@dataclass
class Event:
    id: int
    t_ms: Optional[int]
    source: str
    behavior: str
    obj: str = ""
    args: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    evidence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Event":
        return Event(**{k: d.get(k, Event.__dataclass_fields__[k].default)
                        for k in Event.__dataclass_fields__})


@dataclass
class SampleAnalysis:
    """All normalized observations for one sample."""
    sample_id: str
    format: str = ""                    # docm / xlsm
    family: str = ""
    variant: str = ""
    events: List[Event] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def add(self, e: Event) -> None:
        if e.id == 0:
            e.id = len(self.events) + 1
        self.events.append(e)

    def dynamic_events(self) -> List[Event]:
        return [e for e in self.events if e.source == "dynamic"]

    def static_events(self) -> List[Event]:
        return [e for e in self.events if e.source == "static"]

    def behaviors(self, source: Optional[str] = None) -> List[str]:
        evs = self.events if source is None else \
            [e for e in self.events if e.source == source]
        seen, out = set(), []
        for e in evs:
            if e.behavior not in seen:
                seen.add(e.behavior)
                out.append(e.behavior)
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "format": self.format,
            "family": self.family,
            "variant": self.variant,
            "events": [e.to_dict() for e in self.events],
            "meta": self.meta,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "SampleAnalysis":
        sa = SampleAnalysis(d["sample_id"], d.get("format", ""),
                            d.get("family", ""), d.get("variant", ""))
        sa.events = [Event.from_dict(x) for x in d.get("events", [])]
        sa.meta = d.get("meta", {})
        return sa


# ---------------------------------------------------------------------------
# Reconstruction result schema (output of reconstruction module)
# ---------------------------------------------------------------------------
@dataclass
class StageClaim:
    stage: str
    evidence: List[int] = field(default_factory=list)   # event ids
    confidence: float = 0.0
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BehaviorClaim:
    behavior: str
    evidence: List[int] = field(default_factory=list)
    confidence: float = 0.0
    supported: bool = True          # has direct telemetry evidence
    obj: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Reconstruction:
    sample_id: str
    stages: List[StageClaim] = field(default_factory=list)
    behaviors: List[BehaviorClaim] = field(default_factory=list)
    chain: str = ""                 # "delivery -> execution -> impact"
    status: str = "ok"              # ok | partial | failed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "stages": [s.to_dict() for s in self.stages],
            "behaviors": [b.to_dict() for b in self.behaviors],
            "chain": self.chain,
            "status": self.status,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Reconstruction":
        r = Reconstruction(d["sample_id"], chain=d.get("chain", ""),
                           status=d.get("status", "ok"))
        r.stages = [StageClaim(**{k: s.get(k) for k in
                      StageClaim.__dataclass_fields__}) for s in d.get("stages", [])]
        r.behaviors = [BehaviorClaim(**{k: b.get(k) for k in
                       BehaviorClaim.__dataclass_fields__})
                       for b in d.get("behaviors", [])]
        return r
