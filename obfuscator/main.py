import argparse
import logging
import os
import pathlib
import random
import re
import shutil

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

    parser.add_argument("--extra-file", action='append', help="Extra file to be rewritten")

    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    return parser.parse_args()


def main():
    args = _args()

    random.seed(args.seed)

    src_dir = files_io.prepare_source_files(args.location, args.tmp)

    ignore_dir_names = re.compile(
        r".*(build|\.git|\.vscode|\.idea|\.pytest_cache|__pycache__|cmake).*"
    )

    src_files = [file_path for ext in [".cpp", ".h"] for file_path in src_dir.glob(f"**/*{ext}")]
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

    if args.output:
        os.makedirs(args.output, exist_ok=True)

        if args.clean_output and os.path.exists(args.output) and args.output not in [".", "/"]:
            shutil.rmtree(args.output)

    # Rewrite the files.
    logger.info(f"Extra files: {args.extra_file}")
    all_files = src_files + [pathlib.Path(file_path) for file_path in args.extra_file]
    for file_path in all_files:
        if ignore_dir_names.match(str(file_path)) is not None:
            continue

        files_io.rewrite_file(file_path, args.output, hashed_symbols, args.inplace)

    if args.inplace:
        logger.info(f"Rewrote {args.location} inplace.")
        for src_file in src_files:
            shutil.copy(src_file, args.location)


if __name__ == "__main__":
    main()
