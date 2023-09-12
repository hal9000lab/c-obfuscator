import argparse
import logging
import os
import pathlib
import random
import re
import shutil
from typing import List

from obfuscator import processor, files_io

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger()


def _args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--location", help="Location of the file to be processed", required=True)
    parser.add_argument("--output", help="Location of the output files")
    parser.add_argument("--inplace", action="store_true", help="Rewrite the file inplace")
    parser.add_argument("--ignore-file", nargs="*", help="Ignore file")
    parser.add_argument("--tmp", default=None, help="Temporary directory")
    parser.add_argument("--clean-output", action="store_true", help="Clean the output directory")

    parser.add_argument("--extra-file", action='append', help="Extra file to be rewritten", default=[])

    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    return parser.parse_args()


def main_cmd(location: str,
             output: str,
             inplace: bool,
             seed: int,
             ignore_files: List[str],
             tmp: str,
             clean_output: bool,
             extra_file: List[str]):
    random.seed(seed)

    src_dir = files_io.prepare_source_files(location, tmp)

    ignore_dir_names = re.compile(
        r".*(build|\.git|\.vscode|\.idea|\.pytest_cache|__pycache__|cmake).*"
    )

    src_files = [
        file_path for ext in [".cpp", ".h"] for file_path in src_dir.glob(f"**/*{ext}")
    ]
    # Scan to get the symbol table.
    symbol_tables = []
    for file_path in src_files:
        if ignore_dir_names.match(str(file_path)) is not None:
            continue

        with open(file_path) as code_file:
            symbol_table = processor.process_c_code(file_path, code_file.readlines())
            symbol_tables.append(symbol_table)

    logger.info(f"Loaded {len(symbol_tables)} symbol tables.")
    hashed_symbols = processor.hash_symbols(symbol_tables)

    # For debug, save hashed symbols
    with open("hashed_symbols.txt", "w") as f:
        for key, value in hashed_symbols.items():
            f.write(f"{key} {value}\n")

    if output:
        os.makedirs(output, exist_ok=True)

        if (
            clean_output
            and os.path.exists(output)
            and output not in [".", "/"]
        ):
            shutil.rmtree(output)

    # Rewrite the files.
    logger.info(f"Extra files: {extra_file}")
    all_files = src_files + [pathlib.Path(file_path) for file_path in extra_file]
    for file_path in all_files:
        if ignore_dir_names.match(str(file_path)) is not None:
            continue

        if ignore_files and file_path.name in ignore_files:
            logger.info(f"Ignoring file {file_path}")
            continue

        files_io.rewrite_file(file_path, output, hashed_symbols, inplace)

    if inplace:
        logger.info(f"Rewrote {location} inplace.")
        for src_file in src_files:
            shutil.copy(src_file, location)


def main():
    args = _args()
    main_cmd(args.location, args.output, args.inplace, args.seed, args.ignore_file, args.tmp, args.clean_output, args.extra_file)


if __name__ == "__main__":
    main()
