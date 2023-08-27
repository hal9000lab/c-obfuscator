import logging
import pathlib
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
