# Oblivion — paper summary (implementation paper)

> Sanna, Cara, Maiorca, Giacinto. *Oblivion: an open-source system for
> large-scale analysis of macro-based office malware.* J. Computer Virology
> and Hacking Techniques 20:783–802 (2024). doi:10.1007/s11416-024-00531-3

## Problem
- Macro-based Office files (VBA) are a top infection vector; macros are
  heavily obfuscated so static analysis fails.
- Existing tools focus on malicious/benign classification, not on
  *understanding* what the macro does (attack families, embedded scripts,
  contacted resources).
- Online/offline sandboxes are slow and can't handle large corpora or
  MsgBox-style interaction gates.

## Architecture (4 phases)
1. **Pre-processing** (static, via OleVBA): find macros, classify samples:
   *corrupted / password-protected / interaction-based / standard
   (.cls, .bas, .bas+.cls) / empty*; detect obfuscation heuristics
   (API presence, random names, encoding functions, & and + distributions).
2. **Instrumentation** (extension of ESET VHook): inject a logging VBA class
   + self-logging versions of methods (CreateObject, GetObject, Mid, …)
   to trace **every variable value and method call**; handles arrays/lists,
   inline statements, multi-line If/With/For/While, exceptions, comments.
3. **Execution**: instrumented file run in a VM (Windows 11 + Office 365 +
   Sandboxie); PyWinAuto handles MsgBox/InputBox interaction windows;
   win32com mirrors Close behavior for close-triggered macros.
4. **Post-processing** (report): call graph (methods truly executed),
   per-variable value evolution, PowerShell extraction + **PowerDrive**
   deobfuscation, attack profile (suspicious APIs, env variables, URLs).

## Obfuscation taxonomy (Section 2.4)
- **Random**: randomized identifiers
- **Split**: strings chained with `&` and `+`
- **Encode**: Replace/Asc/Chr/Hex or custom xor/Base64/Shift
- **Logic**: unreachable dead code

## Dataset & results
- 42,991 malicious files (27,512 Word + 15,479 Excel, VirusTotal 2018,
  score > 3): 30,750 analyzable (10,077 .cls, 12,897 .bas+.cls, 6,646
  interaction, 11,689 empty, 552 corrupted).
- Execution: 20,237 success (3,357 PowerShell; 16,880 non-PS), 10,513
  errors (7,962 semantic, 2,551 instrumentation).
- Non-PowerShell attack categories: Run Executable (6,235), File
  Manipulation (5,269), Office Infection (3,020), Outlook Infection (2,948),
  File Download (958).
- Top families: Metacol, Thus, Laroux, Donoff, Valyria, Marker, Alcaul,
  Locky, Madeba, Mailcab.
- Performance: **avg 41.11 s/sample** (28.70 s without outliers), most
  < 30 s; vs ANY.RUN (60 s default) and Falcon Sandbox (7–8 min).
- Case study: MsgBox-gated sample executes only after button click;
  ANY.RUN missed it, Oblivion handled it in 8.45 s.

## Limitations (Section 6)
- Only interactions directly linked to the macro are handled.
- Password-protected projects skipped (DPB→DPX patch works sometimes).
- Instrumentation errors mainly from oversized instrumented code.

## What Oblivion-X takes from this paper
- Instrumentation + variable tracing design (our instrumented corpus).
- Report sections (Shell Actions, Variable Values, Domain Traces, ...).
- Obfuscation taxonomy (our E3 variants) and attack categories (our
  families), pre-processing taxonomy (our E1), time/sample baseline (E8).
