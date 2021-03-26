from skeleton import parse_str as parse_skeleton
from skeleton_ast import Var
from pattern import parse_str as parse_pattern
from populator import ChoiceFactoryEnumerator, PopulateParameters, populate_name

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

# To enumerate the total space, we need to know the size of the space
# For the matmul code above
#   A = A + _ * _
# we have two blanks to fill, and for each blank we have three
# choices: A, B, C.
#
# The space is then [3, 3]. To make array choices, we then pass [3, 3]
# to ChoiceFactoryEnumerator, so that it can generate the sampling
# functions such that each sampling function would pick the next
# combination deterministically.
array_choices = [Var('A'), Var('B'), Var('C')]
array_choice_space = [3, 3]

# For index choices, we want either something like A[i][j] or A[j][i],
# but not A[i][i] or A[j][j]. Basically, we are interested in the
# permutation of the possible choices. The space should be [2, 1],
# because when we fill the first hole, we have two choices from {i,
# j}, but for the second hole, we only have one choice left.
index_choices = [Var('i'), Var('j')]
index_choice_space = [2, 1]

# The ChoiceFactoryEnumerator then can be used to generate the sampling functions as follows
for array_choice_factory in ChoiceFactoryEnumerator(array_choice_space).enumerate():
    for index_choice_factory in ChoiceFactoryEnumerator(index_choice_space).enumerate():
        populator = PopulateParameters()
        populator.add('array', array_choices,
                      choice_function=array_choice_factory.create_choice_function())
        # Note that is_finite=True. Once we already pick a choice from the space,
        # we remove it from the space. Permutation can be viewed like this.
        populator.add('index', index_choices,
                      is_finite=True,
                      choice_function=index_choice_factory.create_choice_function())

        maybe_pattern = populate_name(skeleton.clone(), populator.populate)
        maybe_pattern_code = maybe_pattern.pprint()
        pattern = parse_pattern(maybe_pattern_code)
        print(pattern.pprint())
