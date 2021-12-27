from api import Skeleton, Mapping, CodegenConfig

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

expressions = [
    Mapping("low", ["10", "20", "30"]),
    Mapping("high", ["40", "50", "60"]),
]

statements = [
    Mapping("s1", ["A[i][j] = A[i][j] * 2;",
                   "A[i][j] = A[i][j] + 1;"]),
    Mapping("s2", ["B[i][j] = B[i][j] * 2;",
                   "B[i][j] = B[i][j] * 3;"]),
]

config = CodegenConfig()
config.possible_values = {
    'I': (100, 200),
    'J': (100, 200),
}
config.types = {
    'A': 'double',
    'B': 'double',
    'C': 'double',
}
config.initial_values = {
    'A': 'drand(0.0, 1.0)',
    'B': 'drand(0.0, 1.0)',
    'C': 'drand(0.0, 1.0)',
    'I': '800',
    'J': '900',
}
config.template_dir = 'codegen'
config.output_dir = 'output'

program = Skeleton(skeleton_code)
program = program.fill_expressions(expressions)
program = program.fill_statements(statements)
program.generate_code(config)
