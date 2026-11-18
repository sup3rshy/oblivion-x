"""OOXML packaging: assemble .docm/.xlsm files from skeleton parts +
generated vbaProject.bin.

``package_office_file`` builds a single file; ``build_corpus_files`` turns a
generated corpus (manifest + ``sources/``) into the actual Office files on
any platform. Files produced this way contain valid MS-OVBA projects and are
readable by oletools; they are intended for the static-only workflow. The
Windows COM builder remains authoritative for files that must execute in
Office."""
from __future__ import annotations

import time
import uuid
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from oblivionx import resources_dir
from oblivionx.common import read_json, write_json
from oblivionx.corpus.msovba import build_vba_project_bin

_RES = Path(resources_dir)
_SKELETONS = {
    "docm": _RES / "docm_skeleton.zip",
    "xlsm": _RES / "xlsm_skeleton.zip",
}
_VBA_TARGET = {
    "docm": "word/vbaProject.bin",
    "xlsm": "xl/vbaProject.bin",
}


def package_office_file(modules: List[Tuple[str, str, str]],
                        fmt: str,
                        out_path: Path,
                        project_name: Optional[str] = None,
                        project_id: Optional[str] = None) -> None:
    """Build a .docm/.xlsm file with the given VBA modules.

    modules: list of (module_name, kind, vba_source) where kind is
    'document' (ThisDocument/ThisWorkbook) or 'procedural'.
    fmt: 'docm' or 'xlsm'.
    """
    host = "word" if fmt == "docm" else "excel"
    vba_bin = build_vba_project_bin(modules, host=host,
                                    project_name=project_name,
                                    project_id=project_id)
    target = _VBA_TARGET[fmt]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Fixed timestamps make the generated corpus byte-for-byte reproducible;
    # zipfile otherwise stamps every entry with the current local time.
    fixed_time = (2024, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(_SKELETONS[fmt]) as skeleton:
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for name in skeleton.namelist():
                info = zipfile.ZipInfo(name, date_time=fixed_time)
                info.compress_type = zipfile.ZIP_DEFLATED
                zout.writestr(info, skeleton.read(name))
            info = zipfile.ZipInfo(target, date_time=fixed_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            zout.writestr(info, vba_bin)


def build_corpus_files(corpus_dir: Path,
                       samples_dir: Optional[Path] = None,
                       overwrite: bool = False,
                       progress: bool = True) -> Dict[str, Any]:
    """Package every manifest entry into ``<samples_dir>/<id>.<format>``.

    This is the Linux/offline equivalent of ``build_corpus_windows.ps1``.
    Existing files are skipped unless ``overwrite`` is true, so a corpus
    authored with Word/Excel COM is never clobbered accidentally.
    """
    corpus_dir = Path(corpus_dir)
    samples_dir = Path(samples_dir) if samples_dir else corpus_dir / "samples"
    manifest = read_json(corpus_dir / "manifest.json")["samples"]
    samples_dir.mkdir(parents=True, exist_ok=True)
    report: List[Dict[str, Any]] = []
    built = skipped = failed = 0
    for i, m in enumerate(manifest):
        sid = m["id"]
        out_path = samples_dir / f"{sid}.{m['format']}"
        t0 = time.time()
        if out_path.exists() and not overwrite:
            skipped += 1
            report.append({"id": sid, "status": "skipped",
                           "time_ms": 0, "error": "file already exists"})
            continue
        try:
            doc_src = (corpus_dir / "sources" / m["doc_source"]).read_text(
                encoding="latin-1")
            helper_src = (corpus_dir / "sources" / m["helper_source"]).read_text(
                encoding="latin-1")
            # Stable project ID so repeated builds are byte-identical.
            project_id = "{%s}" % uuid.uuid5(uuid.NAMESPACE_URL,
                                             f"oblivionx:{sid}")
            modules = [(m["doc_module"], "document", doc_src)]
            if m["format"] == "xlsm":
                # Real Excel workbooks carry a worksheet module in addition
                # to ThisWorkbook; match that structure so the offline
                # corpus yields the same module counts as the COM builder.
                modules.append(("Sheet1", "document",
                                'Attribute VB_Name = "Sheet1"\r\n'))
            modules.append(("NewMacros", "procedural", helper_src))
            package_office_file(modules, m["format"], out_path,
                                project_id=project_id)
            built += 1
            report.append({"id": sid, "status": "ok",
                           "time_ms": round((time.time() - t0) * 1000),
                           "error": ""})
        except Exception as exc:  # keep going; report the failing sample
            failed += 1
            report.append({"id": sid, "status": "error",
                           "time_ms": round((time.time() - t0) * 1000),
                           "error": str(exc)})
        if progress and (i + 1) % 50 == 0:
            print(f"  corpus build: {i + 1}/{len(manifest)}")
    write_json(report, samples_dir / "build_report.json")
    return {"out_dir": str(samples_dir), "n_samples": len(manifest),
            "n_built": built, "n_skipped": skipped, "n_failed": failed}
