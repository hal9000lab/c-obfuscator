import argparse
import logging
import pathlib
import re

from obfuscator import processor, file_io

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

    with open("hashed_symbols.txt", "w") as f:
        for key, value in hashed_symbols.items():
            f.write(f"{key} {value}\n")

    # Rewrite the files.
    src_files = [file_path for ext in [".cpp", ".h"] for file_path in dirs.glob(f"**/*{ext}")]
    for file_path in src_files:
        if ignore_dir_names.match(str(file_path)) is not None:
            continue

        file_io.rewrite_file(file_path, args.output, hashed_symbols)



if __name__ == "__main__":
    main()
