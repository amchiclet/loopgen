from skeleton import \
    parse_str as parse_skeleton, \
    parse_stmt_str as parse_stmt
from pattern import parse_str as parse_pattern
from populator import PopulateParameters, populate_stmt

# A pattern belongs to a slightly different syntax than skeletons.
# In particular, there are no holes in patterns.
# See pattern.py for its grammar.
#
# When you're finished filling all holes in a skeleton,
# you can pass parse its string representation to get a pattern.

def create_full_skeleton():
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

    stmt_codes = [
        'A[i] = 1;',
        'A[i] = B[i] + C[i];',
        'A[i] = 5 * D[i];',
    ]
    parameters = PopulateParameters()
    parameters.add('_', [parse_stmt(code) for code in stmt_codes])

    filled_skeleton = populate_stmt(skeleton, parameters.populate)
    print(filled_skeleton.pprint())
    return filled_skeleton

full_skeleton = create_full_skeleton()

# Get the string representation of the skeleton.
full_skeleton_str = full_skeleton.pprint()

# A skeleton that still has holes would fail while parsing.
pattern = parse_pattern(full_skeleton_str)

# The string representation of a pattern matches that of a
# full skeleton, but it's represented with a different AST
# in memory. A pattern is used to create an instance, which
# has more useful information to generate runnable code.
print(pattern.pprint())
