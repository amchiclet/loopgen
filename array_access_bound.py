from z3_utils import expr_to_cexpr, get_scalar_cvars, find_max, find_min, Error
from z3 import Int

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
        bounds[decl.name] = bound

    related_cexprs = {}
    for decl in decls:
        for dimension in range(decl.n_dimensions):
            dim_var = dimension_var(decl.name, dimension)
            related_cexprs[dim_var] = []
    for access in accesses:
        for dimension, index in enumerate(access.indices):
            dim_var = dimension_var(access.var, dimension)
            cexpr = expr_to_cexpr(index, cvars)
            assert(cexpr is not None)
            related_cexprs[dim_var].append(cexpr)

    # find_min(size) for all index where (size > index)
    for decl in decls:
        for dimension, size in enumerate(decl.sizes):
            dim_var = dimension_var(decl.name, dimension)
            dim_var_cexpr = Int(dim_var)
            upperbound_constraints = [cexpr < dim_var_cexpr for cexpr in related_cexprs[dim_var]]
            if size is None:
                dimension_max_cexpr = expr_to_cexpr(var_map.get_max(dim_var), cvars)
                upperbound_constraints.append(dim_var_cexpr <= dimension_max_cexpr)
            else:
                size_cexpr = expr_to_cexpr(size, cvars)
                upperbound_constraints.append(size_cexpr == dim_var_cexpr)

            l.info('upper bounds')
            l.info(constraints + upperbound_constraints)
            array_dim_size = find_max(constraints + upperbound_constraints, dim_var_cexpr)
            if array_dim_size is None:
                return None
            upper_bound = array_dim_size - 1
            l.info(f'found upperbound size for {dim_var} {upper_bound}')

            lowerbound_constraints = [cexpr >= dim_var_cexpr for cexpr in related_cexprs[dim_var]]
            dimension_min_cexpr = expr_to_cexpr(var_map.get_min(dim_var), cvars)
            lowerbound_constraints.append(dim_var_cexpr >= dimension_min_cexpr)
            l.info('lower bounds')
            l.info(constraints + lowerbound_constraints)
            lower_bound = find_min(constraints + lowerbound_constraints, dim_var_cexpr)
            if lower_bound is None:
                return None
            l.info(f'found lowerbound size for {dim_var} {lower_bound}')
            bound = bounds[decl.name]
            bound.new_min_index(dimension, lower_bound)
            bound.new_max_index(dimension, upper_bound)

    for bound in bounds.values():
        bound.set_unaccessed_dimensions_to_default()
    return bounds
