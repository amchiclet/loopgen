from skeleton import \
    parse_str as parse_skeleton, \
    parse_stmt_str as parse_statement, \
    parse_seq_str as parse_seq, \
    parse_expr_str as parse_expression

from pattern import parse_str as parse_pattern
from instance import create_instance, VariableMap
from skeleton_ast import replace, Literal, populate_name, populate_stmt, populate_expr, Var, populate_op, Op
from random import choice
from codelet_generator import generate_codelet
from populator import Populator

skeleton_code = """
declare A[][];
declare B[][];
declare C[][];

for [i, j, k] {
  $_$
  $_$
  $_$
}
"""

blank_code = ""

matmul_code = """
  A[i][j] = `_`[i][k] * `_`[k][j];
"""

matadd_code = """
  A[i][j] = `_`[i][j] + `_`[i][j];
"""

matvec_code = """
  A[0][i] = `_`[0][i] + `_`[i][j] * `_`[0][j];
"""

freestyle_code = """
  `_`[i][j] = #_# @_@ #_#;
"""

stmts = [parse_seq(code) for code in [blank_code, matmul_code, matadd_code, matvec_code, freestyle_code]]

expr1_code = "`_`[i][j]"
expr2_code = "`_`[i][k]"
expr3_code = "`_`[j][k]"

exprs = [parse_expression(code) for code in [expr1_code, expr2_code, expr3_code]]

# skeleton
skeleton = parse_skeleton(skeleton_code)
print('// Original')
print(skeleton.pprint())
print('============================')

# pattern
stmt_populator = Populator(stmts)
skeleton = populate_stmt(skeleton, stmt_populator.populate)
print('// After replacing statements')
print(skeleton.pprint())
print('============================')

expr_populator = Populator(exprs)
skeleton = populate_expr(skeleton, expr_populator.populate)
print('// After replacing expressions')
print(skeleton.pprint())
print('============================')

op_populator = Populator([Op('*'), Op('+'), Op('/'), Op('-')])
skeleton = populate_op(skeleton, op_populator.populate)
print('// After replacing operations')
print(skeleton.pprint())
print('============================')

name_populator = Populator([Var('A'), Var('B'), Var('C')])
skeleton = populate_name(skeleton, name_populator.populate)
print('// After replacing array names')
print(skeleton.pprint())
print('============================')
