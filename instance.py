from pattern_ast import get_accesses, get_loops, gather_loop_shapes, gather_loop_vars, Access, Op, ConstReplacer
from random import randint, choice, shuffle, uniform
from loguru import logger
from z3_utils import expr_to_cexpr, get_scalar_cvars, find_max, find_min
from copy import deepcopy
from constant_assignment import VariableMap
from array_access_bound import (
    dimension_var,
    determine_array_access_bounds,
    ArrayAccessBound)

from z3 import Solver, Int, unsat, Optimize, sat, Or, And, Not

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
    def __init__(self, pattern, array_access_bounds):
        self.pattern = pattern
        if array_access_bounds is None:
            self.array_access_bounds = {}
            for decl in self.pattern.decls:
                bound = ArrayAccessBound(decl.name, decl.is_local, decl.n_dimensions)
                for size in decl.sizes:
                    assert(size is not None)
                    bound.min_indices.append(0)
                    bound.max_indices.append(size - 1)
                self.array_access_bounds[decl.name] = bound
        else:
            for name, bound in array_access_bounds.items():
                decl = next(d for d in pattern.decls if d.name == name)
                for dim, max_index in enumerate(bound.max_indices):
                    size = max_index + 1
                    if decl.sizes[dim] is None:
                        decl.sizes[dim] = size
                    else:
                        assert(decl.sizes[dim] == size)
            self.array_access_bounds = array_access_bounds
    def pprint(self):
        lines = []
        lines.append(self.pattern.pprint())
        for name in sorted(self.array_access_bounds.keys()):
            lines.append(f'Array {self.array_access_bounds[name].pprint()}')
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

def assign_types(pattern, type_assignment):
    pass

def create_instance(pattern, var_map, max_tries=10000, l=None, type_assignment=None):
    if l is None:
        l = logger

    def try_once():
        random_pattern = replace_constant_variables_blindly(pattern, var_map)
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
                    cloned_var_map.set_max(dim_var, size)

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

        bounds = determine_array_access_bounds(random_pattern.decls,
                                               accesses, cvars,
                                               constraints,
                                               cloned_var_map, l)
        if bounds is None:
            return None

        return Instance(random_pattern, bounds)

    for _ in range(max_tries):
        result = try_once()
        if result is None:
            continue
        return result

    return None

def create_instance_with_fixed_size_deprecated(pattern, loop_vars, size):
    def set_exact_loop_bounds(var_map, loop_var, min_val, max_val):
        lower_bound = f'{loop_var}_greater_eq'
        var_map.set_min(lower_bound, min_val)
        var_map.set_max(lower_bound, min_val)
        upper_bound = f'{loop_var}_less_eq'
        var_map.set_min(upper_bound, max_val)
        var_map.set_max(upper_bound, max_val)

    # instance
    var_map = VariableMap(default_max=size)
    for loop_var in loop_vars:
        set_exact_loop_bounds(var_map, loop_var, 0, size-1)

    instance = create_instance(pattern, var_map)
    return instance

def create_instance_with_fixed_size(pattern, size):
    def set_exact_loop_bounds(var_map, loop_var, min_val, max_val):
        lower_bound = f'{loop_var}_greater_eq'
        var_map.set_min(lower_bound, min_val)
        var_map.set_max(lower_bound, min_val)
        upper_bound = f'{loop_var}_less_eq'
        var_map.set_min(upper_bound, max_val)
        var_map.set_max(upper_bound, max_val)

    loops = get_loops(pattern)
    loop_shapes = gather_loop_shapes(loops)
    loop_vars = gather_loop_vars(loop_shapes)

    # instance
    var_map = VariableMap(default_max=size)
    for loop_var in set(loop_vars):
        set_exact_loop_bounds(var_map, loop_var, 0, size-1)

    instance = create_instance(pattern, var_map)
    return instance
