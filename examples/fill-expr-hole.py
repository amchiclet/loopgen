from skeleton import \
    parse_str as parse_skeleton, \
    parse_expr_str as parse_expr

from populator import PopulateParameters, populate_expr

# An expression hole is surrounded by #.
# The usage is the same as the name hole, except where it may appear in the AST.
code = """
declare A[];
declare B[];
declare C[];

for [i] {
  A[i] = #_#;
}
"""

skeleton = parse_skeleton(code)
print(skeleton.pprint())

# Expr nodes as options.
expr_codes = [
    'A[i] * B[i]',
    'B[i] + C[i]',
    'C[i] - D[i]',
]
parameters = PopulateParameters()
parameters.add('_', [parse_expr(code) for code in expr_codes])

filled_skeleton = populate_expr(skeleton, parameters.populate)
print(filled_skeleton.pprint())
