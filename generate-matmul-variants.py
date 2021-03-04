from skeleton import \
    parse_str as parse_skeleton, \
    parse_stmt_str as parse_statement, \
    parse_seq_str as parse_seq, \
    parse_expr_str as parse_expression

from pattern import parse_str as parse_pattern
from instance import create_instance, VariableMap
from skeleton_ast import replace, populate_name, populate_stmt, populate_expr, Var, populate_op, Op
from random import choice, seed
from codelet_generator import generate_codelet
from populator import Populator

from hashlib import md5

# seed(12345)

skeleton_code = """
declare A[][];
declare B[][];
declare C[][];
declare D[][];
declare E[][];

for [i, j, k] {
  A[i][j] = A[i][j] + (#_:op1#) * (#_:op2#);
}
"""
skeleton = parse_skeleton(skeleton_code)

op1a = "#_:ik# @_@ B[i][k]"
op1b = "B[i][k] @_@ #_:ik#"

op2a = "#_:kj# @_@ `_:bc`[k][j]"
op2b = "`_:bc`[k][j] @_@ #_:kj#"

operand_populator_1 = Populator()
operand_populator_1.add('op1', [parse_expression(code) for code in [op1a, op1b]])
operand_populator_1.add('op2', [parse_expression(code) for code in [op2a, op2b]])

ik1 = "`_:de`[i][k]"
ik2 = "2.5"
kj1 = "`_:de`[k][j]"
kj2 = "1.5"
operand_populator_2 = Populator()
operand_populator_2.add('ik', [parse_expression(code) for code in [ik1, ik2]])
operand_populator_2.add('kj', [parse_expression(code) for code in [kj1, kj2]])

op_populator = Populator([Op('*'), Op('+')])

name_populator = Populator()
name_populator.add('bc', [Var('B'), Var('C')])
name_populator.add('de', [Var('D'), Var('E')])

def generate_one(code):
    code = populate_expr(code, operand_populator_1.populate)
    code = populate_expr(code, operand_populator_2.populate)    
    code = populate_op(code, op_populator.populate)
    code = populate_name(code, name_populator.populate)
    return code

generated_bodies = []
generated_hashes = set()
n_wanted = 100
max_tries = 10000
for _ in range(max_tries):
    body = generate_one(skeleton.clone())

    code = body.pprint()
    code_hash = md5(code.encode('utf-8')).hexdigest()

    if code_hash in generated_hashes:
        print('duplicate')
        continue

    generated_hashes.add(code_hash)
    generated_bodies.append(body)
    if len(generated_hashes) == n_wanted:
        break

def create_instance_with_size(size):
    def set_exact_loop_bounds(var_map, loop_var, min_val, max_val):
        lower_bound = f'{loop_var}_greater_eq'
        var_map.set_min(lower_bound, min_val)
        var_map.set_max(lower_bound, min_val)
        upper_bound = f'{loop_var}_less_eq'
        var_map.set_min(upper_bound, max_val)
        var_map.set_max(upper_bound, max_val)

    # instance
    var_map = VariableMap()
    for loop_var in ['i', 'j', 'k']:
        set_exact_loop_bounds(var_map, loop_var, 0, size-1)

    instance = create_instance(pattern, var_map)
    return instance

print(len(generated_hashes))

def name_many(nodes, delimiter=''):
    return delimiter.join([name(node) for node in nodes])

def name(node):
    from pattern_ast import Hex, Assignment, AbstractLoop, Literal, Access, Program, Op
    ty = type(node)
    if ty == Literal:
        return 'X'
    if ty == Hex:
        return node.str_val
    if ty == Assignment:
        return f'_set_{name(node.lhs)}{name(node.rhs)}'
    if ty == Access:
        return f'{node.var}{name_many(node.indices)}'
    if ty == AbstractLoop:
        assert(len(node.body) == 1)
        return name(node.body[0])
    if ty == Op:
        op_map = {
            '+': '_add_',
            '*': '_mul_'
        }
        return f'{op_map[node.op]}{name_many(node.args)}'
    if ty == Program:
        assert(len(node.body) == 1)
        return name(node.body[0])
    print(ty)

v_number = 1
for body in generated_bodies:
    pattern = parse_pattern(body.pprint())
    pattern_name = name(pattern)

    for size in 420, 600, 850:
        instance = create_instance_with_size(size)

        # C code generation
        application = 'LoopGen'
        batch = 'matmul_variations'
        code_prefix = f'{pattern_name}'
        code = f'{code_prefix}.c'
        codelet = f'{code_prefix}_{size}.c_de'
        n_iterations = 10
        print(instance.pprint())
        generate_codelet(application, batch, code, codelet, n_iterations, instance)
