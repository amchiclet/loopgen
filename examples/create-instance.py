from pattern import parse_str as parse_pattern
from instance import create_instance, VariableMap

# A pattern may contains constant variables.
#
# Constant variables are identifiers that are not declared.
#
# The user has 2 ways to declare variables
# (1) Explicitly declare a variable with the keyword "declare".
# (2) Implicitly declare a variable in a for loop inside the square brackets.
#
# Example:

code = """
  declare A[];
  declare B[];
  for [i] {
    A[i] = B[i] + b * c + 5;
  }
"""

# The constant variables are b and c.
#
# An instance is a pattern
# (1) with no constant variables
# (2) whose array sizes are determined
#
# Hence, to create an instance, we need to
# (1) replace constant variables with literals
# (2) determine array sizes

# ***************************************
# How to replace constant variables
# ***************************************

# The library provides a way to replace constant variables with literals.
# First, the user creates a variable map which specifies the range of
# values that a constant variable will be replaced with.

var_map = VariableMap()
var_map.set_min('b', 0)
var_map.set_max('b', 5)
var_map.set_min('c', 6)
var_map.set_max('c', 10)

# This specifies that the constant variable b will be replaced with
# some value in the (inclusive) range [0, 5], and c with a value
# in the range [6, 10].
#
# Additionally, there are implcit constant variables when the loop
# bounds are not specified. The complete form of the pattern above
# is as follows.

fully_specified_loop = """
  declare A[];
  declare B[];
  for [(i, <= i_less_eq, >= i_greater_eq, += 1)] {
    A[i] = B[i] + b * c + 5;
  }
"""

# Notice that i_less_eq and i_greater_eq are the default loop bounds,
# and 1 is the default loop step.
# The user can specify how to replace i_less_eq and i_greater_eq through
# the variable map.

var_map.set_min('i_greater_eq', 0)
var_map.set_max('i_greater_eq', 0)
var_map.set_min('i_less_eq', 25)
var_map.set_max('i_less_eq', 100)

# The code above specifies that the loop bound starts exactly at 0, and
# ends at some value in the range [25, 100].

# ***************************************
# How to determine array sizes
# ***************************************

# The array size can either be specified directly by the user
# or have the library determine the size for it.
#
# The user may specify the size directly in the declare statement.

specified_array_size = """
  declare A[];
  declare B[50];
  for [(i, <= i_less_eq, >= i_greater_eq, += 1)] {
    A[i] = B[i] + b * c + 5;
  }
"""

# In the code above, the array B has size 50.
# The size of array A is left for the library to decide.
#
# Finally to create an instance, use the function create_instance.
# The function ensures that a valid instance is created.

pattern = parse_pattern(specified_array_size)
instance = create_instance(pattern, var_map)

# A valid instance only includes in-bound array accesses.
# In the code above, since array B has size 50, and there
# is an access B[i], then i_less_eq will never be greater
# than 49. If i_less_eq can be greater than 49, it means
# that the access B[i] can be out of bound.
print(instance.pprint())
