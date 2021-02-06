from pattern_ast import get_accesses, get_loops, Access, Op, ConstReplacer
from random import randint, choice, shuffle, uniform
from loguru import logger
from z3_utils import expr_to_cexpr, get_scalar_cvars, find_max, find_min
from copy import deepcopy
from enum import Enum

class Error(Enum):
    Z3_BUG = 0

class Limit:
    def __init__(self, min_val=None, max_val=None):
        self.min_val = min_val
        self.max_val = max_val
    def clone(self):
        return Limit(self.min_val, self.max_val)

class VariableMap:
    def __init__(self, default_min=0, default_max=999):
        self.default_min = default_min
        self.default_max = default_max
        self.limits = {}
    def remove_var(self, var):
        if var in self.limits:
            self.limits.pop(var)
    def has_min(self, var):
        return var in self.limits and not self.limits[var].min_val is None
    def has_max(self, var):
        return var in self.limits and not self.limits[var].max_val is None
    def set_min(self, var, min_val):
        if var not in self.limits:
            self.limits[var] = Limit()
        self.limits[var].min_val = min_val
    def set_max(self, var, max_val):
        if var not in self.limits:
            self.limits[var] = Limit()
        self.limits[var].max_val = max_val
    def get_min(self, var):
        if var not in self.limits:
            return self.default_min
        min_val = self.limits[var].min_val
        return min_val if min_val is not None else self.default_min
    def get_max(self, var):
        if var not in self.limits:
            return self.default_max
        max_val = self.limits[var].max_val
        return max_val if max_val is not None else self.default_max
    def clone(self):
        cloned = VariableMap(self.default_min, self.default_max)
        for var, limit in self.limits.items():
            cloned.limits[var] = limit.clone()
        return cloned
    def pprint(self):
        lines = []
        for var in sorted(self.limits.keys()):
            limit = self.limits[var]
            lines.append(f'Variable {var} range [{limit.min_val}, {limit.max_val}]')
        return '\n'.join(lines)

from z3 import Solver, Int, unsat, Optimize, sat, Or, And, Not

def dimension_var(var, dimension):
    return f'{var}{"[]"*(dimension+1)}'

def generate_index_constraints(accesses, cvars, var_map):
    constraints = []
    for access in accesses:
        for dimension, index in enumerate(access.indices):
            cexpr = expr_to_cexpr(index, cvars)
            if cexpr is not None:
                constraints.append(0 <= cexpr)
                dim_var = dimension_var(access.var, dimension)
                dim_size = var_map.get_max(dim_var)
                constraints.append(cexpr < dim_size)
    return constraints

def generate_loop_shape_constraints(loop_shapes, cvars, var_map):
    constraints = []
    for shape in loop_shapes:
        i = expr_to_cexpr(shape.loop_var, cvars)

        i_greater_eq = expr_to_cexpr(shape.greater_eq, cvars)
        if i_greater_eq is not None:
            constraints.append(i_greater_eq <= i)

        i_less_eq = expr_to_cexpr(shape.less_eq, cvars)
        if i_less_eq is not None:
            constraints.append(i <= i_less_eq)

    return constraints

def generate_bound_constraints(cvars, var_map):
    constraints = []
    for var, cvar in cvars.items():
        current_min = var_map.get_min(var)
        current_max = var_map.get_max(var)
        constraints.append(cvar >= current_min)
        constraints.append(cvar <= current_max)
    return constraints

class ArraySize:
    def __init__(self, name, is_local, n_dimensions):
        self.name = name
        self.is_local = is_local
        self.min_indices = [None] * n_dimensions
        self.max_indices = [None] * n_dimensions
        self.n_dimensions = n_dimensions
    def new_min(self, dim, index):
        if self.min_indices[dim] is None or index < self.min_indices[dim]:
            self.min_indices[dim] = index
    def new_max(self, dim, index):
        if self.max_indices[dim] is None or index > self.max_indices[dim]:
            self.max_indices[dim] = index
    def check(self):
        for dim in range(self.n_dimensions):
            if self.min_indices[dim] is None:
                self.min_indices[dim] = 0
            if self.max_indices[dim] is None:
                self.max_indices[dim] = 0
    def pprint(self):
        sizes = [max_index + 1 for max_index in self.max_indices]
        brackets = [f'[{size}]' for size in sizes]
        return f'{self.name}{"".join(brackets)}'

def determine_array_sizes(decls, accesses, cvars, constraints, var_map, l=None):
    if l is None:
        l = logger
    constraint_strs = '\n'.join(map(str, constraints))
    l.debug(f'Determining array sizes for constraints\n{constraint_strs}')
    bypass_set = set()
    array_sizes = {}
    cloned = var_map.clone()
    for decl in decls:
        array = ArraySize(decl.name, decl.is_local, decl.n_dimensions)

        for dimension in range(decl.n_dimensions):
            dim_var = dimension_var(decl.name, dimension)
            if cloned.has_min(dim_var) and cloned.has_max(dim_var):
                array.new_min(dimension, cloned.get_min(dim_var))
                array.new_max(dimension, cloned.get_max(dim_var))
                bypass_set.add(dim_var)

        array_sizes[decl.name] = array

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
                    return max_val
                min_val = find_min(constraints, cexpr, l)
                if min_val is None or min_val == Error.Z3_BUG:
                    return min_val
            array_sizes[access.var].new_min(dimension, min_val)
            array_sizes[access.var].new_max(dimension, max_val)

    for array in array_sizes.values():
        array.check()
    return array_sizes

def validate_var_map(program, var_map):
    cloned = var_map.clone()

    accesses = get_accesses(program)

    cvars = get_scalar_cvars(program)
    index_constraints = generate_index_constraints(accesses, cvars, cloned)
    bound_constraints = generate_bound_constraints(cvars, cloned)
    constraints = index_constraints + bound_constraints

    solver = Solver()
    solver.set('timeout', 10000)
    solver.add(constraints)
    status = solver.check()

    if status == unsat:
        return False
    return True

class Instance:
    def __init__(self, pattern, array_sizes):
        self.pattern = pattern
        if array_sizes is None:
            self.array_sizes = {}
            for decl in self.pattern.decls:
                array_size = ArraySize(decl.name, decl.is_local, decl.n_dimensions)
                array_size.min_indices = [0] * decl.n_dimensions
                array_size.max_indices = []
                for size in decl.sizes:
                    if size is None:
                        array_size.max_indices.append(None)
                    else:
                        array_size.max_indices.append(size - 1)
                self.array_sizes[decl.name] = array_size
        else:
            for name, array in array_sizes.items():
                decl = next(d for d in pattern.decls if d.name == name)
                for dim, max_index in enumerate(array.max_indices):
                    size = max_index + 1
                    if decl.sizes[dim] is None:
                        decl.sizes[dim] = size
                    else:
                        assert(decl.sizes[dim] == size)
            self.array_sizes = array_sizes
    def pprint(self):
        lines = []
        lines.append(self.pattern.pprint())
        for name in sorted(self.array_sizes.keys()):
            lines.append(f'Array {self.array_sizes[name].pprint()}')
        return '\n'.join(lines)
    def clone(self):
        return Instance(self.pattern.clone(),
                        deepcopy(self.array_sizes))

def create_instance_blindly(pattern, var_map):
    cloned = pattern.clone()
    replace_map = {}
    for const in cloned.consts:
        var = const.name
        min_val = var_map.get_min(var)
        max_val = var_map.get_max(var)
        # TODO: support other types than int
        if type(min_val) == int:
            val = randint(min_val, max_val)
        elif type(min_val) == float:
            val = uniform(min_val, max_val)
        replace_map[const.name] = val
    replacer = ConstReplacer(replace_map)
    cloned.replace(replacer)
    cloned.consts = []
    return Instance(cloned, None)

def create_instance(pattern, var_map, max_tries=10000, l=None):
    if l is None:
        l = logger

    def try_once():
        random_pattern = create_instance_blindly(pattern, var_map).pattern
        cvars = get_scalar_cvars(random_pattern)
        accesses = get_accesses(random_pattern)
        cloned_var_map = var_map.clone()

        # Set array sizes in var map
        for decl in random_pattern.decls:
            for dimension in range(decl.n_dimensions):
                size = decl.sizes[dimension]
                if size is not None:
                    max_index = size - 1
                    dim_var = dimension_var(decl.name, dimension)
                    # TODO: we don't really need min
                    cloned_var_map.set_min(dim_var, 0)
                    # TODO: maybe allow more room for the max
                    cloned_var_map.set_max(dim_var, max_index)

        index_constraints = generate_index_constraints(accesses,
                                                       cvars,
                                                       cloned_var_map)

        loop_shape_constraints = []
        for loop in get_loops(random_pattern):
            loop_shape_constraints += generate_loop_shape_constraints(loop.loop_shapes,
                                                                      cvars,
                                                                      cloned_var_map)

        bound_constraints = generate_bound_constraints(cvars, cloned_var_map)

        l.debug('Index constraints:\n' + '\n'.join(map(str, index_constraints)))
        l.debug('Loop shape constraints:\n' + '\n'.join(map(str, loop_shape_constraints)))
        l.debug('Bound constraints:\n' + '\n'.join(map(str, bound_constraints)))

        assert(len(index_constraints) > 0)
        invert_index_constraints = Not(And(index_constraints))
        
        constraints = [invert_index_constraints] + loop_shape_constraints + bound_constraints

        solver = Solver()
        solver.set('timeout', 10000)
        solver.add(constraints)
        status = solver.check()
        if status != unsat:
            l.debug(f'Constraints are not unsatisfiable ({status}). '
                    'May result in index out of bound')
            l.debug('Constraints:\n' + '\n'.join(map(str, constraints)))
            if status == sat:
                l.debug(f'Model:\n{solver.model()}')
            return None

        constraints = index_constraints + loop_shape_constraints + bound_constraints
        solver = Solver()
        solver.set('timeout', 10000)
        solver.add(constraints)
        status = solver.check()
        if status != sat:
            l.debug(f'Constraints are not satisfiable ({status}). '
                    'May result in no iterations')
            l.debug('\n'.join(map(str, constraints)))
            return None

        array_sizes = determine_array_sizes(random_pattern.decls,
                                            accesses, cvars,
                                            constraints,
                                            cloned_var_map, l)
        if array_sizes is None or array_sizes == Error.Z3_BUG:
            return None

        return Instance(random_pattern, array_sizes)

    for _ in range(max_tries):
        result = try_once()
        if result == Error.Z3_BUG:
            return None
        if result == Error.Z3_BUG:
            return Error.Z3_BUG
        if result is not None:
            return result

    return None
