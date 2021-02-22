from skeleton import \
    parse_str as parse_skeleton, \
    parse_stmt_str as parse_statement, \
    parse_expr_str as parse_expression

from pattern import parse_str as parse_pattern
from instance import create_instance, VariableMap
from skeleton_ast import replace, Literal, populate_name, populate_stmt, populate_expr, Var
from random import choice
from codelet_generator import generate_codelet
from populator import Populator

skeleton_code = """
declare A[][];
declare B[][];
declare C[][];

for [i, j, k] {
  `_:lhs`[i][j] = `x:rhs`[i][j];
  $_:stmts1$
  $_:stmts2$
}
"""

stmt1_code = """
  `_:lhs`[i][j] = `x:rhs`[i][j] + `_:rhs`[j][k] - #_#;
"""

stmt2_code = """
  A[i][j] = B[i][j] + `x:rhs`[j][k] - #_#;
"""

stmt3_code = """
  A[i][j] = `x:rhs`[i][j] + C[j][k] - #_#;
"""

stmts = [parse_statement(code) for code in [stmt1_code, stmt2_code, stmt3_code]]

expr1_code = "`x:rhs`[i][j]"
expr2_code = "`x:rhs`[i][j] + `x:rhs`[i][j]"
expr3_code = "`x:rhs`[i][j] + `x:rhs`[i][j] * C[j][k]"

exprs = [parse_expression(code) for code in [expr1_code, expr2_code, expr3_code]]

# skeleton
skeleton = parse_skeleton(skeleton_code)
print(skeleton.pprint())

# pattern
stmt_populator = Populator()
stmt_populator.add('stmts1', stmts)
stmt_populator.add('stmts2', stmts)

skeleton = populate_stmt(skeleton, stmt_populator.populate)
print(skeleton.pprint())

expr_populator = Populator(exprs)
skeleton = populate_expr(skeleton, expr_populator.populate)
print(skeleton.pprint())

name_populator = Populator()
name_populator.add('lhs', [Var('A')])
name_populator.add('rhs', [Var('B'), Var('C')])
skeleton = populate_name(skeleton, name_populator.populate)
print(skeleton.pprint())
