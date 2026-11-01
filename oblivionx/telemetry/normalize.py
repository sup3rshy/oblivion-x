"""Telemetry normalization: convert raw analysis outputs into the common
Event schema.

Sources:
  * VBA instrumented trace log (our own instrumentation, Oblivion-style)
  * Oblivion report text (paper Appendix A format)
  * simulator traces (oblivionx.simulate)

Each parser maps source-specific lines into normalized events with
timestamps (dynamic) or without (static reports).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from oblivionx.common import BEHAVIOR_DEFS
from oblivionx.telemetry.schema import Event, SampleAnalysis

# ---------------------------------------------------------------------------
# VBA trace log (our instrumented macros)
# ---------------------------------------------------------------------------

def parse_vba_trace(text: str, sample_id: str, family: str = "",
                    variant: str = "") -> SampleAnalysis:
    """Parse the trace written by instrumented VBA:

    action<TAB>object<TAB>timerSeconds
    """
    sa = SampleAnalysis(sample_id=sample_id, family=family, variant=variant)
    eid = 0
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        action = parts[0] if parts else ""
        obj = parts[1] if len(parts) > 1 else ""
        t_sec = float(parts[2]) if len(parts) > 2 and parts[2] else None
        behavior = _map_action(action, obj)
        if behavior is None:
            continue
        eid += 1
        sa.add(Event(id=eid, t_ms=int(t_sec * 1000) if t_sec else None,
                     source="dynamic", behavior=behavior, obj=obj,
                     confidence=0.99, evidence=f"trace:{action}"))
    return sa


def _map_action(action: str, obj: str) -> Optional[str]:
    a = action.lower()
    m = {
        "shell": "shell_run",
        "createobject": "shell_run",
        "wscript.run": "shell_run",
        "powershell": "powershell_run",
        "cmd": "cmd_run",
        "http_open": "http_download",
        "http_send": "http_download",
        "url": "url_reference",
        "downloadfile": "http_download",
        "regwrite": "registry_write",
        "file_open_out": "file_write",
        "file_open_binary": "file_write",
        "file_print": "file_write",
        "file_close": "file_write",
        "shell_exec": "file_execute",
        "kill": "file_delete",
        "msgbox": "msgbox_gate",
        "inputbox": "msgbox_gate",
        "environ": "env_read",
        "outlook_createitem": "outlook_access",
        "outlook_send": "outlook_send",
        "savecopyas": "file_write",
        "saveas": "file_write",
        "printout": "print_document",
        "copy": "data_copy",
        "ftp": "ftp_upload",
        "xor_crypt": "file_encrypt",
        "macro_entry": "macro_entry",
        "window_hide": "window_hide",
    }
    behavior = m.get(a)
    if behavior is None and "powershell" in a:
        behavior = "powershell_run"
    return behavior


# ---------------------------------------------------------------------------
# Oblivion report text
# ---------------------------------------------------------------------------

def parse_oblivion_report(text: str, sample_id: str, family: str = "",
                          variant: str = "") -> SampleAnalysis:
    """Parse an Oblivion post-processing report (paper Appendix A)."""
    sa = SampleAnalysis(sample_id=sample_id, family=family, variant=variant)
    eid = 0

    def section(name: str) -> str:
        m = re.search(r"### " + name + r" ###\n(.*?)(?=###|\Z)",
                      text, re.S)
        return m.group(1).strip() if m else ""

    def add(behavior: str, obj: str, confidence: float = 0.95):
        nonlocal eid
        eid += 1
        sa.add(Event(id=eid, t_ms=None, source="dynamic",
                     behavior=behavior, obj=obj, confidence=confidence,
                     evidence="oblivion-report"))

    for line in section("Shell Actions").splitlines():
        if line.strip() and "Nothing Found" not in line:
            b = "powershell_run" if "powershell" in line.lower() else \
                "shell_run"
            add(b, line.strip())
    for line in section("Executable Files").splitlines():
        if line.strip() and "Nothing Found" not in line:
            add("file_execute", line.strip())
    for line in section("Domain Traces").splitlines():
        if line.strip() and "Nothing Found" not in line:
            add("url_reference", line.strip())
    for line in section("System File Writes").splitlines():
        if line.strip() and "Nothing Found" not in line:
            add("file_write", line.strip())
    for line in section("External Calls").splitlines():
        if line.strip() and "Nothing Found" not in line:
            add("shell_run", line.strip())
    for line in section("Auto Exec Methods").splitlines():
        if line.strip() and "Nothing Found" not in line:
            add("macro_entry", line.strip())
    for line in section("Environment Variables").splitlines():
        if line.strip() and "Nothing Found" not in line:
            add("env_read", line.strip())
    deob = section("Deobfuscated Powershell").strip()
    if deob and "clear" not in deob.lower() and "nothing" not in deob.lower():
        add("powershell_run", deob[:200])
    return sa


# ---------------------------------------------------------------------------
# Generic entry
# ---------------------------------------------------------------------------

def normalize(path: Path, source: str, sample_id: str, family: str = "",
              variant: str = "", meta: Optional[Dict[str, Any]] = None
              ) -> SampleAnalysis:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    if source == "vba_trace":
        sa = parse_vba_trace(text, sample_id, family, variant)
    elif source == "oblivion_report":
        sa = parse_oblivion_report(text, sample_id, family, variant)
    else:
        raise ValueError(f"unknown source: {source}")
    if meta:
        sa.meta.update(meta)
    return sa
