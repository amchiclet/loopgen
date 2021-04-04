from z3_utils import expr_to_cexpr, get_scalar_cvars, find_max, find_min

class ArrayAccessBound:
    def __init__(self, name, is_local, n_dimensions):
        self.name = name
        self.is_local = is_local
        self.min_indices = [None] * n_dimensions
        self.max_indices = [None] * n_dimensions
        self.n_dimensions = n_dimensions
    def new_min_index(self, dim, index):
        if self.min_indices[dim] is None or index < self.min_indices[dim]:
            self.min_indices[dim] = index
    def new_max_index(self, dim, index):
        if self.max_indices[dim] is None or index > self.max_indices[dim]:
            self.max_indices[dim] = index
    def set_unaccessed_dimensions_to_default(self):
        for dim in range(self.n_dimensions):
            current_min = self.min_indices[dim]
            current_max = self.max_indices[dim]
            if current_min is None:
                self.min_indices[dim] = 0 if current_max is None else current_max
            if current_max is None:
                self.max_indices[dim] = 0 if current_min is None else current_min
    def pprint(self):
        sizes = [max_index + 1 for max_index in self.max_indices]
        brackets = [f'[{size}]' for size in sizes]
        return f'{self.name}{"".join(brackets)}'

from enum import Enum
class Error(Enum):
    Z3_BUG = 0

def dimension_var(var, dimension):
    return f'{var}{"[]"*(dimension+1)}'

def determine_array_access_bounds(decls, accesses, cvars, constraints, var_map, l=None):
    if l is None:
        l = logger
    constraint_strs = '\n'.join(map(str, constraints))
    l.debug(f'Determining array sizes for constraints\n{constraint_strs}')
    bypass_set = set()
    bounds = {}
    cloned = var_map.clone()
    for decl in decls:
        bound = ArrayAccessBound(decl.name, decl.is_local, decl.n_dimensions)

        for dimension in range(decl.n_dimensions):
            dim_var = dimension_var(decl.name, dimension)
            if cloned.has_min(dim_var) and cloned.has_max(dim_var):
                bound.new_min_index(dimension, cloned.get_min(dim_var))
                bound.new_max_index(dimension, cloned.get_max(dim_var) - 1)
                bypass_set.add(dim_var)

        bounds[decl.name] = bound

    for access in accesses:
        for dimension, index in enumerate(access.indices):

            dim_var = dimension_var(access.var, dimension)
            if dim_var in bypass_set:
                continue

            cexpr = expr_to_cexpr(index, cvars)
            if cexpr is None:
                l.warning(f'Unable to analyze the max value of {index.pprint()} in {access.pprint()}')
                max_val = cloned.default_max
                min_val = cloned.default_min
            else:
                max_val = find_max(constraints, cexpr, l)
                if max_val is None or max_val == Error.Z3_BUG:
                    return None
                min_val = find_min(constraints, cexpr, l)
                if min_val is None or min_val == Error.Z3_BUG:
                    return None
            bound = bounds[access.var]
            bound.new_min_index(dimension, min_val)
            bound.new_max_index(dimension, max_val)

    for bound in bounds.values():
        bound.set_unaccessed_dimensions_to_default()
    return bounds
