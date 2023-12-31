import dataclasses
import logging
import pathlib
import re
from enum import Enum
from typing import List, Optional, Dict

from obfuscator.parser import re_c_function, re_static_variable, re_const_variable, re_cpp_class_name
from obfuscator.symbol_encoder import encode_name

logger = logging.getLogger(__name__)


class SymbolType(Enum):
    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    CLASS_NAME = "class_name"
    CLASS_IDENTITY = "class_identity"
    STATIC_VARIABLE = "static_variable"
    CONST_VARIABLE = "const_variable"


class LineContextType(Enum):
    CLASS_DEFINITION = "class_definition"
    CLASS_IMPLEMENTATION = "class_implementation"
    FUNCTION_DEFINITION = "function_definition"
    FUNCTION_IMPLEMENTATION = "function_implementation"
    STATIC_VARIABLE = "static_variable"
    GLOBAL_VARIABLE = "global_variable"


@dataclasses.dataclass
class Symbol:
    _name: str
    type: SymbolType
    return_type: str
    line: int
    class_name: Optional[str] = None

    @property
    def name(self):
        if self.type == SymbolType.CLASS_NAME:
            return f"class {self._name}"
        elif self.type == SymbolType.CLASS_IDENTITY:
            return f"{self._name}::"
        return self._name

    @property
    def hash_name(self):
        if self.type == SymbolType.CLASS_NAME:
            return f"class {encode_name(self._name)}"
        elif self.type == SymbolType.CLASS_IDENTITY:
            return f"{encode_name(self._name)}::"
        return encode_name(self._name)


@dataclasses.dataclass
class SymbolTable:
    file_path: pathlib.Path
    symbols: List[Symbol]
    header_file: bool = False


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

        # For now, let's ignore class definition.
        # if line_strip.startswith("class"):
        #     line_context = LineContextType.CLASS_DEFINITION
        #     continue
        # if line_context == LineContextType.CLASS_DEFINITION:
        #     if line_strip.startswith("};"):
        #         line_context = LineContextType.GLOBAL_VARIABLE
        #     continue
        #
        # if line_context == LineContextType.FUNCTION_DEFINITION:
        #     if line_strip.startswith("}"):
        #         line_context = LineContextType.GLOBAL_VARIABLE
        #     continue

        parsed_symbols = []

        if line_context == LineContextType.GLOBAL_VARIABLE:
            if groups := re_c_function.match(line_strip):
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
                parsed_symbols = [Symbol(
                    _name=groups.group("class_name"),
                    type=SymbolType.CLASS_NAME,
                    line=line_number,
                    class_name=None,
                    return_type=None
                ),
                    Symbol(
                        _name=groups.group("class_name"),
                        type=SymbolType.CLASS_IDENTITY,
                        line=line_number,
                        class_name=None,
                        return_type=None
                )]
                # line_context = LineContextType.CLASS_IMPLEMENTATION

        if parsed_symbols:
            symbols.extend(parsed_symbols)
            last_symbol = parsed_symbols[:]
            parsed_symbols = []

    symbol_table = SymbolTable(file_path, symbols, header_file=is_header_file)
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
        # Ignore duplicates in header files
        if symbol_table.header_file:
            continue
        for symbol in symbol_table.symbols:
            # Ignore duplicates of static variables
            # if symbol.typepe == SymbolType.STATIC_VARIABLE:
            #     continue
            symbols.append(symbol.name)

    duplicates = []
    for symbol in symbols:
        if symbols.count(symbol) > 1:
            duplicates.append(symbol)

    return duplicates


def hash_symbols(symbol_tables: List[SymbolTable], ignore_files: List[str] = None) -> Dict[re.Pattern, str]:
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
                if symbol.name in duplicates:
                    logger.warning(f"Duplicated symbol {symbol.name} found in {symbol_table.file_path} - ignore")
                    continue
                global_hashed_symbol_table[symbol.name] = symbol.hash_name
            elif symbol.type == SymbolType.STATIC_VARIABLE:
                new_name = symbol.hash_name
                global_hashed_symbol_table[symbol.name] = new_name
                logger.info(f"Hashed static variable name '{symbol.name}' to '{new_name}' "
                            f"{symbol_table.file_path}:{symbol.line}")
            elif symbol.type == SymbolType.CONST_VARIABLE:
                new_name = symbol.hash_name
                global_hashed_symbol_table[symbol.name] = new_name
                logger.info(f"Hashed const variable name '{symbol.name}' to '{new_name}' "
                            f"{symbol_table.file_path}:{symbol.line}")
            elif symbol.type in [SymbolType.CLASS_NAME, SymbolType.CLASS_IDENTITY]:
                new_name = symbol.hash_name
                global_hashed_symbol_table[symbol.name] = new_name
                logger.info(f"Hashed class name '{symbol.name}' to '{new_name}' "
                            f"{symbol_table.file_path}:{symbol.line}")

    global_hashed_symbol_table = {
        re.compile(f"\\b{key}\\b"): value for key, value in global_hashed_symbol_table.items()}

    return global_hashed_symbol_table
