import base64
import copy
import dataclasses
import hashlib
import pathlib
import random
import re
import logging
from hashlib import sha256
from typing import List, Optional, Dict

import pycparser

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Symbol:
    name: str
    type: str
    return_type: str
    line: int
    class_name: Optional[str] = None


@dataclasses.dataclass
class SymbolTable:
    file_path: pathlib.Path
    symbols: List[Symbol]


# Regular expression for matching C function and extract function name
re_c_function = re.compile(r"^\w+\s+(\w+)\(.*\)\s*{?.*")

# Regular expression for extracting C function name with the return type
# re_c_function_with_return_type = re.compile(r"^\w+\s+(\w+)\(.*\)\s*{?.*")

# Regular expression for matching C++ class method and extract method name
re_cpp_method = re.compile(r"^\w+\s+(\w+)::(\w+)\(.*\)\s*{.*")


def process_c_code(file_path: pathlib.Path, lines: List[str]) -> SymbolTable:
    # Get the symbol table from the C code
    symbols = []

    in_class_definition = False

    for line_number, line in enumerate(lines, 1):
        # For now, let's ignore class definition.
        if line.strip().startswith("class"):
            in_class_definition = True
            continue
        if in_class_definition:
            if line.strip().startswith("};"):
                in_class_definition = False
            continue

        if re_c_function.match(line) is not None:
            groups = re_c_function.findall(line.strip())
            symbol = Symbol(
                name=groups[0],
                type="function",
                return_type=None,
                line=line_number,
                class_name=None
            )
            symbols.append(symbol)
        elif re_cpp_method.match(line) is not None:
            groups = re_cpp_method.findall(line.strip())[0]
            symbol = Symbol(
                name=groups[1],
                type="method",
                line=line_number,
                class_name=groups[0],
                return_type=None
            )
            symbols.append(symbol)

    symbol_table = SymbolTable(file_path, symbols)
    return symbol_table


def _find_duplicates(symbold_tables: List[SymbolTable]) -> List[str]:
    # Find duplicate symbols
    symbols = []
    for symbol_table in symbold_tables:
        for symbol in symbol_table.symbols:
            symbols.append(symbol.name)

    duplicates = []
    for symbol in symbols:
        if symbols.count(symbol) > 1:
            duplicates.append(symbol)

    return duplicates


def hash_symbols(symbol_tables: List[SymbolTable], ignore_files: List[str] = None) -> Dict[str, str]:
    if ignore_files is None:
        ignore_files = []
    global_hashed_symbol_table = {}
    duplicates = _find_duplicates(symbol_tables)
    for symbol_table in symbol_tables:
        for ignore_file in ignore_files:
            if ignore_file in str(symbol_table.file_path):
                continue
        for symbol in symbol_table.symbols:
            if symbol.type == "function":
                new_name = base64.b32encode(sha256(symbol.name.encode()).digest()).rstrip(b"=").decode().lower()
                if ord('0') <= ord(new_name[0]) <= ord('9'):
                    new_name = chr(random.randint(97, 122)) + new_name[1:]

                if symbol.name in duplicates:
                    logger.warning(f"Duplicated symbol {symbol.name} found in {symbol_table.file_path} - ignore")
                    continue

                global_hashed_symbol_table[symbol.name] = new_name

    return global_hashed_symbol_table


def rewrite_file(orig_file: pathlib.Path, dst_dir: str, hashed_symbol_table: Dict[str, str]):
    with open(orig_file) as code_file:
        lines = code_file.readlines()

    for line_number, line in enumerate(lines, 0):
        for orig_name, new_name in hashed_symbol_table.items():
            if orig_name in line:
                lines[line_number] = line.replace(orig_name, new_name)

    dst_file = pathlib.Path(dst_dir) / orig_file.name
    with open(dst_file, "w") as code_file:
        code_file.writelines(lines)
        logger.info(f"Rewrote {orig_file} to {dst_file}")