from random import choice

class TypeAssignment:
    def __init__(self, default_types=None):
        self.default_types = default_types if default_types is not None else ['float', 'double', 'int']
        self.map = {}
    def set(self, var_name, ty):
        self.map[var_name] = [ty]
    def set_choices(self, var_name, tys):
        self.map[var_name] = tys
    def can_be(self, var_name, ty):
        if var_name not in self.map:
            return ty in self.default_types
        return ty in self.map[var_name]
    def get(self, var_name):
        if var_name in self.map:
            return choice(self.map[var_name])
        return choice(self.default_types)

# Assign types to declarations that don't have types yet
# Mutates the given pattern directly
def assign_types(pattern, type_assignment):
    for decl in pattern.decls:
        if decl.ty is not None:
            continue
        decl.ty = type_assignment.get(decl.name)
