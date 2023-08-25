import argparse
import os
import logging
import pathlib
import re

import pycparser
import clang.cindex

from obfuscator import processor

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger()


def _args():
    parser = argparse.ArgumentParser()
    parser.add_argument("location", help="Location of the file to be processed")
    parser.add_argument("output", help="Location of the output files")
    parser.add_argument("--ignore-file", nargs="*", help="Ignore file")

    return parser.parse_args()


def main():
    args = _args()

    dirs = pathlib.Path(args.location)

    ignore_dir_names = re.compile(
        r".*(build|\.git|\.vscode|\.idea|\.pytest_cache|__pycache__|cmake).*"
    )

    # Scan to get the symbol table.
    symbol_tables = []
    for file_path in dirs.glob("**/*.cpp"):
        if ignore_dir_names.match(str(file_path)) is not None:
            continue

        with open(file_path) as code_file:
            symbol_table = processor.process_c_code(file_path, code_file.readlines())
            symbol_tables.append(symbol_table)

    logger.info(f"Loaded {len(symbol_tables)} symbol tables.")
    hashed_symbols = processor.hash_symbols(symbol_tables)


if __name__ == "__main__":
    main()
