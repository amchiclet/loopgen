from pattern import parse_str, parse_stmt_str, parse_expr_str
from instance import try_create_instance
from constant_assignment import VariableMap
from type_assignment import TypeAssignment
from codegen.c_generator import generate_code
from populator import PopulateParameters, populate_stmt, populate_expr
from random import randint
from pathlib import Path

############################
# Step 1: Prepare skeleton #
############################

# This skeleton defines two scalars: I and J.
#
# It also defines 3 arrays:
# 1. Array A has 2 dimensions.
#    Let the library determine the size of the first dimension.
#    The second dimension has size J.
# 2. Array B has 2 dimensions.
#    The first dimension has size I.
#    Let the library determine the size of the second dimension.
# 3. Array C has 2 dimensions.
#    Let the library determine the size of both dimensions.
#
# It has a doubly nested loops whose loop variables are i and j.
#
# Loop i counts from low to high which are specified through
# the expression holes #_:low# and #_:high#.
#
# Expression holes have the form #name:family_name#.
# In this case, the name of the hole is unspecified, but the family
# names are "low" and "high".
#
# The user will tell the library what are the possible expressions
# for the family names "low" and "high".
#
# Because the names are unspecified, they don't need to have the same
# value when the holes are filled. (They could still randomly end up
# with the same value though.)
#
# Next, within the loop there are 4 statement holes.
#
# The first two holes $_:s1$ and $_:s1$ tells the library to fill in
# the statements from s1 pool. Again, the user tells the library
# what are possible statements for s1.
#
# The other two holes $x:s2$ and $x:s2$ tells the library to fill in
# the statements from the s2 pool. Moreover, it tells the library that
# the name of these holes are x. Both holes are x, which means that
# whatever the library populates, they need to be the same.

skeleton_code = """
declare I;
declare J;
declare A[][J];
declare B[I][];
declare C[][];

for [(i, >=#_:low#, <=#_:high#), (j, >=#_:low#, <=#_:high#)] {
  $_:s1$
  $_:s1$
  $x:s2$
  $x:s2$
}
"""

# Parse string so we have an AST that can be used later.
skeleton = parse_str(skeleton_code)
print(skeleton.pprint())

######################################
# Step 2: Fill in the skeleton holes #
######################################

# First, let's populate the statement holes
def populate_stmts(node):
    # Possible statements for family s1
    stmts1 = [parse_stmt_str(s) for s in ['A[i][j] = A[i][j] + 5.0;',
                                          'B[i][j] = B[i][j] + 5.0;',
                                          'C[i][j] = C[i][j] + 5.0;']]
    # Possible statements for family s2
    stmts2 = [parse_stmt_str(s) for s in ['A[i][j] = B[i][j] + C[i][j];',
                                          'B[i][j] = A[i][j] + C[i][j];',
                                          'C[i][j] = A[i][j] + B[i][j];']]

    # Tell the library to use stmts1 as the statement pool for s1 and
    # stmts2 as the pool for s2
    params = PopulateParameters()
    params.add('s1', stmts1)
    params.add('s2', stmts2)

    # populate_stmt populates the statement holes in the skeleton The
    # function expects a skeleton and the populating function.
    # If the user uses PopulateParameters, they can use
    # PopulateParameters.populate as the populating function.
    return populate_stmt(skeleton, params.populate)

skeleton = populate_stmts(skeleton)
print(skeleton.pprint())

# Next, let's populate the expression holes
def populate_exprs(skeleton):
    # The use can choose not to use PopulateParameters and write a
    # populating function directly.
    def populate(node):
        if node.family_name == 'low':
            return parse_expr_str(str(randint(0, 500)))
        elif node.family_name == 'high':
            return parse_expr_str(str(randint(500, 1000)))
        else:
            return parse_expr_str(str(randint(0, 1000)))
    # Use the function above to populate the expressions in the
    # skeleton.
    return populate_expr(skeleton, populate)

skeleton = populate_exprs(skeleton)
print(skeleton.pprint())

##################################
# Step 3: Generate the C program #
##################################

# There is still some missing information in order to generate a
# complete C program: First, remember there are some array dimensions
# whose size we left unspecified. Second, we haven't specified the
# types of the variables we are using.
#
# We will now convert a completed skeleton into an "instance". An
# instance is an object that has enough information to generate C
# programs.
#
# Variable map specifies what's the possible range of values of
# variables. With this information, the library can analyze the
# program to determine the array sizes and check for validity..
#
# For example, suppose we have the program
#
# declare N;
# declare X[][N];
# for [(i, i>=10, i<=50)] {
#   X[i][100] = 0.0;
# }
#
# The library can now figure out that the first dimension of X needs
# to have size at least 51. Also if N is less than 101, there can be
# an array out of bound and the program is invalid.

# Variable maps let us specify variable values.
# In this case we fix I to 800 and J to 1100, but we can also specify
# ranges.
var_map = VariableMap()
var_map.set_value('I', 800)
var_map.set_value('J', 900)

# TypeAssignment assigns types to variables.
types = TypeAssignment(default_types=['int'])
types.set('A', 'double')
types.set('B', 'double')
types.set('C', 'double')

# try_create_instance analyzes the array sizes and validity.
# If it can prove that the program is invalid, it will return None.
instance = try_create_instance(skeleton, var_map, types)
print(instance.pprint())

# Finally generate C code. Here we specify how values are initialized
# in the C code.
#
# Note that I and J need to match up with what we specified in
# VariableMap above. In other words, we promised the library that I
# and J will have these values and it said that the program is valid,
# so we should actually use these values when initializing I and J.
init_value_map = {
    'A': 'drand(0.0, 1.0)',
    'B': 'drand(0.0, 1.0)',
    'C': 'drand(0.0, 1.0)',
    'I': '800',
    'J': '900',
}

dst_dir = 'output'
Path(dst_dir).mkdir(parents=True, exist_ok=True)
generate_code(dst_dir, instance, init_value_map=init_value_map, template_dir='codegen')
