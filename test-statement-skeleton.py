from skeleton import parse_str as parse_skeleton
from skeleton import parse_stmt_str as parse_statement

from pattern import parse_str as parse_pattern
from instance import create_instance, VariableMap
from skeleton_ast import replace, Literal
from random import choice
from codelet_generator import generate_codelet
from populator import Populator

skeleton_code = """
declare A[][];
declare B[][];
declare C[][];

for [i, j, k] {
  $_:stmts1$
  $_:stmts2$
}
"""

stmt1_code = """
  A[i][j] = A[i][j] + B[j][k];
"""

stmt2_code = """
  A[i][j] = B[i][j] + B[j][k];
"""

stmt3_code = """
  A[i][j] = B[i][j] + C[j][k];
"""

stmt1 = parse_statement(stmt1_code)

# skeleton
skeleton = parse_skeleton(skeleton_code)
print(skeleton.pprint())

# pattern
populator = Populator()
populator.add('stmts1', [Literal(int, 1)])
populator.add('stmts2', [Literal(int, 0)])
maybe_pattern = replace(skeleton, populator)
maybe_pattern_code = maybe_pattern.pprint()
pattern = parse_pattern(maybe_pattern_code)
print(pattern.pprint())

# instance
var_map = VariableMap()
instance = create_instance(pattern, var_map)
print(instance.pprint())
print(instance.pattern.cprint())

# C code generation
batch = 'mm_batch'
code = 'mm_code'
codelet = 'mm_codelet'
n_iterations = 5
generate_codelet(batch, code, codelet, n_iterations, instance)
