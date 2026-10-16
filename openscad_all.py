#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["typer"]
# ///

import os
import shutil
import subprocess
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Annotated

import typer

OPENSCAD = shutil.which("openscad-nightly") or shutil.which("openscad") or "openscad"


def render(scad_file: Path) -> None:
    stem = scad_file.with_suffix("")
    cmd = [OPENSCAD, "-o", f"{stem}.png", "-o", f"{stem}.stl", str(scad_file)]
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


def main(
    dir: Annotated[
        Path, typer.Argument(help="Directory to search for .scad files")
    ] = Path("."),
) -> None:
    scad_files = sorted(dir.rglob("*.scad"))
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
        list(pool.map(render, scad_files))


if __name__ == "__main__":
    typer.run(main)
