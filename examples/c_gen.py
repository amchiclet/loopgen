from pattern import parse_str as parse_pattern
from instance import create_instance_with_fixed_size
from codegen.c_generator import generate_code

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

# Generates code in the my_output_dir directory
# Once the files are generated, set the CC environment variable
# to use a C compiler, then run make.
generate_code('my_output_dir', instance)
