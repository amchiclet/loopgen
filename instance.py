from pattern_ast import get_accesses, get_loops, gather_loop_shapes, gather_loop_vars, Access, Op, ConstReplacer, Literal, plus_one
from random import randint, choice, shuffle, uniform
from loguru import logger
from z3_utils import expr_to_cexpr, get_scalar_cvars, get_int_cvars, find_max, find_min
from copy import deepcopy
from constant_assignment import VariableMap
from array_access_bound import (
    dimension_var,
    determine_array_access_bounds,
    ArrayAccessBound)
from type_assignment import TypeAssignment, assign_types
from z3 import Solver, Int, unsat, Optimize, sat, Or, And, Not

# Whatever's an index, it should be greater than 0 and less
# than or equal the possible array size for that dimension
def generate_index_constraints(accesses, cvars, var_map):
    constraints = []
    for access in accesses:
        for dimension, index in enumerate(access.indices):
            cexpr = expr_to_cexpr(index, cvars)
            if cexpr is not None:
                constraints.append(0 <= cexpr)
                dim_var = dimension_var(access.var, dimension)
                dim_size = var_map.get_max(dim_var)
                dim_size_cexpr = expr_to_cexpr(dim_size, cvars)
                constraints.append(cexpr < dim_size_cexpr)
    return constraints

# Loop variables do not extend further than their loop bounds
def generate_loop_shape_constraints(loop_shapes, cvars):
    constraints = []
    for shape in loop_shapes:
        i = expr_to_cexpr(shape.loop_var, cvars)

        i_greater_eq = expr_to_cexpr(shape.greater_eq, cvars)
        if i_greater_eq is not None:
            constraints.append(i_greater_eq <= i)

        for expr in shape.less_eq:
            i_less_eq = expr_to_cexpr(expr, cvars)
            if i_less_eq is not None:
                constraints.append(i <= i_less_eq)
    return constraints

# Whatever assertion the user specifies in the var map must
# be respected.
def generate_bound_constraints(decls, cvars, var_map):
    constraints = []
    for name, min_val, max_val in var_map.iterate_ranges():
        if name in cvars:
            cvar = cvars[name]
            constraints.append(cvar >= min_val)
            constraints.append(cvar <= max_val)
    return constraints

class Instance:
    def __init__(self, pattern, array_access_bounds):
        self.pattern = pattern

        for name, bound in array_access_bounds.items():
            decl = next(d for d in pattern.decls if d.name == name)
            for dim, max_index in enumerate(bound.max_indices):
                if decl.sizes[dim] is None:
                    decl.sizes[dim] = plus_one(max_index)
        self.array_access_bounds = array_access_bounds
    def pprint(self):
        lines = []
        lines.append(self.pattern.pprint())
        for name in sorted(self.array_access_bounds.keys()):
            lines.append(f'access {self.array_access_bounds[name].pprint()}')
        return '\n'.join(lines)
    def clone(self):
        return Instance(self.pattern.clone(),
                        deepcopy(self.array_access_bounds))

def replace_constant_variables_blindly(pattern, var_map):
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
    return cloned

def try_create_instance(pattern, var_map, types, force):
    l = logger

    random_pattern = replace_constant_variables_blindly(pattern, var_map)
    accesses = get_accesses(random_pattern)

    if force:
        bounds = {}
        for decl in random_pattern.decls:
            for size in decl.sizes:
                assert(size is not None)
            bound = ArrayAccessBound(decl.name, decl.is_local, decl.n_dimensions)
            bounds[decl.name] = bound
        assign_types(random_pattern, types)
        return Instance(random_pattern, bounds)

    cvars = get_int_cvars(random_pattern, types)

    cloned_var_map = var_map.clone()

    # Set array sizes in var map
    for decl in random_pattern.decls:
        for dimension in range(decl.n_dimensions):
            size = decl.sizes[dimension]
            if size is not None:
                dim_var = dimension_var(decl.name, dimension)
                # TODO: we don't really need min
                cloned_var_map.set_min(dim_var, 0)
                # TODO: maybe allow more room for the max
                cloned_var_map.set_max(dim_var, size)

    index_constraints = generate_index_constraints(accesses,
                                                   cvars,
                                                   cloned_var_map)

    loop_shape_constraints = []
    for loop in get_loops(random_pattern):
        loop_shape_constraints += generate_loop_shape_constraints(loop.loop_shapes,
                                                                  cvars)

    bound_constraints = generate_bound_constraints(random_pattern.decls, cvars, cloned_var_map)

    l.debug('Index constraints:\n' + '\n'.join(map(str, index_constraints)))
    l.debug('Loop shape constraints:\n' + '\n'.join(map(str, loop_shape_constraints)))
    l.debug('Bound constraints:\n' + '\n'.join(map(str, bound_constraints)))

    if len(index_constraints) > 0:
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

    bounds = determine_array_access_bounds(random_pattern.decls,
                                           accesses, cvars,
                                           constraints,
                                           cloned_var_map, l)
    if bounds is None:
        return None

    assign_types(random_pattern, types)
    return Instance(random_pattern, bounds)

def create_instance(pattern, var_map, types):
    for _ in range(1000):
        result = try_create_instance(pattern, var_map, types)
        if result is None:
            continue
        return result

    return None
