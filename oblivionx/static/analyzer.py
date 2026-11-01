"""Static analyzer: turn extracted VBA source into normalized EVENTS.

The static pipeline only sees what is visible WITHOUT execution. Obfuscated
samples hide most indicators; the deobfuscator recovers the rest. Output is
the same Event schema used by the dynamic side, enabling the static vs
dynamic comparison (E2 / RQ2).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from oblivionx.common import BEHAVIOR_DEFS
from oblivionx.static.deobfuscator import (detect_obfuscation,
                                           recover_payloads)
from oblivionx.static.extractor import extract_modules, all_sources
from oblivionx.telemetry.schema import Event, SampleAnalysis

# indicator -> (behavior, regex) for static scanning
_STATIC_RULES = [
    ("macro_entry", re.compile(r"Sub\s+(AutoOpen|Auto_Open|Workbook_Open|"
                               r"Document_Open|AutoExec|Document_New)\b", re.I)),
    # A shell *call*: a bare CreateObject("WScript.Shell") is not enough.
    ("shell_run", re.compile(r"\bShell\s+[\"'\w]|\.Run\s+[\"'\w]|"
                             r"ShellExecute", re.I)),
    ("powershell_run", re.compile(r"powershell|PowerShell\.exe|"
                                  r"EncodedCommand|ExecutionPolicy", re.I)),
    ("cmd_run", re.compile(r"cmd\.exe|cmd\s+/c|%COMSPEC%", re.I)),
    ("http_download", re.compile(r"XMLHTTP|DownloadFile|URLDownloadToFile|"
                                 r"OpenURL|WinHttpRequest", re.I)),
    ("url_reference", re.compile(r"https?://[^\s\"']+|ftp://[^\s\"']+", re.I)),
    ("registry_write", re.compile(r"RegWrite|reg\s+add|HKCU|HKLM|"
                                  r"HKEY_CURRENT_USER|CurrentVersion\\\\Run", re.I)),
    ("startup_write", re.compile(r"XLSTART|\\\\STARTUP", re.I)),
    ("office_template_infect", re.compile(r"Normal\.dotm|NormalTemplate|"
                                          r"XLSTART|SaveCopyAs|VBComponents",
                                          re.I)),
    ("outlook_access", re.compile(r"Outlook\.Application|MailItem|"
                                  r"Outlook\.Session", re.I)),
    ("outlook_send", re.compile(r"\.Send\b|Recipients\.Add|\.Body\s*=", re.I)),
    ("ftp_upload", re.compile(r"\bftp\b|FtpPutFile|InternetConnect", re.I)),
    ("file_write", re.compile(r"\bOpen\s+\S+\s+For|CreateTextFile|"
                              r"SaveCopyAs|SaveAs2?|WriteLine|Print\s+#", re.I)),
    ("file_execute", re.compile(r"Invoke-Item|Start-Process|\.Run\s+\w+,\s*0",
                                re.I)),
    ("file_encrypt", re.compile(r"\bEncrypt\b|Rijndael|\bAES\b|\bCrypt\b|"
                                r"\bXor\b", re.I)),
    ("file_delete", re.compile(r"\bKill\b|DeleteFile|Remove-Item", re.I)),
    ("vbom_security_disable", re.compile(r"AccessVBOM|Application\.VBE|"
                                         r"VBAWarnings", re.I)),
    ("window_hide", re.compile(r"vbHide|-WindowStyle Hidden|-w\s+Hidden", re.I)),
    ("msgbox_gate", re.compile(r"\bMsgBox\b|\bInputBox\b", re.I)),
    ("env_read", re.compile(r"\bEnviron\s*\(", re.I)),
    ("code_delete", re.compile(r"DeleteLines|CodeModule", re.I)),
    ("save_as_pdf", re.compile(r"ExportAsFixedFormat|xlTypePDF", re.I)),
    ("print_document", re.compile(r"PrintOut|\.Print\b", re.I)),
    ("data_copy", re.compile(r"\.Copy\b|PasteSpecial|\.Range\s*\(", re.I)),
]


def analyze_static(path: Path, sample_id: str,
                   family: str = "", variant: str = "",
                   fmt: str = "") -> SampleAnalysis:
    """Run the static pipeline on one file and return normalized events."""
    modules = extract_modules(Path(path))
    src = all_sources(modules)
    sa = SampleAnalysis(sample_id=sample_id, family=family, variant=variant,
                        format=fmt)
    sa.meta = {
        "n_modules": len(modules),
        "modules": [m["name"] for m in modules],
        "obfuscation_detected": {},
        "recovered_payloads": [],
        "status": "ok",
    }

    # obfuscation detection
    sa.meta["obfuscation_detected"] = detect_obfuscation(src)

    # behavior indicators (on original source)
    eid = 0
    for behavior, rx in _STATIC_RULES:
        for m in rx.finditer(src):
            if behavior == "url_reference" and not _safe_url(m.group(0)):
                continue
            eid += 1
            sa.add(Event(id=eid, t_ms=None, source="static",
                         behavior=behavior, obj=m.group(0)[:200],
                         confidence=0.85,
                         evidence=f"static:{behavior}"))

    # recovered payloads (deobfuscation) -> behaviors on the RECOVERED text
    recovered = recover_payloads(src)
    sa.meta["recovered_payloads"] = recovered
    for text in recovered:
        for behavior, rx in _STATIC_RULES:
            if behavior in ("string_concat", "chr_encode", "base64_encode"):
                continue
            for m in rx.finditer(text):
                eid += 1
                sa.add(Event(id=eid, t_ms=None, source="static",
                             behavior=behavior, obj=m.group(0)[:200],
                             confidence=0.9,
                             evidence="static:recovered"))

    # obfuscation behaviors themselves are static-observable
    flags = sa.meta["obfuscation_detected"]
    for technique, behavior in [("split", "string_concat"),
                                ("encode", "chr_encode"),
                                ("logic", "dead_code")]:
        if flags.get(technique):
            eid += 1
            sa.add(Event(id=eid, t_ms=None, source="static",
                         behavior=behavior, obj=technique, confidence=0.95))
    if flags.get("encode") and re.search(r"[A-Za-z0-9+/]{40,}={0,2}", src):
        eid += 1
        sa.add(Event(id=eid, t_ms=None, source="static",
                     behavior="base64_encode", obj="base64-blob",
                     confidence=0.95))

    # deobfuscation success flag (for the metric)
    sa.meta["deobfuscation_applied"] = bool(recovered)
    sa.meta["behavior_count"] = len(sa.events)
    return sa


def _safe_url(url: str) -> bool:
    """Only record non-malicious-looking reference URLs (simulated)."""
    return True
