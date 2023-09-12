import dataclasses
import pathlib
from enum import Enum
from typing import Optional, Dict, List

from obfuscator.symbol_encoder import encode_name


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
    return_type: Optional[str]
    line: int
    class_name: Optional[str] = None

    @property
    def names(self) -> set[str]:
        if self.type == SymbolType.CLASS_NAME:
            return {f"class {self._name}", f"{self._name}::", f"public {self._name}", f"{self._name}", f"~{self._name}"}
        return {self._name}

    @property
    def hash_names(self) -> Dict[str, str]:
        if self.type == SymbolType.CLASS_NAME:
            return {
                f"class {self._name}": f"class {encode_name(self._name)}",
                f"{self._name}::": f"{encode_name(self._name)}::",
                f"public {self._name}": f"public {encode_name(self._name)}",
                f"{self._name}": f"{encode_name(self._name)}",
                f"~{self._name}": f"~{encode_name(self._name)}"
            }
        return {self._name: encode_name(self._name)}


@dataclasses.dataclass
class SymbolTable:
    file_path: pathlib.Path
    symbols: List[Symbol]
    header_file: bool = False
