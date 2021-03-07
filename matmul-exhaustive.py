from skeleton import parse_str as parse_skeleton
from skeleton_ast import Var
from pattern import parse_str as parse_pattern
from instance import create_instance, VariableMap
from random import choice
from codelet_generator import generate_codelet
from populator import ChoiceFactoryEnumerator, PopulateParameters, populate_name

matmul_code = """
declare A[][];
declare B[][];
declare C[][];

for [i, j, k] {
  A[`x:index`][`y:index`] = A[`x:index`][`y:index`] + `_:array`[`x:index`][k] * `_:array`[k][`y:index`];
}
"""
# skeleton
skeleton = parse_skeleton(matmul_code)
print(skeleton.pprint())

array_choices = [Var('A'), Var('B'), Var('C')]
index_choices = [Var('i'), Var('j')]

# 2 choices need to be made, i.e. to determine the two instances of _:array
n_array_choices = 2
array_choice_space = n_array_choices * [len(array_choices)]

# 2 choices need to be made, i.e. to determine what is x:index and what is y:index
n_index_choices = 2
index_choice_space = n_index_choices * [len(index_choices)]

i = 0
for array_choice_factory in ChoiceFactoryEnumerator(array_choice_space).enumerate():
    for index_choice_factory in ChoiceFactoryEnumerator(index_choice_space).enumerate():
        populator = PopulateParameters()
        populator.add('array', array_choices, choice_function=array_choice_factory.create_choice_function())
        populator.add('index', index_choices, choice_function=index_choice_factory.create_choice_function())

        maybe_pattern = populate_name(skeleton.clone(), populator.populate)
        maybe_pattern_code = maybe_pattern.pprint()
        pattern = parse_pattern(maybe_pattern_code)
        print(pattern.pprint())
        i += 1




