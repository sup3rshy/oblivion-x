"""Static extraction of VBA from Office files (OLE + OOXML).

Wraps oletools to pull every module's source code out of .doc/.xls/.docm/
.xlsm files, plus file-level metadata. This mirrors the pre-processing
phase of Oblivion (which itself uses OleVBA).
"""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import olefile
from oletools.olevba import VBA_Project, _extract_vba

MODULE_EXTS = {0x21: ".bas", 0x22: ".cls", 0x19: ".bas"}


def extract_modules(path: Path) -> List[Dict[str, Any]]:
    """Extract all VBA modules of a file as
    [{name, kind, source, stream}], or [] if no macros."""
    path = Path(path)
    data = path.read_bytes()
    modules: List[Dict[str, Any]] = []
    if zipfile.is_zipfile(path):
        # OOXML: word/vbaProject.bin or xl/vbaProject.bin
        zf = zipfile.ZipFile(path)
        vba_name = next((n for n in zf.namelist()
                         if n.endswith("vbaProject.bin")), None)
        if vba_name is None:
            return modules
        ole = olefile.OleFileIO(zf.read(vba_name))
        try:
            modules = _extract_ole(ole)
        except Exception:
            return []
        ole.close()
        zf.close()
        return modules
    if olefile.isOleFile(data):
        ole = olefile.OleFileIO(data)
        try:
            modules = _extract_ole(ole)
        except Exception:
            return []
        ole.close()
    return modules


def _extract_ole(ole) -> List[Dict[str, Any]]:
    """Extract modules from an OLE container.

    oletools expects ``vba_root`` to be the storage *containing* the VBA
    storage (empty for an OOXML ``vbaProject.bin``, ``"Macros/"`` for a
    legacy Word document). It appends ``VBA/`` itself when opening module
    streams, so passing ``"VBA/"`` here yields a doubled path and no code.
    """
    out: List[Dict[str, Any]] = []
    for root in ("", "Macros/"):
        project_path = root + "PROJECT"
        dir_path = root + "VBA/dir"
        if not (ole.exists(project_path) and ole.exists(dir_path)):
            continue
        try:
            for subpath, filename, code in _extract_vba(
                    ole, root, project_path, dir_path, relaxed=True):
                if not code:
                    continue
                kind = "document" if filename.lower().endswith(".cls") \
                    else "procedural"
                name = Path(filename).stem
                out.append({
                    "name": name,
                    "kind": kind,
                    "source": code,
                    "stream": subpath,
                })
        except Exception:
            continue
        if out:
            break
    return out


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def has_macros(path: Path) -> bool:
    return len(extract_modules(path)) > 0


def all_sources(modules: List[Dict[str, Any]]) -> str:
    return "\n".join(m["source"] for m in modules)
