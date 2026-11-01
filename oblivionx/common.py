"""Oblivion-X: shared definitions.

Behavior catalog, attack stages, family definitions, obfuscation taxonomy,
and JSON helpers. Everything in the project is grounded on these definitions
so that ground truth, static analysis, dynamic telemetry, reconstruction and
evaluation all speak the same language.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_NAME = "Oblivion-X"
VERSION = "0.1.0"

# --------------------------------------------------------------------------
# Attack stages (chronological, as used for stage reconstruction)
# --------------------------------------------------------------------------
STAGE_ORDER: List[str] = [
    "delivery",        # auto-exec entry points (AutoOpen, Document_Open, ...)
    "defense_evasion", # obfuscation usage, VBOM security disable, hidden windows
    "execution",       # spawning shells / running commands (Shell, WScript, cmd)
    "c2_download",     # network fetch (XMLHTTP, WebClient.DownloadFile, URLs)
    "persistence",     # registry / startup / template infection
    "exfiltration",    # email (Outlook), FTP upload
    "impact",          # file write/execute/encrypt/delete of payloads
    "cleanup",         # post-impact actions (code deletion, self-delete)
]

# --------------------------------------------------------------------------
# Behavior catalog.
# Each behavior belongs to a stage (or None for benign) and carries the
# static/dynamic hints used by the pipelines to observe it.
# bonapt_category maps macro-domain behaviors onto Bon-APT's 10 behavior
# categories (Device, File, Kernel, Memory, Network, Process&thread,
# Registry, System, Text, Window) for cross-domain abstraction.
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class BehaviorDef:
    id: str
    stage: Optional[str]
    description: str
    bonapt_category: str
    vba_hints: List[str] = field(default_factory=list)      # VBA API substrings
    ps_hints: List[str] = field(default_factory=list)       # PowerShell substrings


BEHAVIOR_DEFS: Dict[str, BehaviorDef] = {b.id: b for b in [
    # delivery
    BehaviorDef("macro_entry", "delivery",
                "Auto-exec entry point present (AutoOpen/Workbook_Open/...)",
                "System", ["Sub AutoOpen", "Sub Workbook_Open", "Sub Document_Open",
                           "Sub Auto_Open", "Sub AutoExec", "Sub Document_New"]),
    # execution
    BehaviorDef("shell_run", "execution",
                "A shell/process is spawned (Shell, WScript.Shell Run)",
                "Process & thread", ["Shell ", "WScript.Shell", ".Run ", "ShellExecute",
                                     "CreateObject", "Shell.Application"]),
    BehaviorDef("powershell_run", "execution",
                "PowerShell is invoked with a command",
                "System", ["powershell", "-EncodedCommand", "-ExecutionPolicy",
                           "PowerShell.exe", "-NoProfile", "-WindowStyle"]),
    BehaviorDef("cmd_run", "execution",
                "cmd.exe is invoked",
                "System", ["cmd.exe", "cmd /c", "Cmd.Exe", "%COMSPEC%"]),
    BehaviorDef("env_read", "execution",
                "Environment variables read (Environ) to build paths",
                "System", ["Environ("]),
    # defense_evasion
    BehaviorDef("string_concat", "defense_evasion",
                "Strings split and chained with & / + (split obfuscation)",
                "Text", ["&", "+"]),
    BehaviorDef("chr_encode", "defense_evasion",
                "Characters built via Chr/ChrW/Asc/Hex arithmetic",
                "Text", ["Chr(", "ChrW(", "Chr$(", "Asc(", "Hex("]),
    BehaviorDef("base64_encode", "defense_evasion",
                "Base64-encoded payload present",
                "Text", ["base64", "b64", "FromBase64String", "Encoding",
                         "-enc "]),
    BehaviorDef("dead_code", "defense_evasion",
                "Logic obfuscation: unreachable code / decoy routines",
                "Text", []),
    BehaviorDef("vbom_security_disable", "defense_evasion",
                "VBA security disabled (AccessVBOM)",
                "System", ["AccessVBOM", "Application.VBE", "VBAWarnings"]),
    BehaviorDef("window_hide", "defense_evasion",
                "Window style hidden (vbnHide / -WindowStyle Hidden)",
                "Window", ["vbHide", "-WindowStyle Hidden", "-w Hidden", "0)"],),
    BehaviorDef("msgbox_gate", "defense_evasion",
                "MsgBox/InputBox interaction gate",
                "Window", ["MsgBox", "InputBox"]),
    # c2_download
    BehaviorDef("http_download", "c2_download",
                "HTTP download (XMLHTTP, WebClient.DownloadFile, URLDownloadToFile)",
                "Network", ["XMLHTTP", "DownloadFile", "URLDownloadToFile",
                            "OpenURL", "WinHttpRequest", "MSXML2"]),
    BehaviorDef("url_reference", "c2_download",
                "A URL literal appears (static observation only)",
                "Network", ["http://", "https://", "ftp://"]),
    BehaviorDef("dns_resolve", "c2_download",
                "DNS resolution of a contacted domain",
                "Network", []),
    # persistence
    BehaviorDef("registry_write", "persistence",
                "Registry write (RegWrite / reg add / HKCU...)",
                "Registry", ["RegWrite", "reg add", "HKCU", "HKLM",
                             "HKEY_CURRENT_USER", "CurrentVersion\\Run"]),
    BehaviorDef("startup_write", "persistence",
                "File written to Startup folder",
                "File", ["Startup", "XLSTART", "AppData\\Roaming\\Microsoft\\Word\\STARTUP"]),
    BehaviorDef("office_template_infect", "persistence",
                "Office global template infected (Normal.dotm / XLSTART workbook)",
                "File", ["Normal.dotm", "NormalTemplate", "XLSTART", "Book1",
                         "Personal.xls", "VBProject", "VBComponents"]),
    # exfiltration
    BehaviorDef("outlook_access", "exfiltration",
                "Outlook object model accessed",
                "Network", ["Outlook.Application", "Outlook.MailItem",
                            "Outlook.Session", "Namespace"]),
    BehaviorDef("outlook_send", "exfiltration",
                "Mail sent through Outlook",
                "Network", [".Send", ".MailItem", "Recipients.Add", ".Body"]),
    BehaviorDef("ftp_upload", "exfiltration",
                "FTP upload of collected data",
                "Network", ["FTP", "OpenURL", "UploadFile", "InternetConnect",
                            "FtpPutFile"]),
    # impact
    BehaviorDef("file_write", "impact",
                "Additional file written to disk (payload / log)",
                "File", ["Open ", "CreateTextFile", "WriteLine", "SaveAs",
                         "SaveCopyAs", "CreateFile", "FileSystemObject",
                         "WriteFile", "Print #"]),
    BehaviorDef("file_execute", "impact",
                "Dropped executable / script executed",
                "Process & thread", ["Shell ", ".Run ", "Invoke-Item", "Start-Process"]),
    BehaviorDef("file_encrypt", "impact",
                "Files encrypted (ransomware-like)",
                "File", ["Encrypt", "Rijndael", "AES", "Crypt", "XOR"]),
    BehaviorDef("file_delete", "impact",
                "Files deleted",
                "File", ["Kill ", "DeleteFile", "Remove-Item", "Del "]),
    # cleanup
    BehaviorDef("code_delete", "cleanup",
                "VBA code deleted post-execution (CodeModule.DeleteLines)",
                "System", ["DeleteLines", "CodeModule"]),
    # benign
    BehaviorDef("save_as_pdf", None,
                "Worksheet/document exported to PDF (benign)",
                "File", ["ExportAsFixedFormat", "xlTypePDF"]),
    BehaviorDef("print_document", None,
                "Document printed (benign)",
                "Text", ["PrintOut", ".Print"]),
    BehaviorDef("data_copy", None,
                "Cells copied/formatted (benign)",
                "Text", [".Copy", ".PasteSpecial", "Range("]),
]}


def behavior_stage(bid: str) -> Optional[str]:
    return BEHAVIOR_DEFS[bid].stage


def behavior_bonapt(bid: str) -> str:
    return BEHAVIOR_DEFS[bid].bonapt_category


# Bon-APT's ten abstraction categories (Table 2 of the paper).
BONAPT_CATEGORIES: List[str] = [
    "Device", "File", "Kernel", "Memory", "Network",
    "Process & thread", "Registry", "System", "Text", "Window",
]

# --------------------------------------------------------------------------
# Obfuscation taxonomy (Section 2.4 of the Oblivion paper)
# --------------------------------------------------------------------------
OBFUSCATION_TECHNIQUES: List[str] = [
    "plain",   # no obfuscation
    "random",  # random obfuscation: randomized identifiers
    "split",   # split obfuscation: strings chained with & and +
    "encode",  # encode obfuscation: Chr/Asc/Hex/Base64
    "logic",   # logic obfuscation: unreachable dead code
    "combo",   # random + split + encode + logic combined
]

# --------------------------------------------------------------------------
# Malware families (ground truth templates).
# Mirrors the families observed in the Oblivion paper (Table 4) plus
# benign families, with fully synthetic, harmless payloads (127.0.0.1 /
# example.com markers) so the corpus is safe to execute anywhere.
# --------------------------------------------------------------------------
@dataclass
class FamilySpec:
    family: str
    description: str
    formats: List[str]                       # docm / xlsm
    stages: List[str]                        # ordered attack chain (GT)
    behaviors: List[str]                     # full behavior list (GT)
    interaction: bool = False                # needs MsgBox/InputBox interaction
    env_dep: Optional[str] = None            # needs outlook / ftp available
    date_trigger: bool = False               # behavior only on specific date
    timeout: bool = False                    # deliberately slow (for E8)


FAMILIES: Dict[str, FamilySpec] = {f.family: f for f in [
    FamilySpec(
        "donoff_downloader",
        "Donoff-style downloader: PowerShell downloads and runs a payload "
        "(simulated: fetches a benign marker from 127.0.0.1/example.com).",
        ["docm", "xlsm"],
        ["delivery", "defense_evasion", "execution", "c2_download", "impact"],
        ["macro_entry", "env_read", "powershell_run", "shell_run",
         "window_hide", "http_download", "url_reference", "file_write",
         "file_execute"]),
    FamilySpec(
        "metacol_mailer",
        "Metacol-style mass mailer: hijacks Outlook to send copies of itself.",
        ["docm"],
        ["delivery", "exfiltration"],
        ["macro_entry", "outlook_access", "outlook_send"],
        env_dep="outlook"),
    FamilySpec(
        "laroux_replicator",
        "Laroux-style replicator: infects the global template / XLSTART "
        "so every new workbook is infected.",
        ["xlsm"],
        ["delivery", "persistence", "impact"],
        ["macro_entry", "office_template_infect", "file_write", "env_read",
         "startup_write"]),
    FamilySpec(
        "locky_ransom",
        "Locky-style ransomware simulation: encrypts marker files in a "
        "sandbox folder (XOR only, reversible, local test dir).",
        ["docm", "xlsm"],
        ["delivery", "persistence", "impact"],
        ["macro_entry", "file_write", "file_encrypt", "registry_write",
         "env_read"]),
    FamilySpec(
        "vba_dropper",
        "VBA dropper: writes an embedded (benign) executable stub and runs "
        "it (Run Executable attack category).",
        ["docm", "xlsm"],
        ["delivery", "execution", "impact"],
        ["macro_entry", "file_write", "file_execute", "env_read", "shell_run"]),
    FamilySpec(
        "marker_ftp",
        "Marker-style info-stealer: collects pseudo-logs and uploads them "
        "via FTP (simulated local FTP marker).",
        ["docm", "xlsm"],
        ["delivery", "execution", "exfiltration"],
        ["macro_entry", "file_write", "ftp_upload", "env_read", "shell_run",
         "cmd_run"],
        env_dep="ftp"),
    FamilySpec(
        "thus_wiper",
        "Thus-style wiper: payload activates only on December 13th and "
        "deletes marker files.",
        ["docm"],
        ["delivery", "defense_evasion", "impact"],
        ["macro_entry", "file_delete", "env_read"],
        date_trigger=True),
    FamilySpec(
        "valyria_dual",
        "Valyria-style dual-purpose: downloads an extra payload and sends "
        "pseudo-information to a remote endpoint (simulated).",
        ["docm", "xlsm"],
        ["delivery", "c2_download", "exfiltration"],
        ["macro_entry", "http_download", "url_reference", "outlook_access",
         "outlook_send"],
        env_dep="outlook"),
    FamilySpec(
        "benign_formatting",
        "Benign: formats a table and exports sheets to PDF on close.",
        ["docm", "xlsm"],
        ["delivery"],
        ["macro_entry", "save_as_pdf", "data_copy"]),
    FamilySpec(
        "benign_report",
        "Benign: copies data into a report sheet and prints it.",
        ["docm", "xlsm"],
        ["delivery"],
        ["macro_entry", "data_copy", "print_document", "save_as_pdf"]),
    FamilySpec(
        "donoff_interaction",
        "Donoff variant with a MsgBox gate: the download only happens if "
        "the user clicks the button (anti-automation trick).",
        ["docm"],
        ["delivery", "defense_evasion", "execution", "c2_download", "impact"],
        ["macro_entry", "msgbox_gate", "env_read", "powershell_run",
         "http_download", "url_reference", "file_write", "file_execute",
         "window_hide", "shell_run"],
        interaction=True),
    FamilySpec(
        "broken_semantic",
        "Syntactically valid macro that fails at runtime (undefined Sub) - "
        "for E7 failure analysis.",
        ["docm"],
        ["delivery"],
        ["macro_entry"]),
    FamilySpec(
        "empty_macro",
        "File with a macro module but no code (empty routines) - E7.",
        ["docm"],
        [],
        []),
    FamilySpec(
        "slow_timeout",
        "Macro with a long busy loop (anti-analysis delay) - E7/E8.",
        ["docm"],
        ["delivery", "execution"],
        ["macro_entry", "shell_run", "cmd_run"],
        timeout=True),
]}

# --------------------------------------------------------------------------
# Failure taxonomy (Oblivion Section 5.2, extended for E7)
# --------------------------------------------------------------------------
FAILURE_CLASSES: List[str] = [
    "static_empty",          # no VBA code
    "static_corrupted",      # unparsable macro
    "static_password",       # password-protected VBA project
    "dynamic_semantic",      # runtime error in original macro
    "dynamic_instrumentation",  # error introduced by instrumentation
    "dynamic_timeout",       # exceeded time limit
    "dynamic_interaction",   # gated on user interaction that was not handled
    "dynamic_env",           # missing environment dependency (Outlook/FTP)
    "dynamic_date",          # date-triggered payload did not fire
]

# --------------------------------------------------------------------------
# JSON helpers
# --------------------------------------------------------------------------
def write_json(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, default=str)


def read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_ground_truth(path: Path) -> Dict[str, Any]:
    return read_json(path)


def stage_index(stage: str) -> int:
    return STAGE_ORDER.index(stage) if stage in STAGE_ORDER else -1
