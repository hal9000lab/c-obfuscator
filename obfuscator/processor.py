import logging
import logging
import pathlib
import re
from typing import List, Dict

from obfuscator.parser import re_c_function, re_static_variable, re_const_variable, re_cpp_class_name, \
    re_cpp_class_name_derived, re_cpp_class_method_override
from obfuscator.symbol import LineContextType, SymbolTable, Symbol, SymbolType

logger = logging.getLogger(__name__)


def process_c_code(file_path: pathlib.Path, lines: List[str]) -> SymbolTable:
    # Get the symbol table from the C code
    symbols = []

    line_context: LineContextType = LineContextType.GLOBAL_VARIABLE
    is_header_file = file_path.suffix in [".h", ".hpp"]

    last_symbol = None

    for line_number, line in enumerate(lines, 1):
        line_strip = line.strip()
        # Ignore comments
        if line_strip.startswith("//") or line_strip.startswith("/*") or line_strip.startswith(
                "*") or line_strip.startswith("#"):
            continue

        parsed_symbols = []

        if (groups := re_c_function.match(line_strip)) or (groups := re_cpp_class_method_override.match(line_strip)):
            parsed_symbols = [Symbol(
                _name=groups.group("func_name"),
                type=SymbolType.FUNCTION,
                return_type=None,
                line=line_number,
                class_name=None
            )]
            line_context = LineContextType.FUNCTION_DEFINITION
        elif groups := re_static_variable.match(line):
            parsed_symbols = [Symbol(
                _name=groups.group("var_name"),
                type=SymbolType.STATIC_VARIABLE,
                line=line_number,
                class_name=None,
                return_type=groups.group("var_type")
            )]
        elif groups := re_const_variable.match(line):
            parsed_symbols = [Symbol(
                _name=groups.group("var_name"),
                type=SymbolType.CONST_VARIABLE,
                line=line_number,
                class_name=None,
                return_type=groups.group("var_type")
            )]
        elif groups := re_cpp_class_name.match(line):
            parsed_symbols = [
                Symbol(
                    _name=groups.group("class_name"),
                    type=SymbolType.CLASS_NAME,
                    line=line_number,
                    class_name=None,
                    return_type=None
                )]
        elif groups := re_cpp_class_name_derived.match(line):
            parsed_symbols = [
                Symbol(
                    _name=groups.group("class_name"),
                    type=SymbolType.CLASS_NAME,
                    line=line_number,
                    class_name=None,
                    return_type=None
                )]

        if parsed_symbols:
            symbols.extend(parsed_symbols)
            last_symbol = parsed_symbols[:]
            parsed_symbols = []

    symbol_table = SymbolTable(file_path, symbols, header_file=is_header_file)
    return symbol_table


def _find_duplicates(symbols_tables: List[SymbolTable]) -> set[str]:
    """Find duplicate symbols in the symbol tables

    Args:
        symbols_tables (List[SymbolTable]): [description]

    Returns:
        List[str]: list of duplicated symbols
    """
    # Find duplicate symbols
    symbols = []
    for symbol_table in symbols_tables:
        # Ignore duplicates in header files
        if symbol_table.header_file:
            continue
        for symbol in symbol_table.symbols:
            symbols.extend(symbol.names)

    duplicates = []
    for symbol in symbols:
        if symbols.count(symbol) > 1:
            duplicates.append(symbol)

    return set(duplicates)


def hash_symbols(symbol_tables: List[SymbolTable], ignore_files: List[str] = None) -> dict[str, str]:
    """Hash the symbols in the symbol tables

    Args:
        symbol_tables (List[SymbolTable]): [description]
        ignore_files (List[str], optional): [description]. Defaults to None.

    Returns:
        Dict[str, str]: [description]
    """

    if ignore_files is None:
        ignore_files = []
    global_hashed_symbol_table: Dict[str, str] = {}
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
                if symbol.names.intersection(duplicates):
                    logger.warning(f"Duplicated symbol {symbol.names} found in {symbol_table.file_path} - ignore")
                    continue
                global_hashed_symbol_table.update(symbol.hash_names)
            elif symbol.type == SymbolType.STATIC_VARIABLE:
                global_hashed_symbol_table.update(symbol.hash_names)
            elif symbol.type == SymbolType.CONST_VARIABLE:
                global_hashed_symbol_table.update(symbol.hash_names)
            elif symbol.type in [SymbolType.CLASS_NAME, SymbolType.CLASS_IDENTITY]:
                global_hashed_symbol_table.update(symbol.hash_names)

    global_hashed_symbol_table = {
        re.compile(f"\\b{key}\\b"): value for key, value in global_hashed_symbol_table.items()}

    return global_hashed_symbol_table
