# Regular expression for matching C function and extract function name
import re

re_c_function = re.compile(r"^(?P<func_type>\w+)\s+(?P<func_name>\w+)\(.*\)\s*{$")

re_c_function_def = re.compile(r"^(?P<func_type>\w+)\s+(?P<func_name>\w+)\(.*\);")

# Regular expression for matching C++ class method and extract method name
re_cpp_method = re.compile(r"^\w+\s+(?P<class_name>\w+)::(?P<method_name>\w+)\(.*\)\s*{.*")

# Regular expression for matching static variable, like static bool updateBaseline
re_static_variable = re.compile(r"^static\s+(?P<var_type>[a-zA-Z0-9_<> ]+)\s+(?P<var_name>\w+)\s*=?.*(;|{).*")
