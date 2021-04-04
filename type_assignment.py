from random import choice

class TypeAssignment:
    def __init__(self, default_types=None):
        self.default_types = default_types if default_types is not None else []
        self.map = {}
    def get_type(self, var_name):
        if var_name in self.map:
            return choice(self.map[var_name])
        return choice(self.default_types)

# Assign types to declarations that don't have types yet
# Mutates the given pattern directly
def assign_types(pattern, type_assignment):
    for decl in pattern.decls:
        if decl.ty is not None:
            continue
        decl.ty = type_assignment.get_type(decl.name)
