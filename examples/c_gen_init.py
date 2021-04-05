from pattern import parse_str as parse_pattern
from instance import create_instance
from constant_assignment import VariableMap
from type_assignment import TypeAssignment
from codegen.c_generator import generate_code

code = """
declare A[][];
declare B[][];
declare n;
declare m;

for [(i, >=0, <=n), (j, >=0, <= m)] {
  A[i][j] = B[i][j] + 5;
}
"""

pattern = parse_pattern(code)
print(pattern.pprint())

size = 100

# Set possible values for n and m.
# We need to do this because n and m are used as loop bounds
# and they determine how much space to allocate arrays with.
var_map = VariableMap()
var_map.set_value('n', size-1)
var_map.set_value('m', size-1)

# Specify variable types
types = TypeAssignment()
types.set('A', 'float')
types.set('B', 'float')
types.set('n', 'int')
types.set('m', 'int')

instance = create_instance(pattern, var_map, types=types)
print(instance.pprint())

# Config how values are initialized
init_value_map = VariableMap()
init_value_map.set_range('A', 0.0, 1.0)
init_value_map.set_range('B', 0.0, 1.0)
init_value_map.set_value('n', size-1)
init_value_map.set_value('m', size-1)

# Generate code
generate_code('my_output_dir', instance, init_value_map)
