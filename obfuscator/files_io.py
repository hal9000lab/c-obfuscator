import logging
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


def rewrite_file(orig_file: pathlib.Path, dst_dir: str, hashed_symbol_table: Dict[re.Pattern, str], inplace: bool = False):
    """Rewrite the file with the hashed symbol table."""

    with open(orig_file) as code_file:
        lines = code_file.readlines()

    for line_number, line in enumerate(lines, 0):
        if line.startswith("#"):  # ignore any directives
            continue
        for re_orig_name, new_name in hashed_symbol_table.items():
            if re_orig_name.search(line) is not None:
                lines[line_number] = re_orig_name.sub(new_name, lines[line_number])

    if inplace:
        dst_file = orig_file
    else:
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
    ret = subprocess.call(f"clang-format -style=file:obfuscator/clang-format.style -i {tmp_location}/*", shell=True)
    logger.info(f"clang-format ret code {ret}")
    if ret != 0:
        sys.exit(ret)


    return pathlib.Path(tmp_location)
