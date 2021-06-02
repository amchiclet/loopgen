from pattern import parse_str as parse_pattern
from instance import create_instance
from constant_assignment import VariableMap
from type_assignment import TypeAssignment
from codegen.c_generator import generate_code
from codelet_generator import generate_codelet_full, name

code = """
declare A[n+1];
declare B[n+1];
declare x;
declare n;

for [(i, >=0, <=n)] {
  A[i] = (B[i] + x) * 0.5;
  x = B[i];
}
"""

pattern = parse_pattern(code)

size = 999999
var_map = VariableMap()
var_map.set_value('n', size)
var_map.set_value('m', size)

# Specify variable types
types = TypeAssignment()
types.set('A', 'double')
types.set('B', 'double')
types.set('x', 'double')
types.set('n', 'int')

instance = create_instance(pattern, var_map, types=types)
print(instance.pprint())

init_value_map = {
    'A': 'drand(0.0, 1.0)',
    'B': 'drand(0.0, 1.0)',
    'x': 'drand(0.0, 1.0)',
    'n': size,
}

generate_code('output-codegen', instance, init_value_map)
