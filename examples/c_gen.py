from pattern import parse_str as parse_pattern
from instance import create_instance_with_fixed_size

code = """
declare A[][];
declare B[][];

for [i, j] {
  A[i][j] = B[i][j] + 5;
}
"""

pattern = parse_pattern(code)
print(pattern.pprint())

instance = create_instance_with_fixed_size(pattern, 100)

# Here's a default C program generator
# Depending on the experiment being carried out, the user
# may want to write a custom generator
# See codegen/c_generator.py in case there are some re-usable functions.
from codegen.c_generator import generate_code

# Generates code in the my_output_dir directory
# Once the files are generated, set the CC environment variable
# to use a C compiler, then run make.
generate_code('my_output_dir', instance)
