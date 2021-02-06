import random

class IncrementalChoice:
    def __init__(self):
        self.index = 0
    def choice(self, population):
        self.index = self.index % len(population)
        sample = population[self.index]
        self.index += 1
        return sample

def parse(hole_name):
    if ':' in hole_name:
        i = hole_name.index(':')
        name = hole_name[1:i]
        family = hole_name[i+1:-1]
    else:
        name = hole_name[1:-1]
        family = '_'
    return name, family, f'{name}:{family}'

class Populator:
    def __init__(self, default_choices=None, is_finite=False, choice_function=random.choice):
        self.available = {}
        self.choice_functions = {}
        self.assigned = {}
        self.finite_families = set()
        if default_choices is not None:
            self.add('_', default_choices, is_finite=is_finite, choice_function=choice_function)

    def add(self, family_name, choices, is_finite=False, choice_function=random.choice):
        assert(family_name not in self.available)
        self.available[family_name] = list(choices)
        self.choice_functions[family_name] = choice_function
        if is_finite:
            self.finite_families.add(family_name)

    def populate(self, hole_name):
        name, family, full_name = parse(hole_name)
        if name != '_' and full_name in self.assigned:
            return self.assigned[full_name]

        assert(family in self.available)
        assert(len(self.available[family]) > 0)

        choice_function = self.choice_functions[family]
        chosen = choice_function(self.available[family])
        if name != '_':
            self.assigned[full_name] = chosen
        if family in self.finite_families:
            self.available[family].remove(chosen)

        return chosen
