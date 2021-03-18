from skeleton import parse_str as parse_skeleton
from skeleton_ast import Op
from populator import PopulateParameters, populate_op

# An operation hole is surrounded by @.
# The usage is the same as the name hole, except where it may appear in the AST.
code = """
declare A[];
declare B[];
declare C[];

for [i] {
  A[i] = A[i] @_@ B[i] @_@ C[i];
}
"""

skeleton = parse_skeleton(code)
print(skeleton.pprint())

# Op nodes as options.
parameters = PopulateParameters()
parameters.add('_', [Op('+'), Op('-'), Op('*'), Op('/')])

filled_skeleton = populate_op(skeleton, parameters.populate)
print(filled_skeleton.pprint())
