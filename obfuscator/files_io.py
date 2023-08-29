import logging
import os
import pathlib
import shutil
import tempfile
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


def rewrite_file(orig_file: pathlib.Path, dst_dir: str, hashed_symbol_table: Dict[str, str]):
    """Rewrite the file with the hashed symbol table."""

    with open(orig_file) as code_file:
        lines = code_file.readlines()

    for line_number, line in enumerate(lines, 0):
        for orig_name, new_name in hashed_symbol_table.items():
            if orig_name in line:
                lines[line_number] = lines[line_number].replace(orig_name, new_name)

    dst_file = pathlib.Path(dst_dir) / orig_file.name
    with open(dst_file, "w") as code_file:
        code_file.writelines(lines)
        logger.info(f"Rewrote {orig_file} to {dst_file}")


def prepare_source_files(dirs: pathlib.Path, tmp_location: pathlib.Path = None) -> Path:
    """Copy the source files to a temporary directory and run clang-format on them.

    Args:
        dirs (pathlib.Path): The source directory.
        tmp_location (pathlib.Path, optional): The temporary directory. Defaults to None.

    Returns:
        The temporary directory.

    """
    if tmp_location is None:
        tmp_location = tempfile.TemporaryDirectory().name
        logger.info(f"Created temporary directory {tmp_location}")

    os.makedirs(tmp_location, exist_ok=True)

    shutil.copytree(dirs, tmp_location, dirs_exist_ok=True)
    logger.info(f"Copied {dirs} to {tmp_location}")

    # Run clang-format on the files in tmp_location.
    os.system(f"clang-format -style=google -i {tmp_location}/*")

    return pathlib.Path(tmp_location)
