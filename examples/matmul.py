from skeleton import parse_str as parse_skeleton
from skeleton_ast import Var
from pattern import parse_str as parse_pattern
from populator import PopulateParameters, populate_name

matmul_code = """
declare A[][];
declare B[][];
declare C[][];

for [i, j, k] {
  A[`x:index`][`y:index`] =
      A[`x:index`][`y:index`] +
      `_:array`[`x:index`][k] * `_:array`[k][`y:index`];
}
"""

skeleton = parse_skeleton(matmul_code)
print(skeleton.pprint())

array_choices = [Var('A'), Var('B'), Var('C')]
index_choices = [Var('i'), Var('j')]

populator = PopulateParameters()
populator.add('array', array_choices)
populator.add('index', index_choices)

maybe_pattern = populate_name(skeleton.clone(), populator.populate)
maybe_pattern_code = maybe_pattern.pprint()
pattern = parse_pattern(maybe_pattern_code)
print(pattern.pprint())

