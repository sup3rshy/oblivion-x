"""VBA source obfuscation transforms (Oblivion paper taxonomy, Section 2.4).

Four techniques + combinations, implemented as deterministic source-to-source
transforms:
  * random  - randomized identifiers (Random Obfuscation)
  * split   - string literals chained with & (Split Obfuscation)
  * encode  - Chr()/Asc() character building + Base64 blob (Encode)
  * logic   - unreachable decoy code (Logic Obfuscation)
  * combo   - all of the above

Entry points (Document_Open / Workbook_Open / auto-exec names) are NEVER
renamed, so the instrumented execution still finds them.
"""
from __future__ import annotations

import base64
import random
import re
from typing import Dict, List, Optional, Tuple

_PROTECTED = {
    # VBA keywords, entry points and intrinsics that must not be renamed
    "sub", "end", "function", "dim", "as", "string", "long", "integer",
    "double", "boolean", "object", "set", "call", "if", "then", "else",
    "elseif", "end if", "for", "next", "each", "in", "to", "while", "wend",
    "do", "loop", "exit", "on", "error", "resume", "goto", "open", "close",
    "print", "put", "get", "binary", "output", "append", "random",
    "document_open", "workbook_open", "autoclose", "autoopen", "auto_open",
    "thisdocument", "thisworkbook", "newmacros", "attribute", "vb_name",
    "private", "public", "byval", "byref", "and", "or", "not", "xor",
    "true", "false", "nothing", "date", "day", "month", "chr", "chrw",
    "asc", "len", "mid", "environ", "freefile", "shell", "msgbox",
    "vbyesno", "vbyes", "inputbox", "createobject", "getobject",
    "activeDocument", "activeworkbook", "worksheet", "worksheets",
    "range", "selection", "true", "false",
}


def _rand_name(rng: random.Random, base: str = "") -> str:
    alpha = "abcdefghijklmnopqrstuvwxyz"
    return (base or rng.choice(alpha) + rng.choice(alpha)) + \
        "".join(rng.choice(alpha + "0123456789") for _ in range(rng.randint(6, 11)))


def _rename_identifiers(code: str, rng: random.Random) -> str:
    """Rename variable names and non-entry Sub/Function names."""
    # collect identifiers declared with Dim / Set / For Each / As clauses
    mapping: Dict[str, str] = {}
    decl = re.findall(r"\b(?:Dim|Set)\s+([A-Za-z_]\w*)", code, re.I)
    args = re.findall(r"\b(?:ByVal|ByRef)\s+([A-Za-z_]\w*)\s+As", code, re.I)
    fdecl = re.findall(r"\b(?:Function|Sub)\s+([A-Za-z_]\w*)\s*\(",
                       code, re.I)
    for name in decl + args + fdecl:
        if name.lower() in _PROTECTED:
            continue
        if name not in mapping:
            mapping[name] = _rand_name(rng)
    for old, new in sorted(mapping.items(), key=lambda kv: -len(kv[0])):
        code = re.sub(rf"\b{re.escape(old)}\b", new, code)
    return code


def _apply_per_line(code: str, fn) -> str:
    """Apply a transform to code lines, leaving ``Attribute`` lines intact.

    Attribute values are compile-time metadata: splitting or encoding them
    produces syntactically invalid VBA.
    """
    out = []
    for line in code.splitlines(keepends=True):
        if line.lstrip().lower().startswith("attribute"):
            out.append(line)
        else:
            out.append(fn(line))
    return "".join(out)


def _split_strings(code: str, rng: random.Random) -> str:
    """Split long string literals with & chaining."""
    changed = [False]

    def repl(m: "re.Match") -> str:
        literal = m.group(1)
        if len(literal) < 8:
            return m.group(0)
        pieces: List[str] = []
        i = 0
        while i < len(literal):
            size = rng.randint(4, 9)
            pieces.append(literal[i:i + size])
            i += size
        changed[0] = True
        return " & ".join('"' + p + '"' for p in pieces)

    out = _apply_per_line(
        code, lambda line: re.sub(
            r'"([A-Za-z0-9_\\:\-/\. ]{8,})"', repl, line))
    if not changed[0]:
        # no long literal: split the first short literal so the technique
        # is always represented (and the ground truth stays consistent)
        done = [False]

        def _short(m: "re.Match") -> str:
            if done[0]:
                return m.group(0)
            done[0] = True
            lit = m.group(1)
            return " & ".join('"' + lit[i:i + 2] + '"'
                              for i in range(0, len(lit), 2))

        out = _apply_per_line(
            out, lambda line: re.sub(
                r'"([A-Za-z0-9_\\:\-/\. ]{6,})"', _short, line, count=1))
    return out


def _encode_strings(code: str, rng: random.Random) -> str:
    """Replace chosen literals with Chr() chains; add a Base64 blob."""
    targets = ["powershell.exe", "WScript.Shell", "MSXML2.XMLHTTP",
               "Outlook.Application", "oblivionx", "payload.exe",
               "127.0.0.1"]
    out = code
    for t in targets:
        if t in out:
            chain = " & ".join(f"Chr({ord(c)})" for c in t)
            out = out.replace('"' + t + '"', chain, 1)
    if out == code:
        # no known target: encode the first literal of length >= 5 so the
        # technique is always present in the sample
        done = [False]

        def _first(m: "re.Match") -> str:
            if done[0]:
                return m.group(0)
            done[0] = True
            return " & ".join(f"Chr({ord(c)})" for c in m.group(1))

        out = _apply_per_line(
            code, lambda line: re.sub(r'"([^"\r\n]{5,})"', _first, line,
                                      count=1))
    b64 = base64.b64encode(b"http://127.0.0.1:9090/payload.exe").decode()
    out += (f'\r\nPublic Function OblivionXDecoy() As String\r\n'
            f'    Dim b64 As String\r\n'
            f'    b64 = "{b64}"\r\n'
            f'    OblivionXDecoy = b64\r\n'
            f'End Function\r\n')
    return out


def _add_logic_junk(code: str, rng: random.Random) -> str:
    """Add unreachable decoy routines and dead branches."""
    # Readable names on purpose: logic obfuscation is dead code, not random
    # identifier obfuscation, and the detector must not confuse the two.
    junk = (
        '\r\nPublic Sub OblivionXJunkRoutine()\r\n'
        '    Dim junkcounter As Long\r\n'
        '    Dim junktext As String\r\n'
        '    If False Then\r\n'
        '        junktext = "decoy"\r\n'
        '        junkcounter = 1 + 1\r\n'
        '    End If\r\n'
        'End Sub\r\n'
    )
    dead = (
        '\r\n    Dim deadvarunused As Long\r\n'
        '    If 1 = 2 Then\r\n'
        '        deadvarunused = 999\r\n'
        '    End If\r\n'
    )
    # append junk sub at end; inject dead block after first Dim if possible
    out = junk + code
    out = out.replace("\r\nEnd Sub\r\n", dead + "\r\nEnd Sub\r\n", 1)
    return out


def obfuscate(code: str, technique: str, seed: int = 0) -> str:
    """Apply one obfuscation technique ('plain' returns code unchanged)."""
    rng = random.Random(seed ^ 0x0B11F17E)
    out = code
    if technique in ("random", "combo"):
        out = _rename_identifiers(out, rng)
    if technique in ("split", "combo"):
        out = _split_strings(out, rng)
    if technique in ("encode", "combo"):
        out = _encode_strings(out, rng)
    if technique in ("logic", "combo"):
        out = _add_logic_junk(out, rng)
    return out


def obfuscate_sample(doc_src: str, helper_src: str, technique: str,
                     seed: int = 0) -> Tuple[str, str]:
    """Obfuscate both modules of a sample (entry points preserved)."""
    return (obfuscate(doc_src, technique, seed),
            obfuscate(helper_src, technique, seed + 1))
