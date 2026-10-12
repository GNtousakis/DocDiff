"""Build dist/DocDiff.exe (one-file, windowed) with PyInstaller. Run on Windows."""
from __future__ import annotations

import sys
from pathlib import Path

import PyInstaller.__main__

ROOT = Path(__file__).resolve().parent.parent

# pywinrt projections are native extension modules in a namespace package: collect everything.
WINRT_PACKAGES = [
    "winrt",
    "winrt.system",
    "winrt.windows.foundation",
    "winrt.windows.foundation.collections",
    "winrt.windows.globalization",
    "winrt.windows.graphics.imaging",
    "winrt.windows.media.ocr",
    "winrt.windows.storage.streams",
]


def main() -> None:
    args = [
        str(ROOT / "run_docdiff.py"),
        "--name", "DocDiff",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"),
        "--collect-submodules", "docdiff",
        "--add-data", f"{ROOT / 'docdiff' / 'fixtures'};docdiff/fixtures",
        "--exclude-module", "tkinter",
    ]
    if sys.platform == "win32":
        for pkg in WINRT_PACKAGES:
            args += ["--collect-all", pkg, "--hidden-import", pkg]
    PyInstaller.__main__.run(args)


if __name__ == "__main__":
    main()
