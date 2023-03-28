from random import randint
from api import Skeleton, Mapping, CodegenConfig

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
skeleton = Skeleton(skeleton_code)
print(skeleton)

######################################
# Step 2: Fill in the skeleton holes #
######################################

# First, let's populate the statement holes
def populate_stmts(skeleton):
    # Possible statements for family s1
    stmts1 = ['A[i][j] = A[i][j] + 5.0;',
              'B[i][j] = B[i][j] + 5.0;',
              'C[i][j] = C[i][j] + 5.0;']
    # Possible statements for family s2
    stmts2 = ['A[i][j] = B[i][j] + C[i][j];',
              'B[i][j] = A[i][j] + C[i][j];',
              'C[i][j] = A[i][j] + B[i][j];']

    # Tell the library to use stmts1 as the statement pool for s1 and
    # stmts2 as the pool for s2
    mappings = [
        Mapping('s1', stmts1),
        Mapping('s2', stmts2),
    ]

    # fill_statements populates the statement holes in the skeleton.
    return skeleton.fill_statements(mappings)

skeleton = populate_stmts(skeleton)
print(skeleton)

# Next, let's populate the expression holes.
# This is similar to how we populate statements.
def populate_exprs(skeleton):
    low = [f'{randint(0, 500)}' for _ in range(3)]
    high = [f'{randint(500, 1000)}' for _ in range(3)]

    mappings = [
        Mapping('low', low),
        Mapping('high', high)
    ]

    return skeleton.fill_expressions(mappings)

skeleton = populate_exprs(skeleton)
print(skeleton)

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
# program to determine the array sizes and check for validity.
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

config = CodegenConfig()

# config.possible_values lets us specify variable values.
# In this case we fix I to 800 and J to 1100, but we can also specify
# ranges.
config.possible_values = {
    'I': 1800,
    'J': 1500,
}

# config.types assigns types to variables.
config.types = {
    'A': 'double',
    'B': 'double',
    'C': 'double',
}

# Next, we specify how values are initialized in the C code with
# config.initial_values.
#
# Note that I and J need to match up with what we specified in
# config.possible_values above. In other words, we promised the
# library that I and J will have these values and it said that the
# program is valid, so we should actually use these values when
# initializing I and J.
config.initial_values = {
    'A': 'drand(0.0, 1.0)',
    'B': 'drand(0.0, 1.0)',
    'C': 'drand(0.0, 1.0)',
    'I': '1800',
    'J': '1500',
}

# The library uses templated strings to generate C code and provides
# some templates.  Here we use codelet-template-int-inputs as the
# template. The actualy template can be viewed by going to that
# directory. The template allows the generated program to accept int
# parameters from the command line. For this example, inputs from the
# command line are not used though.
config.template_dir = 'codelet-template-int-inputs'

# Finally, specify the output directory.
config.output_dir = 'output'

skeleton.generate_code(config)

# Some C code should now be generated at the directory output.
# Assuming you have gcc,
# $ cd output
# $ make
# $ ./run
