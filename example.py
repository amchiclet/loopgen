from pattern import parse_str, parse_stmt_str, parse_expr_str
from instance import try_create_instance
from constant_assignment import VariableMap
from type_assignment import TypeAssignment
from codegen.c_generator import generate_code
from populator import PopulateParameters, populate_stmt, populate_expr, populate_op, populate_name, ChoiceRecorder
from random import randint, seed
from pathlib import Path

# seed(0)

# Prepare skeleton

skeleton_code = """
declare I;
declare J;
declare A[][J];
declare B[I][];
declare C[][];

for [(i, >=#_:low#, <=#_:high#), (j, >=#_:low#, <=#_:high#)] {
  $_$
  $_$
  $_:s1$
  $_:s1$
  $_:s2$
  $_:s2$
}
"""

skeleton = parse_str(skeleton_code)
print(skeleton.pprint())

# Fill in the skeleton holes

def populate_stmts(node):
    s1 = [parse_stmt_str(s) for s in ['A[i][j] = A[i][j] + 5.0;',
                                      'B[i][j] = B[i][j] + 5.0;',
                                      'C[i][j] = C[i][j] + 5.0;']]
    s2 = [parse_stmt_str(s) for s in ['A[i][j] = B[i][j] + C[i][j];',
                                      'B[i][j] = A[i][j] + C[i][j];',
                                      'C[i][j] = A[i][j] + B[i][j];']]
    params = PopulateParameters(s1 + s2)
    params.add('s1', s1)
    params.add('s2', s2)

    return populate_stmt(skeleton, params.populate)

skeleton = populate_stmts(skeleton)
print(skeleton.pprint())

def populate_exprs(skeleton):
    def populate(node):
        if node.family_name == 'low':
            return parse_expr_str(str(randint(0, 500)))
        elif node.family_name == 'high':
            return parse_expr_str(str(randint(500, 1000)))
        else:
            return parse_expr_str(str(randint(0, 1000)))
    return populate_expr(skeleton, populate)

skeleton = populate_exprs(skeleton)
print(skeleton.pprint())

# Create an instance

var_map = VariableMap(default_min=0, default_max=1000)
var_map.set_value('I', 800)
var_map.set_value('J', 1100)

types = TypeAssignment(default_types=['int'])
types.set('A', 'double')
types.set('B', 'double')
types.set('C', 'double')

instance = try_create_instance(skeleton, var_map, types)
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
