from random import choice

def parse(hole_name):
    if ':' in hole_name:
        i = hole_name.index(':')
        name = hole_name[1:i]
        family = hole_name[i:-1]
    else:
        name = hole_name[1:-1]
        family = '_'
    return name, family, f'{name}:{family}'

class Populator:
    def __init__(self, default_choices, is_finite=False):
        self.available = {}
        self.assigned = {}
        self.finite_families = set()
        self.add('_', default_choices, is_finite=is_finite)

    def add(self, family_name, choices, is_finite=False):
        assert(family_name not in self.available)
        self.available[family_name] = list(choices)
        if is_finite:
            self.finite_families.add(family_name)

    def populate(self, hole_name):
        name, family, full_name = parse(hole_name)
        print(name, family, full_name)
        if name != '_' and full_name in self.assigned:
            return self.assigned[full_name]

        print(f'populating {full_name}')
        assert(family in self.available)
        assert(len(self.available[family]) > 0)

        chosen = choice(self.available[family])
        if name != '_':
            self.assigned[full_name] = chosen
        if family in self.finite_families:
            self.available[family].remove(chosen)

        return chosen
