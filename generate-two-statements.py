from skeleton import \
    parse_str as parse_skeleton, \
    parse_stmt_str as parse_statement, \
    parse_seq_str as parse_seq, \
    parse_expr_str as parse_expression

from pattern import parse_str as parse_pattern
from skeleton_ast import Var, Op
from random import choice, seed
from codelet_generator import generate_codelets_with_fixed_sizes
from populator import PopulateParameters, populate_name, populate_stmt, populate_expr, populate_op

from hashlib import md5

seed(12345)

skeleton_code = """
declare A[][];
declare B[][];
declare C[][];
declare D[][];
declare E[][];
declare a;
declare b;
declare c;

for [i, j] {
  $_:stmt$
  $_:stmt$
}
"""
skeleton = parse_skeleton(skeleton_code)

stmt = ['#_:lhs# = #_:rhs# @_:op@ #_:rhs# @_:op@ #_:rhs#;']
lhs = ['`_:X_lhs`[`i1:I`][`i2:I`]']
rhs = ['`_:X_rhs`[`i1:I`][`i2:I`]', '`_:S_rhs`', '1.5']
scalar_names = ['a', 'b', 'c']
array_names = ['A', 'B', 'C', 'D', 'E']
index_names = ['i', 'j']
op_names = ['+', '*']

stmts = PopulateParameters()
stmts.add('stmt', [parse_statement(code) for code in stmt])

exprs = PopulateParameters()
exprs.add('lhs', [parse_expression(code) for code in lhs])
exprs.add('rhs', [parse_expression(code) for code in rhs])

ops = PopulateParameters()
ops.add('op', list(map(Op, op_names)))

names = PopulateParameters()
names.add('X_lhs', list(map(Var, array_names)))
names.add('X_rhs', list(map(Var, array_names)))
names.add('S_rhs', list(map(Var, scalar_names)))
names.add('I', list(map(Var, index_names)), is_finite=True)

def generate_one(code):
    code = populate_stmt(code, stmts.populate)
    code = populate_expr(code, exprs.populate)
    code = populate_op(code, ops.populate)
    code = populate_name(code, names.populate)
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

patterns = [parse_pattern(body.pprint()) for body in generated_bodies]
generate_codelets_with_fixed_sizes(patterns, index_names, [420, 600, 850])
