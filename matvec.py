from skeleton import parse_str as parse_skeleton
from pattern import parse_str as parse_pattern
from instance import create_instance, VariableMap
from skeleton_ast import populate
from random import choice
from codelet_generator import generate_codelet
from populator import Populator, IncrementalChoice

matvec_code = """
declare A[];
declare B[][];
declare C[];

for [i, j] {
  A[`x:index`] = A[`x:index`] + B[`x:index`][`y:index`] * C[`y:index`];
}
"""

def set_exact_loop_bounds(var_map, loop_var, min_val, max_val):
    lower_bound = f'{loop_var}_greater_eq'
    var_map.set_min(lower_bound, min_val)
    var_map.set_max(lower_bound, min_val)
    upper_bound = f'{loop_var}_less_eq'
    var_map.set_min(upper_bound, max_val)
    var_map.set_max(upper_bound, max_val)
    
def generate(arrays, indices):
    # skeleton
    skeleton = parse_skeleton(matvec_code)
    print(skeleton.pprint())

    # pattern
    index_choice = IncrementalChoice()

    populator = Populator()
    populator.add('index', indices.order, choice_function=index_choice.choice)

    maybe_pattern = populate(skeleton, populator.populate)
    maybe_pattern_code = maybe_pattern.pprint()
    pattern = parse_pattern(maybe_pattern_code)
    print(pattern.pprint())

    # instance
    var_map = VariableMap()
    for loop_var in ['i', 'j']:
        set_exact_loop_bounds(var_map, loop_var, 0, 849)

    instance = create_instance(pattern, var_map)
    print(instance.pprint())
    print(instance.pattern.cprint())

    # C code generation
    application = 'LoopGen'
    batch = 'matvec'
    code_prefix = f'V{indices.name}{arrays.name}'
    code = f'{code_prefix}.c'
    codelet = f'{code_prefix}850.c_de'
    n_iterations = 10
    generate_codelet(application, batch, code, codelet, n_iterations, instance)

from dataclasses import dataclass

@dataclass
class Pool:
    order: list
    name: str

index_pools = [
    Pool(['i', 'j'], '1'),
    Pool(['j', 'i'], 'L')
]
array_pools = [
    Pool([], 'aba'),
    Pool([], 'abc'),
]

for indices in index_pools:
    for arrays in array_pools:
        generate(arrays, indices)

