import dataclasses
import pathlib
import re
from typing import List, Optional

import pycparser


@dataclasses.dataclass
class Symbol:
    name: str
    type: str
    line: int
    class_name: Optional[str] = None


@dataclasses.dataclass
class SymbolTable:
    file_path: pathlib.Path
    symbols: List[Symbol]


# Regular expression for matching C function and extract function name
re_c_function = re.compile(r"^\w+\s+(\w+)\(.*\)\s*{?.*")

# Regular expression for matching C++ class method and extract method name
re_cpp_method = re.compile(r"^\w+\s+(\w+)::(\w+)\(.*\)\s*{.*")


def process_c_code(file_path: pathlib.Path, lines: List[str]) -> SymbolTable:
    # Get the symbol table from the C code
    symbols = []

    in_class_definition = False

    for line_number, line in enumerate(lines, 1):
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
                class_name=groups[0]
            )
            symbols.append(symbol)

    symbol_table = SymbolTable(file_path, symbols)
    return symbol_table
