from skeleton import parse_str as parse_skeleton
from pattern import parse_str as parse_pattern
from instance import create_instance, VariableMap
from cgenerator import CGenerator

from skeleton_ast import populate
from random import choice

from pathlib import Path

skeleton_code = """
declare A[][];
declare B[][];
declare C[][];

for [i, j, k] {
  C[i][j] = C[i][j] + `_`[i][k] * `_`[k][j];
}
"""
    
def conf_contents(codelet):
    return (f'<?xml version="1.0" ?>\n'
            f'<codelet>\n'
            f'  <language value="C"/>\n'
            f'  <label name="{codelet}"/>\n'
            f'  <function name="codelet"/>\n'
            f'  <binary name="wrapper"/>\n'
            f'</codelet>\n')

def meta_contents(batch, code, codelet):
    return (f'application name=LoopGen\n'
            f'batch name={batch}\n'
            f'code name={code}\n'
            f'codelet name={codelet}\n')

def codelet_dir(batch, code, codelet, base='.'):
    return f'{base}/{batch}/{code}/{codelet}'

def meta_file(codelet_dir):
    return f'{codelet_dir}/codelet.meta'

def conf_file(codelet_dir):
    return f'{codelet_dir}/codelet.conf'

def generate_directories(batch, code, codelet, base='.'):
    path = Path(get_codelet_dir(batch, code, codelet, base))
    path.mkdir(parents=True, exist_ok=True)

class MatmulPopulator:
    def populate(self, hole_name):
        if hole_name == '`_`':
            return choice(['A', 'B'])
        assert(False)

def mm_contents():
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
    cgen = CGenerator(instance)
    print(cgen.core())
    print(cgen.main())
batch = 'mm_batch'
code = 'mm_code'
codelet = 'mm_codelet'

dst_dir = codelet_dir(batch, code, codelet)
Path(dst_dir).mkdir(parents=True, exist_ok=True)
Path(meta_file(dst_dir)).write_text(meta_contents(batch, code, codelet))
Path(conf_file(dst_dir)).write_text(conf_contents(codelet))

mm_contents()
