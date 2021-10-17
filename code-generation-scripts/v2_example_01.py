from pattern import (parse_str as parse_pattern,
                     parse_stmt_str as parse_stmt,
                     parse_expr_str as parse_expr)
from instance import try_create_instance
from constant_assignment import VariableMap
from type_assignment import TypeAssignment
from codegen.c_generator import generate_code
from populator import PopulateParameters, populate_stmt, populate_expr, populate_op, populate_name, ChoiceRecorder
from random import randint, seed
from pathlib import Path

seed(0)

# Prepare skeleton

skeleton_code = """
declare I;
declare J;
declare A[][J];
declare B[I][];
declare C[][];

for [(i, >=#_:low#, <=#_:high#), (j, >=#_:low#, <=#_:high#)] {
  C[i][j] = A[i][j] + B[i][j];
}
"""

skeleton = parse_pattern(skeleton_code)
print(skeleton.pprint())

# Fill in the skeleton holes

def populate_bounds(node):
    if node.family_name == 'low':
        return parse_expr(str(randint(0, 500)))
    elif node.family_name == 'high':
        return parse_expr(str(randint(500, 1000)))
    else:
        return parse_expr(str(randint(0, 1000)))

pattern = populate_expr(skeleton, populate_bounds)
print(pattern.pprint())

# Create an instance

var_map = VariableMap(default_min=0, default_max=1000)
var_map.set_value('I', 800)
var_map.set_value('J', 1100)

types = TypeAssignment(default_types=['int'])
types.set('A', 'double')
types.set('B', 'double')
types.set('C', 'double')

instance = try_create_instance(pattern, var_map, types)
print(instance.pprint())

# Code gen

init_value_map = {
    'A': 'drand(0.0, 1.0)',
    'B': 'drand(0.0, 1.0)',
    'C': 'drand(0.0, 1.0)',
    'I': '800',
    'J': '1100',
}

dst_dir = 'output-2021-10-17'
Path(dst_dir).mkdir(parents=True, exist_ok=True)
generate_code(dst_dir, instance, init_value_map=init_value_map, template_dir='codegen')
