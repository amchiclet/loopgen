import random
from pattern_ast import Replacer, Const, Declaration, Node, replace, ExpressionHole, StatementHole, OpHole, NameHole
from math import prod

class IncrementalChoice:
    def __init__(self):
        self.index = 0
    def choice(self, population):
        self.index = self.index % len(population)
        sample = population[self.index]
        self.index += 1
        return sample

class FixedChoice:
    def __init__(self, choices, index=0):
        self.choices = choices
        self.index = index
    def choice(self, population):
        assert(self.index < len(self.choices))
        sample = population[self.choices[self.index]]
        self.index += 1
        return sample

class FixedChoiceFactory:
    def __init__(self, choices, index=0):
        self.choices = choices
        self.index = index
    def create_choice_function(self):
        return FixedChoice(self.choices, self.index).choice

class ChoiceRecorder:
    def __init__(self):
        self.choices = []
    def choice(self, population):
        i = random.randint(0, len(population)-1)
        self.choices.append(i)
        return population[i]

def space_to_strides(space):
    strides = [1]
    for size in reversed(space):
        strides.append(size * strides[-1])
    strides.reverse()
    return strides
    
def int_to_point(i, space):
    strides = space_to_strides(space)
    if i >= strides[0]:
        raise RuntimeError('integer too large to be represented by space')

    point = []
    for dimension_size in strides[1:]:
        which_index = i // dimension_size
        point.append(which_index)
        i = i % dimension_size
    return point

def point_to_int(p, space):
    strides = space_to_strides(space)
    i = 0
    print(strides)
    for v, dimension_size in zip(p, strides[1:]):
        i += v * dimension_size
    return i

class ChoiceFactoryEnumerator:
    def __init__(self, space):
        self.space = space
        self.current_position = 0
        self.n_enumerated = 0
        self.space_size = prod(space)
    def enumerate(self):
        while self.n_enumerated < self.space_size:
            current_point = int_to_point(self.current_position, self.space)
            yield FixedChoiceFactory(current_point)
            self.n_enumerated += 1
            self.current_position += 1

# TODO: Store the choices made (probably as a list of integers).
#       This is useful for naming generated programs and debugging purposes.
class PopulateParameters:
    def __init__(self, default_choices=None, is_finite=False, choice_function=random.choice):
        self.available = {}
        self.choice_functions = {}
        self.assigned = {}
        self.finite_families = set()
        if default_choices is not None:
            self.add('_', default_choices, is_finite=is_finite, choice_function=choice_function)

    def add(self, family_name, choices, is_finite=False, choice_function=random.choice):
        assert(family_name not in self.available)
        self.set(family_name, choices, is_finite, choice_function)

    def set(self, family_name, choices, is_finite=False, choice_function=random.choice):
        self.available[family_name] = list(choices)
        self.choice_functions[family_name] = choice_function
        if is_finite:
            self.finite_families.add(family_name)

    def populate(self, node):
        name = node.hole_name
        family = node.family_name
        full_name = f'{name}:{family}'

        if name != '_' and full_name in self.assigned:
            return self.assigned[full_name]

        if family not in self.available:
            return node

        assert(len(self.available[family]) > 0)

        choice_function = self.choice_functions[family]
        chosen = choice_function(self.available[family])
        if name != '_':
            self.assigned[full_name] = chosen
        if family in self.finite_families:
            self.available[family].remove(chosen)

        return chosen.clone()

def populate_name(program, populate_function):
    replacer = NamePopulator(populate_function)
    return replace(program, replacer)

def populate_stmt(program, populate_function):
    replacer = StatementPopulator(populate_function)
    return replace(program, replacer)

def populate_expr(program, populate_function):
    replacer = ExpressionPopulator(populate_function)
    return replace(program, replacer)

def populate_op(program, populate_function):
    replacer = OpPopulator(populate_function)
    return replace(program, replacer)

class Populator(Replacer):
    def __init__(self, populate_function):
        self.populate_function = populate_function
    def should_skip(self, node):
        return type(node) in [Declaration, Const]
    def should_replace(self, node):
        raise NotImplementedError('Populator::should_replace')
    def replace(self, node):
        return self.populate_function(node)

class StatementPopulator(Populator):
    def should_replace(self, node):
        return type(node) == StatementHole

class OpPopulator(Populator):
    def should_replace(self, node):
        return type(node) == OpHole

class ExpressionPopulator(Populator):
    def should_replace(self, node):
        return type(node) == ExpressionHole

class NamePopulator(Populator):
    def should_replace(self, node):
        return type(node) == NameHole
