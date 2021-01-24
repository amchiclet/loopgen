from skeleton import parse_str
from skeleton_ast import populate
from random import choice

code = """
declare A[][];
declare B[][];
declare C[][];

for [i, j, k] {
  C[i][j] = C[i][j] + `_`[i][k] * `_`[k][j];
}
"""

ast = parse_str(code)

def populate_function(hole_name):
    if hole_name == '`_`':
        return choice(['A', 'B'])
    assert(False)

print(ast.pprint())
ast = populate(ast, populate_function)
print(ast.pprint())
