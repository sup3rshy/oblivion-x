"""OOXML packaging: assemble .docm/.xlsm files from skeleton parts +
generated vbaProject.bin."""
from __future__ import annotations

import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

from oblivionx import resources_dir
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
    skeleton = zipfile.ZipFile(_SKELETONS[fmt])
    target = _VBA_TARGET[fmt]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for name in skeleton.namelist():
            zout.writestr(name, skeleton.read(name))
        zout.writestr(target, vba_bin)
    skeleton.close()
