from skeleton import parse_str as parse_skeleton
from pattern import parse_str as parse_pattern
from instance import create_instance, VariableMap
from skeleton_ast import populate
from random import choice
from codelet_generator import generate_codelet
from populator import Populator

skeleton_code = """
declare A[][];
declare B[][];
declare C[][];

for [i, j, k] {
  `_`[i][j] = `_`[i][j] + `_`[i][k] * `_`[k][j];
}
"""

# skeleton
skeleton = parse_skeleton(skeleton_code)
print(skeleton.pprint())

# pattern
populator = Populator(['A', 'B', 'C'])
maybe_pattern = populate(skeleton, populator.populate)
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
