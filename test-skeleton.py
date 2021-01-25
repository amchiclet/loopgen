from skeleton import parse_str as parse_skeleton
from pattern import parse_str as parse_pattern
from instance import create_instance, VariableMap

from skeleton_ast import populate
from random import choice

skeleton_code = """
declare A[][];
declare B[][];
declare C[][];

for [i, j, k] {
  C[i][j] = C[i][j] + `_`[i][k] * `_`[k][j];
}
"""

def generate_codelet_conf(codelet):
    return (f'<?xml version="1.0" ?>\n'
            f'<codelet>\n'
            f'  <language value="C"/>\n'
            f'  <label name="{codelet}"/>\n'
            f'  <function name="codelet"/>\n'
            f'  <binary name="wrapper"/>\n'
            f'</codelet>\n')

def generate_codelet_meta(batch, code, codelet):
    return (f'application name=LoopGen'
            f'batch name={batch}'
            f'code name={code}'
            f'codelet name={codelet}')

class MatmulPopulator:
    def populate(self, hole_name):
        if hole_name == '`_`':
            return choice(['A', 'B'])
        assert(False)

skeleton = parse_skeleton(skeleton_code)
print(skeleton.pprint())
matmul_populator = MatmulPopulator()
maybe_pattern = populate(skeleton, matmul_populator.populate)
maybe_pattern_code = maybe_pattern.pprint()
pattern = parse_pattern(maybe_pattern_code)
print(pattern.pprint())
var_map = VariableMap()
instance = create_instance(pattern, var_map)
print(instance.pprint())
print(instance.pattern.cprint())
