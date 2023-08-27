import base64
import dataclasses
import logging
import pathlib
import random
import re
from enum import Enum
from hashlib import sha256
from typing import List, Optional, Dict

from obfuscator.symbol_encoder import encode_name

logger = logging.getLogger(__name__)


class SymbolType(Enum):
    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    STATIC_VARIABLE = "static_variable"


@dataclasses.dataclass
class Symbol:
    name: str
    type: SymbolType
    return_type: str
    line: int
    class_name: Optional[str] = None


@dataclasses.dataclass
class SymbolTable:
    file_path: pathlib.Path
    symbols: List[Symbol]
    header_file: bool = False


# Regular expression for matching C function and extract function name
re_c_function = re.compile(r"^\w+\s+(?P<var_name>\w+)\(.*\)\s*{?.*")

# Regular expression for matching C++ class method and extract method name
re_cpp_method = re.compile(r"^\w+\s+(\w+)::(\w+)\(.*\)\s*{.*")

# Regular expression for matching static variable, like static bool updateBaseline
re_static_variable = re.compile(r"^static\s+(?P<var_type>[a-zA-Z0-9_ ]+)\s+(?P<var_name>\w+)\s*=?.*;.*")


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
                type=SymbolType.FUNCTION,
                return_type=None,
                line=line_number,
                class_name=None
            )
            symbols.append(symbol)
        elif re_cpp_method.match(line) is not None:
            groups = re_cpp_method.findall(line.strip())[0]
            symbol = Symbol(
                name=groups[1],
                type=SymbolType.METHOD,
                line=line_number,
                class_name=groups[0],
                return_type=None
            )
            symbols.append(symbol)
        elif re_static_variable.match(line) is not None:
            groups = re_static_variable.match(line.strip())
            symbol = Symbol(
                name=groups.group("var_name"),
                type=SymbolType.STATIC_VARIABLE,
                line=line_number,
                class_name=None,
                return_type=groups.group("var_type")
            )
            symbols.append(symbol)

    symbol_table = SymbolTable(file_path, symbols, header_file = file_path.suffix in [".h", ".hpp"])
    return symbol_table


def _find_duplicates(symbols_tables: List[SymbolTable]) -> List[str]:
    """Find duplicate symbols in the symbol tables

    Args:
        symbols_tables (List[SymbolTable]): [description]

    Returns:
        List[str]: list of duplicated symbols
    """
    # Find duplicate symbols
    symbols = []
    for symbol_table in symbols_tables:
        if symbol_table.header_file:
            continue
        for symbol in symbol_table.symbols:
            symbols.append(symbol.name)

    duplicates = []
    for symbol in symbols:
        if symbols.count(symbol) > 1:
            duplicates.append(symbol)

    return duplicates


def hash_symbols(symbol_tables: List[SymbolTable], ignore_files: List[str] = None) -> Dict[str, str]:
    """Hash the symbols in the symbol tables

    Args:
        symbol_tables (List[SymbolTable]): [description]
        ignore_files (List[str], optional): [description]. Defaults to None.

    Returns:
        Dict[str, str]: [description]
    """

    if ignore_files is None:
        ignore_files = []
    global_hashed_symbol_table = {}
    duplicates = _find_duplicates(symbol_tables)
    with open("duplicates.txt", "w") as f:
        for duplicate in duplicates:
            f.write(f"{duplicate}\n")

    for symbol_table in symbol_tables:
        for ignore_file in ignore_files:
            if ignore_file in str(symbol_table.file_path):
                continue
        for symbol in symbol_table.symbols:
            if symbol.type == SymbolType.FUNCTION:
                new_name = encode_name(symbol.name)

                if symbol.name in duplicates:
                    logger.warning(f"Duplicated symbol {symbol.name} found in {symbol_table.file_path} - ignore")
                    continue
                # logger.info(f"Hashed function name '{symbol.name}' to '{new_name}'")
                global_hashed_symbol_table[symbol.name] = new_name
            elif symbol.type == SymbolType.STATIC_VARIABLE:
                new_name = encode_name(symbol.name)
                if symbol.name in duplicates:
                    logger.warning(f"Duplicated symbol {symbol.name} found in {symbol_table.file_path} - ignore")
                    continue
                global_hashed_symbol_table[symbol.name] = new_name
                logger.info(f"Hashed static variable name '{symbol.name}' to '{new_name}' "
                            f"{symbol_table.file_path}:{symbol.line}")

    return global_hashed_symbol_table



