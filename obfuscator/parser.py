# Regular expression for matching C function and extract function name
import re

# C and C++ reserved keywords
reserved_keywords = {
    "auto", "break", "case", "char", "const", "continue", "default", "do", "double", "else", "enum", "extern", "float",
    "for", "goto", "if", "int", "long", "register", "return", "short", "signed", "sizeof", "static", "struct",
    "switch", "typedef", "union", "unsigned", "void", "volatile", "while", "asm", "bool", "catch", "class",
    "const_cast", "delete", "dynamic_cast", "explicit", "export", "false", "friend", "inline", "mutable", "namespace",
    "new", "operator", "private", "protected", "public", "reinterpret_cast", "static_cast", "template", "this",
    "throw", "true", "try", "typeid", "typename", "using", "virtual", "wchar_t", "alignas", "alignof", "char16_t",
    "char32_t", "constexpr", "decltype", "noexcept", "nullptr", "static_assert", "thread_local", "final", "override",
    "transaction_safe", "transaction_safe_dynamic", "import", "module", "co_await", "co_return", "co_yield"
}

re_c_function = re.compile(r"^(?P<func_type>\w+)\s+(?P<func_name>\w+)\(.*\)\s*{$")

re_c_function_def = re.compile(r"^(?P<func_type>\w+)\s+(?P<func_name>\w+)\(.*\);")

# Regular expression for matching C++ class method and extract method name
re_cpp_method = re.compile(r"^\w+\s+(?P<class_name>\w+)::(?P<method_name>\w+)\(.*\)\s*{.*")

# Regular expression for matching static variable, like static bool updateBaseline
re_static_variable = re.compile(r"^static\s+(?P<var_type>[a-zA-Z0-9_<> ]+)\s+\*?\s?(?P<var_name>\w+)\s?=?.*(;|{).*")

re_const_variable = re.compile(r"const\s+(?P<var_type>[a-zA-Z0-9_<> ]+)\s+(?P<var_name>\w+)\s*=?.*(;|{).*")

re_cpp_class_name = re.compile(r"^class\s+(?P<class_name>\w+)\s*{.*")