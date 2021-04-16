from z3 import Int, Optimize, sat, unsat, Solver
from pattern_ast import get_accesses, Op, Access, Literal, Node
from loguru import logger

from enum import Enum
class Error(Enum):
    Z3_BUG = 0

def expr_to_cexpr(expr, cvars):
    # logger.info(expr)
    if type(expr) == Op:
        args = expr.args
        op = expr.op
        if len(args) == 1:
            cexpr = expr_to_cexpr(args[0], cvars)
            if expr.op == '+':
                return cexpr
            elif expr.op == '-':
                return -cexpr
        elif len(args) == 2:
            left = expr_to_cexpr(args[0], cvars)
            right = expr_to_cexpr(args[1], cvars)
            if left is not None and right is not None:
                if op == '+':
                    return left + right
                elif op == '*':
                    return left * right
                elif op == '-':
                    return left - right
                elif op == '/':
                    return left / right
    elif type(expr) == Literal:
        if expr.ty == int:
            return expr.val
    elif type(expr) == Access:
        if expr.is_scalar() and expr.var in cvars:
            return cvars[expr.var]
    elif type(expr) == int:
        return expr
    return None

def get_scalar_cvars(pattern):
    cvars = {}
    def maybe_add(access):
        if access.is_scalar() and access.var not in cvars:
            cvars[access.var] = Int(access.var)

    for access in get_accesses(pattern):
        maybe_add(access)
    for decl in pattern.decls:
        for size in decl.sizes:
            if size is not None:
                for access in get_accesses(size):
                    maybe_add(access)

    return cvars

def affine_to_cexpr(affine, cvars):
    if not affine.var:
        return affine.offset
    return affine.coeff * cvars[affine.var] + affine.offset

def find_max(constraints, expr, l = None):
    if l is None:
        l = logger

    if type(expr) == int:
        return expr

    constraint_strs = [f'{c}' for c in constraints]

    max_optimize = Optimize()
    max_optimize.set('timeout', 10000)
    max_optimize.assert_exprs(*constraints)
    max_optimize.maximize(expr)
    status = max_optimize.check()
    if status != sat:
        l.warning(f'Unable to find max ({status}) for:\n' + '\n'.join(constraint_strs))
        return None

    max_val = max_optimize.model().eval(expr).as_long()

    # Make sure it's actually the max, since z3 has a bug
    #   https://github.com/Z3Prover/z3/issues/4670
    solver = Solver()
    solver.set('timeout', 10000)
    solver.add(constraints + [expr > max_val])
    status = solver.check()

    if status != unsat:
        l.error(f'Z3 bug\nFind max ({expr}) => {max_val} with status ({status}):\n' + '\n'.join(constraint_strs))
        return None
    return max_val

def find_min(constraints, expr, l = None):
    if l is None:
        l = logger

    if type(expr) == int:
        return expr

    constraint_strs = [f'{c}' for c in constraints]

    min_optimize = Optimize()
    min_optimize.set('timeout', 10000)
    min_optimize.assert_exprs(*constraints)
    min_optimize.minimize(expr)
    status = min_optimize.check()
    if status != sat:
        l.warning(f'Unable to find min ({status}) for:\n' + '\n'.join(constraint_strs))
        return None

    min_val = min_optimize.model().eval(expr).as_long()

    # Make sure it's actually the min, since z3 has a bug
    #   https://github.com/Z3Prover/z3/issues/4670
    solver = Solver()
    solver.set('timeout', 10000)
    solver.add(constraints + [expr < min_val])
    status = solver.check()

    if status != unsat:
        l.error(f'Z3 bug\nFind min ({expr}) => {min_val} with status ({status}):\n' + '\n'.join(constraint_strs))
        return None
    return min_val

def find_min_max(constraints, i):
    return [f(constraints, i) for f in [find_min, find_max]]

def is_sat(constraints):
    solver = Solver()
    solver.set('timeout', 10000)
    solver.add(constraints)
    status = solver.check()
    return status == sat
