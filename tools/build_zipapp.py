#!/usr/bin/env python3
"""Build the dependency-free single-file ZipApp."""
from __future__ import annotations

import argparse
import shutil
import tempfile
import zipapp
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "DIKWP_MINEX_FABRIC_OS.pyz")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="minex-zipapp-") as td:
        stage = Path(td)
        shutil.copytree(ROOT / "src" / "minex_fabric", stage / "minex_fabric")
        (stage / "__main__.py").write_text(
            "from minex_fabric.cli import main\nraise SystemExit(main())\n",
            encoding="utf-8",
        )
        zipapp.create_archive(
            stage,
            target=args.output,
            interpreter="/usr/bin/env python3",
            compressed=True,
        )
    args.output.chmod(0o755)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
