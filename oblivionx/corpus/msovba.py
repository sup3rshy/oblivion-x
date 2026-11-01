"""MS-OVBA (vbaProject.bin) and MS-CFB writer.

Generates valid, uncompiled VBA projects (vbaProject.bin) from scratch so the
corpus generator can produce real .docm/.xlsm files on Linux. The writer was
reverse-engineered from files produced by Microsoft Word/Excel 2016 and is
validated by round-tripping through oletools + opening the generated files
in Microsoft Office.

Layout produced:
  * dir stream: uncompressed record bytes wrapped in an MS-OVBA compressed
    container (signature byte 0x01 + literal-only token chunks).
  * each module stream: source code wrapped in the same container
    (textoffset = 0, no performance cache => uncompiled module).
  * CFB container: header + FAT + directory + miniFAT + mini stream +
    regular stream sectors. Directory entry order, tree shape, colors and
    mini-stream ordering replicate Word/Excel's own output.
"""
from __future__ import annotations

import struct
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# MS-OVBA compression (2.4.1). Literal-only token encoding: valid, simple,
# and the same strategy Word itself uses for short streams.
# ---------------------------------------------------------------------------

def msovba_compress(data: bytes, chunk_input: int = 3640) -> bytes:
    """Compress *data* into a CompressedContainer (signature 0x01 + chunks).

    Uses literal tokens only. Each chunk holds at most `chunk_input` source
    bytes so that (flags + literals) stays within the 4096-byte chunk limit.
    """
    out = bytearray([0x01])
    for start in range(0, len(data), chunk_input):
        block = data[start:start + chunk_input]
        n = len(block)
        token_data = bytearray()
        for i in range(0, n, 8):
            token_data.append(0x00)              # 8 literal tokens
            token_data.extend(block[i:i + 8])
        chunk_size = 2 + len(token_data)    # header + token data
        field = chunk_size - 3              # CompressedChunkSize - 3
        # signature bits 12-14 MUST be 0b011, flag bit 15 = 1 (compressed)
        header = 0x8000 | (0b011 << 12) | (field & 0x0FFF)
        out.extend(struct.pack("<H", header))
        out.extend(token_data)
    return bytes(out)


# ---------------------------------------------------------------------------
# dir stream records (MS-OVBA 2.3.4.2)
# ---------------------------------------------------------------------------

def _rec(id_: int, payload: bytes) -> bytes:
    return struct.pack("<H", id_) + payload


def rec_projectsyskind(syskind: int = 3) -> bytes:
    return _rec(0x0001, struct.pack("<LL", 4, syskind))


def rec_projectlcid(lcid: int = 0x0409) -> bytes:
    return _rec(0x0002, struct.pack("<LL", 4, lcid))


def rec_projectlcidinvoke(lcid: int = 0x0409) -> bytes:
    return _rec(0x0014, struct.pack("<LL", 4, lcid))


def rec_projectcodepage(codepage: int = 0x04E4) -> bytes:  # 1252
    return _rec(0x0003, struct.pack("<LH", 2, codepage))


def rec_projectname(name: str) -> bytes:
    raw = name.encode("latin-1")
    return _rec(0x0004, struct.pack("<L", len(raw)) + raw)


def rec_projectdocstring(docstring: bytes = b"") -> bytes:
    return (_rec(0x0005, struct.pack("<L", len(docstring)) + docstring
                 + struct.pack("<H", 0x0040)
                 + struct.pack("<L", len(docstring) * 2)
                 + docstring.decode("latin-1").encode("utf-16-le")))


def rec_projecthelpfilepath(path: bytes = b"") -> bytes:
    return (_rec(0x0006, struct.pack("<L", len(path)) + path
                 + struct.pack("<H", 0x003D)
                 + struct.pack("<L", len(path)) + path))


def rec_projecthelpcontext(context: int = 0) -> bytes:
    return _rec(0x0007, struct.pack("<LL", 4, context))


def rec_projectlibflags(flags: int = 0) -> bytes:
    return _rec(0x0008, struct.pack("<LL", 4, flags))


def rec_projectversion(major: int = 0x6D0B902A, minor: int = 0x000C) -> bytes:
    return _rec(0x0009, struct.pack("<L", 4) + struct.pack("<LH", major, minor))


def rec_projectconstants(constants: bytes = b"") -> bytes:
    return (_rec(0x000C, struct.pack("<L", len(constants)) + constants
                 + struct.pack("<H", 0x003C)
                 + struct.pack("<L", len(constants) * 2)
                 + constants.decode("latin-1").encode("utf-16-le")))


def _ref_name(name: str) -> bytes:
    raw = name.encode("latin-1")
    return (_rec(0x0016, struct.pack("<L", len(raw)) + raw
                 + struct.pack("<H", 0x003E)
                 + struct.pack("<L", len(raw) * 2)
                 + name.encode("utf-16-le")))


def _ref_registered(libid: str) -> bytes:
    raw = libid.encode("latin-1")       # NO null terminator (as Word writes)
    payload = (struct.pack("<L", len(raw)) + raw
               + struct.pack("<L", 0) + struct.pack("<H", 0))
    return _rec(0x000D, struct.pack("<L", len(payload)) + payload)


STDOLE_LIBID = ("*\\G{00020430-0000-0000-C000-000000000046}#2.0#0#"
                "C:\\Windows\\System32\\stdole2.tlb#OLE Automation")
OFFICE_LIBID = ("*\\G{2DF8D04C-5BFA-101B-BDE5-00AA0044DE52}#2.0#0#"
                "C:\\Program Files\\Common Files\\Microsoft Shared\\OFFICE15\\"
                "MSO.DLL#Microsoft Office 15.0 Object Library")


def _ref_project(libid: str, major: int = 0x6D0B902A, minor: int = 0x0008) -> bytes:
    raw = libid.encode("latin-1")
    payload = (struct.pack("<L", len(raw)) + raw
               + struct.pack("<L", len(raw)) + raw
               + struct.pack("<LH", major, minor))
    return _rec(0x000E, struct.pack("<L", len(payload)) + payload)


NORMAL_LIBID = "*\\CNormal"


def build_references() -> bytes:
    # order mirrors Word: stdole, Normal (project ref), Office
    return (_ref_name("stdole") + _ref_registered(STDOLE_LIBID)
            + _ref_name("Normal") + _ref_project(NORMAL_LIBID)
            + _ref_name("Office") + _ref_registered(OFFICE_LIBID))


def rec_projectmodules(count: int) -> bytes:
    return _rec(0x000F, struct.pack("<LH", 2, count))


def rec_projectcookie(cookie: int = 0x1FE6) -> bytes:
    return _rec(0x0013, struct.pack("<LH", 2, cookie))


def build_module_record(name: str, kind: str, textoffset: int = 0,
                        cookie: int = 0x0000) -> bytes:
    """Build a MODULE record.

    kind: 'procedural' (.bas, MODULETYPE 0x0021) or
          'document' (ThisDocument/ThisWorkbook, MODULETYPE 0x0022).
    """
    raw = name.encode("latin-1")
    uni = name.encode("utf-16-le")
    out = bytearray()
    # MODULENAME
    out += _rec(0x0019, struct.pack("<L", len(raw)) + raw)
    # MODULENAMEUNICODE
    out += _rec(0x0047, struct.pack("<L", len(uni)) + uni)
    # MODULESTREAMNAME (name == stream name for our projects)
    out += (_rec(0x001A, struct.pack("<L", len(raw)) + raw
                 + struct.pack("<H", 0x0032) + struct.pack("<L", len(uni))
                 + uni))
    # MODULEDOCSTRING (empty)
    out += _rec(0x001C, struct.pack("<L", 0) + struct.pack("<H", 0x0048)
                + struct.pack("<L", 0))
    # MODULEOFFSET (source starts at 0: no performance cache)
    out += _rec(0x0031, struct.pack("<LL", 4, textoffset))
    # MODULEHELPCONTEXT
    out += _rec(0x001E, struct.pack("<LL", 4, 0))
    # MODULECOOKIE
    out += _rec(0x002C, struct.pack("<LH", 2, cookie))
    # MODULETYPE
    mtype = 0x0021 if kind == "procedural" else 0x0022
    out += _rec(mtype, struct.pack("<L", 0))
    # TERMINATOR
    out += _rec(0x002B, struct.pack("<L", 0))
    return bytes(out)


def build_dir_stream(modules: List[Tuple[str, str, bytes]],
                     project_name: str) -> bytes:
    """Build the dir stream content (uncompressed records).

    modules: list of (module_name, kind, source_code_bytes).
    """
    out = bytearray()
    out += rec_projectsyskind()
    out += rec_projectlcid()
    out += rec_projectlcidinvoke()
    out += rec_projectcodepage()
    out += rec_projectname(project_name)
    out += rec_projectdocstring()
    out += rec_projecthelpfilepath()
    out += rec_projecthelpcontext()
    out += rec_projectlibflags()
    out += rec_projectversion()
    out += rec_projectconstants()
    out += build_references()
    out += rec_projectmodules(len(modules))
    out += rec_projectcookie()
    for i, (name, kind, _code) in enumerate(modules):
        out += build_module_record(name, kind, textoffset=0, cookie=0x56A0 + i)
    # final PROJECTTERMINATOR record as written by Word
    out += _rec(0x0010, struct.pack("<L", 0))
    return bytes(out)


# ---------------------------------------------------------------------------
# PROJECT / PROJECTwm streams
# ---------------------------------------------------------------------------

def build_project_stream(modules: List[Tuple[str, str, bytes]],
                         project_name: str, host: str,
                         project_id: Optional[str] = None) -> bytes:
    """Build the PROJECT stream text."""
    if project_id is None:
        project_id = "{%s}" % str(uuid.uuid4()).upper()
    lines = [
        f'ID="{project_id}"',
    ]
    for name, kind, _ in modules:
        if kind == "document":
            lines.append(f"Document={name}/&H00000000")
    for name, kind, _ in modules:
        if kind == "procedural":
            lines.append(f"Module={name}")
    lines += [
        f'Name="{project_name}"',
        'HelpContextID="0"',
        'VersionCompatible32="393222000"',
        '',
        '[Host Extender Info]',
        '&H00000001={3832D640-CF90-11CF-8E43-00A0C911005A};VBE;&H00000000',
        '',
        '[Workspace]',
    ]
    for name, kind, _ in modules:
        if kind == "document":
            lines.append(f"{name}=0, 0, 0, 0, C")
    for name, kind, _ in modules:
        if kind == "procedural":
            lines.append(f"{name}=32, 32, 1632, 763, ")
    return ("\r\n".join(lines) + "\r\n").encode("latin-1")


def build_projectwm_stream(modules: List[Tuple[str, str, bytes]]) -> bytes:
    """Build PROJECTwm: ANSI name + NUL + UTF-16 name + NULs per module."""
    out = bytearray()
    for name, _kind, _code in modules:
        out += name.encode("latin-1") + b"\x00"
        out += name.encode("utf-16-le") + b"\x00\x00"
    return bytes(out)


# ---------------------------------------------------------------------------
# MS-CFB writer
# ---------------------------------------------------------------------------

NOSTREAM = 0xFFFFFFFF
FREESECT = 0xFFFFFFFE
FATSECT = 0xFFFFFFFD
ENDOFCHAIN = 0xFFFFFFFE          # in miniFAT
SECTOR_SIZE = 512
MINI_SECTOR_SIZE = 64
MINI_CUTOFF = 4096


class _DirEntry:
    __slots__ = ("sid", "name", "etype", "start", "size", "left", "right",
                 "child")

    def __init__(self, sid, name, etype, start=0, size=0):
        self.sid = sid
        self.name = name
        self.etype = etype          # 5 root, 1 storage, 2 stream
        self.start = start
        self.size = size
        self.left = NOSTREAM
        self.right = NOSTREAM
        self.child = NOSTREAM


def _pack_entry(e: _DirEntry, color: int) -> bytes:
    name_u = e.name.encode("utf-16-le")
    buf = bytearray(128)
    buf[0:len(name_u)] = name_u
    struct.pack_into("<H", buf, 64, len(name_u) + 2)   # incl. null terminator
    struct.pack_into("<B", buf, 66, e.etype)
    struct.pack_into("<B", buf, 67, color)             # 1 = black, 0 = red
    struct.pack_into("<I", buf, 68, e.left)
    struct.pack_into("<I", buf, 72, e.right)
    struct.pack_into("<I", buf, 76, e.child)
    # CLSID zeros, state bits 0, timestamps 0
    struct.pack_into("<I", buf, 116, e.start)
    struct.pack_into("<Q", buf, 120, e.size)
    return bytes(buf)


def build_cfb(root_children: Dict[str, bytes],
              storages: Dict[str, Dict[str, bytes]]) -> bytes:
    """Build an OLE Compound File (CFB, v3, 512-byte sectors).

    Directory-entry order, tree shape, colors and stream ordering replicate
    Microsoft Word/Excel output (validated by opening generated files in
    Office).

    root_children: {stream_name: data} directly under the Root Entry.
    storages: {storage_name: {stream_name: data}}.
    """
    # ---- directory entries (Word's ordering) -------------------------------
    entries: List[_DirEntry] = []
    entries.append(_DirEntry(0, "Root Entry", 5))
    sid_of: Dict[Tuple[Optional[str], str], int] = {}
    root_streams: Dict[str, bytes] = dict(root_children)

    # root streams: PROJECT first, PROJECTwm last (as Word does)
    ordered_root: List[str] = []
    if "PROJECT" in root_streams:
        ordered_root.append("PROJECT")
    for name in sorted(root_streams.keys(), key=str.lower):
        if name not in ("PROJECT", "PROJECTwm"):
            ordered_root.append(name)
    if "PROJECTwm" in root_streams:
        ordered_root.append("PROJECTwm")

    for name in ordered_root:
        entries.append(_DirEntry(len(entries), name, 2,
                                 size=len(root_streams[name])))
        sid_of[(None, name)] = len(entries) - 1

    # storage streams: document module first, then the rest sorted by name
    for sname in sorted(storages.keys(), key=str.lower):
        names = list(storages[sname].keys())
        doc_names = [n for n in names
                     if n.lower() in ("thisdocument", "thisworkbook", "sheet1")]
        others = sorted([n for n in names if n not in doc_names],
                        key=str.lower)
        for name in doc_names + others:
            entries.append(_DirEntry(len(entries), name, 2,
                                     size=len(storages[sname][name])))
            sid_of[(sname, name)] = len(entries) - 1

    # storages LAST (Word puts the VBA storage after its streams)
    for sname in sorted(storages.keys(), key=str.lower):
        entries.append(_DirEntry(len(entries), sname, 1))
        sid_of[(sname, None)] = len(entries) - 1

    # ---- mini / regular split ----------------------------------------------
    mini_parts: List[Tuple[_DirEntry, bytes]] = []
    regular_parts: List[Tuple[_DirEntry, bytes]] = []
    for e in entries[1:]:
        if e.etype != 2:
            continue
        data = root_streams.get(e.name)
        if data is None:
            data = next(storages[s][e.name] for s in storages
                        if e.name in storages[s])
        (mini_parts if len(data) < MINI_CUTOFF else regular_parts).append((e, data))

    # mini stream order mirrors Word: document modules, procedurals,
    # _VBA_PROJECT, dir, PROJECTwm, PROJECT
    def mini_sort_key(item: Tuple[_DirEntry, bytes]) -> Tuple[int, str]:
        base = item[0].name.lower()
        if base in ("thisdocument", "thisworkbook"):
            return (0, base)
        if base == "sheet1":
            return (1, base)
        if base == "_vba_project":
            return (2, base)
        if base == "dir":
            return (3, base)
        if base == "projectwm":
            return (4, base)
        if base == "project":
            return (5, base)
        return (1, base)   # procedural modules

    mini_parts.sort(key=mini_sort_key)

    mini_stream = bytearray()
    mini_sector_map: List[Tuple[_DirEntry, int, int]] = []
    for e, data in mini_parts:
        start = len(mini_stream) // MINI_SECTOR_SIZE
        padded = data + b"\x00" * (-len(data) % MINI_SECTOR_SIZE)
        count = len(padded) // MINI_SECTOR_SIZE
        mini_sector_map.append((e, start, count))
        e.start = start
        mini_stream += padded

    n_mini_sectors = len(mini_stream) // MINI_SECTOR_SIZE
    mini_fat_sectors = (n_mini_sectors * 4 + SECTOR_SIZE - 1) // SECTOR_SIZE \
        if n_mini_sectors > 0 else 0
    mini_stream_sectors = (len(mini_stream) + SECTOR_SIZE - 1) // SECTOR_SIZE \
        if len(mini_stream) > 0 else 0

    # ---- regular streams -----------------------------------------------------
    regular_map: List[Tuple[_DirEntry, int, int]] = []
    n_regular = 0
    for e, data in regular_parts:
        count = (len(data) + SECTOR_SIZE - 1) // SECTOR_SIZE
        regular_map.append((e, 0, count))
        n_regular += count

    # ---- directory tree (Word's shape) --------------------------------------
    def sid(sname: Optional[str], name: str) -> int:
        return sid_of[(sname, name)]

    root_entry = entries[0]
    proj_sid = sid(None, "PROJECT") if "PROJECT" in root_streams else None
    projwm_sid = sid(None, "PROJECTwm") if "PROJECTwm" in root_streams else None
    vba_sids = [sid(s, None) for s in storages]

    # Root.child = PROJECT; PROJECT.left = VBA storage; PROJECT.right =
    # PROJECTwm
    if proj_sid is not None:
        root_entry.child = proj_sid
        if vba_sids:
            entries[proj_sid].left = vba_sids[0]
        if projwm_sid is not None:
            entries[proj_sid].right = projwm_sid
    elif vba_sids:
        root_entry.child = vba_sids[0]

    # per-storage children: document module first (child), remaining modules
    # chained via left pointers, _VBA_PROJECT via the first module's right
    # pointer, dir via the last module's left pointer.
    for sname in storages:
        names = [e.name for e in entries if e.etype == 2
                 and (sname, e.name) in sid_of]
        doc_names = [n for n in names if n.lower()
                     in ("thisdocument", "thisworkbook", "sheet1")]
        others = sorted([n for n in names if n not in doc_names
                         and n.lower() not in ("_vba_project", "dir")],
                        key=str.lower)
        ordered = doc_names + others
        if not ordered:
            continue
        entries[sid(sname, None)].child = sid(sname, ordered[0])
        if (sname, "_VBA_PROJECT") in sid_of:
            entries[sid(sname, ordered[0])].right = sid(sname, "_VBA_PROJECT")
        prev = sid(sname, ordered[0])
        for name in ordered[1:]:
            entries[prev].left = sid(sname, name)
            prev = sid(sname, name)
        if (sname, "dir") in sid_of:
            entries[prev].left = sid(sname, "dir")

    # colors: storages red, PROJECTwm/dir red, everything else black
    def color_of(e: _DirEntry) -> int:
        base = e.name.lower()
        if e.etype == 1:
            return 0
        if base in ("projectwm", "dir"):
            return 0
        return 1

    # ---- sector layout -------------------------------------------------------
    n_entries = len(entries)
    dir_sectors = (n_entries * 128 + SECTOR_SIZE - 1) // SECTOR_SIZE

    first_minifat = 1 + dir_sectors
    first_mini = first_minifat + mini_fat_sectors
    first_regular = first_mini + mini_stream_sectors
    total = first_regular + n_regular
    fat_sectors = (total * 4 + SECTOR_SIZE - 1) // SECTOR_SIZE

    pos = first_regular
    for e, _, count in regular_map:
        e.start = pos
        pos += count

    # ---- FAT -------------------------------------------------------------------
    fat = [FREESECT] * total
    for i in range(fat_sectors):
        fat[i] = FATSECT

    def chain(first: int, count: int):
        for i in range(count):
            fat[first + i] = (first + i + 1) if i < count - 1 else ENDOFCHAIN

    chain(1, dir_sectors)
    if mini_fat_sectors:
        chain(first_minifat, mini_fat_sectors)
    if mini_stream_sectors:
        chain(first_mini, mini_stream_sectors)
    for e, start, count in regular_map:
        chain(start, count)

    # ---- miniFAT ----------------------------------------------------------------
    mini_fat = bytearray()
    if n_mini_sectors > 0:
        mini_fat = bytearray(struct.pack("<I", ENDOFCHAIN) * n_mini_sectors)
        for e, start, count in mini_sector_map:
            for i in range(count):
                struct.pack_into("<I", mini_fat, (start + i) * 4,
                                 (start + i + 1) if i < count - 1 else ENDOFCHAIN)

    # ---- header ----------------------------------------------------------------
    header = bytearray(SECTOR_SIZE)
    header[0:8] = bytes.fromhex("D0CF11E0A1B11AE1")
    header[76:512] = b"\xff" * (512 - 76)  # unused DIFAT entries = FREESECT
    struct.pack_into("<H", header, 24, 0x003E)
    struct.pack_into("<H", header, 26, 0x0003)
    struct.pack_into("<H", header, 28, 0xFFFE)
    struct.pack_into("<H", header, 30, 9)
    struct.pack_into("<H", header, 32, 6)
    struct.pack_into("<I", header, 40, 0)
    struct.pack_into("<I", header, 44, fat_sectors)
    struct.pack_into("<I", header, 48, 1)          # first directory sector
    struct.pack_into("<I", header, 52, 0)          # transaction signature
    struct.pack_into("<I", header, 56, MINI_CUTOFF)
    if mini_fat_sectors:
        struct.pack_into("<I", header, 60, first_minifat)
        struct.pack_into("<I", header, 64, mini_fat_sectors)
    else:
        struct.pack_into("<I", header, 60, ENDOFCHAIN)
        struct.pack_into("<I", header, 64, 0)
    struct.pack_into("<I", header, 68, ENDOFCHAIN)
    struct.pack_into("<I", header, 72, 0)
    for i in range(fat_sectors):
        struct.pack_into("<I", header, 76 + 4 * i, i)
    entries[0].start = first_mini if mini_stream_sectors else ENDOFCHAIN
    entries[0].size = len(mini_stream)

    # ---- assemble ------------------------------------------------------------------
    out = bytearray()
    out += header
    for i in range(fat_sectors):
        s = bytearray(SECTOR_SIZE)
        for j in range(SECTOR_SIZE // 4):
            idx = i * (SECTOR_SIZE // 4) + j
            if idx < total:
                struct.pack_into("<I", s, j * 4, fat[idx])
        out += s
    for d in range(dir_sectors):
        s = bytearray()
        for j in range(4):
            idx = d * 4 + j
            if idx < n_entries:
                s += _pack_entry(entries[idx], color_of(entries[idx]))
            else:
                s += b"\x00" * 128
        out += s
    if mini_fat_sectors:
        out += mini_fat.ljust(mini_fat_sectors * SECTOR_SIZE, b"\x00")
    if mini_stream_sectors:
        out += mini_stream.ljust(mini_stream_sectors * SECTOR_SIZE, b"\x00")
    for e, start, count in regular_map:
        data = next(d for (ee, d) in regular_parts if ee is e)
        out += data.ljust(count * SECTOR_SIZE, b"\x00")
    return bytes(out)


# ---------------------------------------------------------------------------
# vbaProject.bin assembly
# ---------------------------------------------------------------------------

def _normalize_module_source(name: str, kind: str, code: str) -> str:
    """Ensure required VBA attributes are present in the module source."""
    if kind == "document":
        needed = [
            f'Attribute VB_Name = "{name}"',
            f'Attribute VB_Base = "1Normal.{name}"',
            'Attribute VB_GlobalNameSpace = False',
            'Attribute VB_Creatable = False',
            'Attribute VB_PredeclaredId = True',
            'Attribute VB_Exposed = True',
            'Attribute VB_TemplateDerived = True',
            'Attribute VB_Customizable = True',
        ]
        lines = code.splitlines()
        have = {ln.split("=")[0].strip().lower() for ln in lines
                if ln.lstrip().lower().startswith("attribute vb_")}
        for attr in needed:
            key = attr.split("=")[0].strip().lower()
            if key not in have:
                lines.insert(0, attr)
        return "\r\n".join(lines) + "\r\n"
    return code


def build_vba_project_bin(modules: List[Tuple[str, str, str]],
                          host: str,
                          project_name: Optional[str] = None,
                          project_id: Optional[str] = None) -> bytes:
    """Build a complete vbaProject.bin for Word ('word') or Excel ('excel').

    modules: list of (module_name, kind, vba_source_text).
      kind: 'document' (ThisDocument/ThisWorkbook) or 'procedural'.
    """
    if project_name is None:
        project_name = "Project" if host == "word" else "VBAProject"
    mods = [(name, kind,
             _normalize_module_source(name, kind, code).encode("latin-1"))
            for name, kind, code in modules]

    vba_streams = {
        "dir": msovba_compress(build_dir_stream(mods, project_name)),
        "_VBA_PROJECT": _vba_project_blob(host),
    }
    for name, kind, code in mods:
        # uncompiled module: PLAIN source code (no performance cache, no
        # compression container) per MS-OVBA 2.3.4.3 for uncompiled modules.
        vba_streams[name] = code

    return build_cfb(
        {"PROJECT": build_project_stream(mods, project_name, host, project_id),
         "PROJECTwm": build_projectwm_stream(mods)},
        {"VBA": vba_streams})


def _vba_project_blob(host: str) -> bytes:
    from oblivionx import resources_dir
    fname = "vba_project_word.bin" if host == "word" else "vba_project_excel.bin"
    return (Path(resources_dir) / fname).read_bytes()
