from skeleton import \
    parse_str as parse_skeleton, \
    parse_stmt_str as parse_stmt

from populator import PopulateParameters, populate_stmt

# A statement hole is surrounded by $.
# The usage is the same as the name hole, except where it may appear in the AST.
code = """
declare A[];
declare B[];
declare C[];

for [i] {
  $_$
  $_$
}
"""

skeleton = parse_skeleton(code)
print(skeleton.pprint())

# Statement nodes as options.
stmt_codes = [
    'A[i] = 1;',
    'A[i] = B[i] + C[i];',
    'A[i] = 5 * D[i];',
]
parameters = PopulateParameters()
parameters.add('_', [parse_stmt(code) for code in stmt_codes])

filled_skeleton = populate_stmt(skeleton, parameters.populate)
print(filled_skeleton.pprint())
