"""Deterministic dynamic-telemetry simulator.

Produces realistic timestamped event traces for corpus samples on Linux,
enabling end-to-end evaluation (E2-E8) without a Windows VM. The real
dynamic pipeline (instrumented macros executed in Office) produces traces
in the same schema via oblivionx.telemetry.normalize.

The simulator models:
  * the family's ground-truth stage sequence with realistic timings
  * benign startup noise (template loads, registry reads, ...)
  * failure modes: semantic errors, environment dependencies, date gates,
    interaction gates and timeouts (per the ground-truth spec)
"""
from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from oblivionx.common import BEHAVIOR_DEFS, STAGE_ORDER
from oblivionx.telemetry.schema import Event, SampleAnalysis

# stage -> typical behaviors ordering helper
_NOISE_POOL = ["file_write", "env_read", "registry_write"]


def _stable_seed(text: str) -> int:
    """Process-independent seed (``hash()`` is salted per interpreter)."""
    import hashlib
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:4], "big")


def _env_now(date_hint: Optional[Any] = None):
    """The simulator's notion of 'today' (injectable for date gates)."""
    import datetime
    if date_hint is not None:
        return date_hint
    return datetime.date.today()


def simulate_sample(sample_id: str, ground_truth: Dict[str, Any],
                    family: str, variant: str, fmt: str,
                    *, interaction_handled: bool = True,
                    env_available: Optional[Dict[str, bool]] = None,
                    date_now: Optional[Any] = None,
                    timeout_ms: int = 120000,
                    rng: Optional[random.Random] = None) -> SampleAnalysis:
    """Simulate the dynamic analysis of one sample."""
    rng = rng or random.Random(0x0B1F17E ^ _stable_seed(sample_id))
    gt = ground_truth
    sa = SampleAnalysis(sample_id=sample_id, family=family, variant=variant,
                        format=fmt)
    env_available = env_available or {}
    sa.meta["simulated"] = True
    sa.meta["failure"] = None
    sa.meta["interaction_handled"] = interaction_handled
    eid = 0
    t = rng.randint(120, 500)   # office startup

    def add(behavior: str, obj: str = "", dt: int = 0, conf: float = 0.99):
        nonlocal eid, t
        t += dt
        if t > timeout_ms:
            sa.meta["failure"] = "dynamic_timeout"
            return False
        eid += 1
        sa.add(Event(id=eid, t_ms=t, source="dynamic", behavior=behavior,
                     obj=obj, confidence=conf, evidence="sim"))
        return True

    # ---- benign startup noise -------------------------------------------
    # Low confidence: below the reconstruction threshold (_MIN_CONF=0.5),
    # so noise never becomes a behavior claim.
    for _ in range(rng.randint(2, 4)):
        add(rng.choice(_NOISE_POOL), "startup-noise",
            dt=rng.randint(20, 200), conf=0.3)

    # ---- failure modes -----------------------------------------------------
    expected = gt.get("expected_failure")
    if expected == "dynamic_semantic":
        add("macro_entry", "Document_Open", dt=300)
        sa.meta["failure"] = "dynamic_semantic"
        sa.meta["error_detail"] = "Sub or Function not defined"
        return sa
    if expected == "static_empty":
        sa.meta["failure"] = "static_empty"
        return sa

    # ---- stage-by-stage behavior replay -------------------------------------
    add("macro_entry", "Document_Open", dt=rng.randint(200, 500))
    stages = gt.get("stages", [])
    behaviors = gt.get("behaviors", [])

    if expected == "dynamic_timeout":
        # The busy loop never returns: only the entry point is observed.
        sa.meta["failure"] = "dynamic_timeout"
        sa.meta["note"] = "busy loop exceeded analysis time limit"
        sa.meta["duration_ms"] = timeout_ms
        return sa

    if gt.get("date_trigger") and not (date_now is not None
                                       and date_now.month == 12
                                       and date_now.day == 13):
        sa.meta["failure"] = "dynamic_date"
        sa.meta["note"] = "payload gated by date; only entry observed"
        return sa

    if gt.get("interaction") and not interaction_handled:
        add("msgbox_gate", "Enable content?", dt=rng.randint(300, 800))
        sa.meta["failure"] = "dynamic_interaction"
        sa.meta["note"] = "execution gated behind MsgBox; not handled"
        return sa

    if gt.get("interaction"):
        add("msgbox_gate", "Enable content?", dt=rng.randint(300, 800))

    # obfuscation behaviors fire during execution (variable building)
    for b in ("string_concat", "chr_encode", "base64_encode", "dead_code"):
        if b in behaviors and b in BEHAVIOR_DEFS:
            add(b, BEHAVIOR_DEFS[b].description, dt=rng.randint(50, 300))

    # per-stage behaviors, in stage order
    env_dep = gt.get("env_dep")
    if env_dep and not env_available.get(env_dep, True):
        # The macro attempts to use the missing dependency, then fails.
        attempt = "outlook_access" if env_dep == "outlook" else "ftp_upload"
        if attempt in BEHAVIOR_DEFS:
            add(attempt, _sim_obj(attempt, family), dt=rng.randint(200, 600))
        sa.meta["failure"] = "dynamic_env"
        sa.meta["note"] = f"missing environment dependency: {env_dep}"
        sa.meta["missing_dependency"] = env_dep
        return sa

    stage_behaviors: Dict[str, List[str]] = {}
    for b in behaviors:
        st = BEHAVIOR_DEFS[b].stage
        if st is not None:
            stage_behaviors.setdefault(st, []).append(b)

    for stage in STAGE_ORDER:
        if stage not in stages:
            continue
        for b in stage_behaviors.get(stage, []):
            if b in ("string_concat", "chr_encode", "base64_encode",
                     "dead_code", "macro_entry", "msgbox_gate"):
                continue
            if not add(b, _sim_obj(b, family), dt=rng.randint(200, 1200)):
                return sa

    # benign, stage-less behaviors (formatting, printing, PDF export) are
    # executed at the end of the macro, after the stage replay.
    for b in behaviors:
        if BEHAVIOR_DEFS[b].stage is not None:
            continue
        if b in ("string_concat", "chr_encode", "base64_encode", "dead_code"):
            continue
        add(b, _sim_obj(b, family), dt=rng.randint(150, 600))

    # family-specific artifacts: URLs, payload paths, etc.
    for b in ("url_reference", "file_execute", "outlook_send", "ftp_upload"):
        if b in behaviors:
            add(b, _sim_obj(b, family), dt=rng.randint(400, 1500))

    sa.meta["duration_ms"] = t
    return sa


def _sim_obj(behavior: str, family: str) -> str:
    objs = {
        "shell_run": "powershell.exe -NoProfile -WindowStyle Hidden ...",
        "powershell_run": "powershell.exe -NoProfile -WindowStyle Hidden "
                          "-ExecutionPolicy Bypass -Command ...",
        "cmd_run": "cmd /c ...",
        "http_download": "http://127.0.0.1:9090/payload.exe",
        "url_reference": "http://127.0.0.1:9090/payload.exe",
        "file_write": "%TEMP%\\oblivionx_payload.exe",
        "file_execute": "%TEMP%\\oblivionx_payload.exe",
        "registry_write": "HKCU\\...\\Run\\oblivionx",
        "file_encrypt": "xor-crypt(%TEMP%\\oblivionx_vault\\secret.txt)",
        "file_delete": "Kill %TEMP%\\oblivionx_wipe_test\\*.*",
        "outlook_send": "outlook MailItem.Send",
        "ftp_upload": "ftp -s:... put oblivionx_log.txt",
        "office_template_infect": "SaveCopyAs XLSTART\\oblivionx_infected.xlsm",
        "env_read": "Environ(TEMP/APPDATA)",
    }
    return objs.get(behavior, f"{family}:{behavior}")
