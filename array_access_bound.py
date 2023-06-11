from z3_utils import expr_to_cexpr, get_scalar_cvars, find_min_max, is_sat
from z3 import Int, Or
from pattern_ast import Op, Literal

class ArrayAccessBound:
    def __init__(self, name, is_local, n_dimensions):
        self.name = name
        self.is_local = is_local
        self.min_indices = [None] * n_dimensions
        self.max_indices = [None] * n_dimensions
        self.n_dimensions = n_dimensions
        self.is_dynamic = False
    def new_min_index(self, dim, index):
        if self.is_dynamic:
            return
        if self.min_indices[dim] is None or index < self.min_indices[dim]:
            self.min_indices[dim] = index
    def new_max_index(self, dim, index):
        if self.is_dynamic:
            return
        if self.max_indices[dim] is None or index > self.max_indices[dim]:
            self.max_indices[dim] = index
    def fix_size(self, dim, size):
        self.is_dynamic = True
        self.min_indices[dim] = 0
        self.max_indices[dim] = size
    def set_unaccessed_dimensions_to_default(self):
        for dim in range(self.n_dimensions):
            current_min = self.min_indices[dim]
            current_max = self.max_indices[dim]
            if current_min is None:
                self.min_indices[dim] = 0 if current_max is None else current_max
            if current_max is None:
                self.max_indices[dim] = 0 if current_min is None else current_min
    def pprint(self):
        brackets = [f'[{min_index}, {max_index}]'
                    for min_index, max_index in zip(self.min_indices, self.max_indices)]
        return f'{self.name}{"".join(brackets)}'
    def __str__(self):
        return self.pprint()

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
        # If the size expr is already set, use it
        for dimension in range(decl.n_dimensions):
            size = decl.sizes[dimension]
            if size is not None:
                # For a given size in the declaration A[M] the max
                # index is M-1.
                size_minus_one = Op('-', [size.clone(), Literal(int, 1)])
                bound.fix_size(dimension, size_minus_one)

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
            if len(related_cexprs[dim_var]) == 0:
                continue

            access_constraints = [cexpr == dim_var_cexpr for cexpr in related_cexprs[dim_var]]
            access_constraints = Or(access_constraints)
            index_analysis_constraints = constraints + [access_constraints]
            l.debug(f'index analysis constraints\n{index_analysis_constraints}')
            min_index, max_index = find_min_max(index_analysis_constraints, dim_var_cexpr)
            if min_index is None or max_index is None:
                return None
            l.debug(f'Found: min_index({min_index}) max_index({max_index})')
            if size is not None:
                size_cexpr = expr_to_cexpr(size, cvars)
                assert(size_cexpr is not None)
                must_be_unsat = constraints + [size_cexpr <= max_index]
                if is_sat(must_be_unsat, print_model=True):
                    l.warning(f'It is possible that {max_index} >= {size}, causing an out-of-bound error')
                    return None
            bound = bounds[decl.name]
            bound.new_min_index(dimension, min_index)
            bound.new_max_index(dimension, max_index)

    for bound in bounds.values():
        bound.set_unaccessed_dimensions_to_default()
    for bound in bounds.values():
        l.debug(bound)
    return bounds
