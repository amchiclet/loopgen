from dependence_analysis import analyze_dependence
from pattern_ast import get_loops, AbstractLoop
from pattern import parse_str, parse_stmt_str, parse_expr_str

from loop_tiling import tilable_loop_nests, tile_loop
from random import randint, choice

code = """
declare A[][][][][][];

for [
  (a, >=0, <=100, +=10),
  (b, >=0, <=100, +=10),
  (c, >=0, <=100, +=10),
  (d, >=0, <=100, +=10),
  (e, >=0, <=100, +=10),
  (f, >=0, <=100, +=10)
] {
  A[a][b][c+1][d][e][f] = A[a][b][c][d][e+1][f] + 1;
}
"""
program = parse_str(code)
dependence_graph, program_with_ids = analyze_dependence(program)
print('dependence graph')
print(dependence_graph)
which_nest = None

loop = program_with_ids.body[0]

tilables = [nest for nest in tilable_loop_nests(dependence_graph, loop)]
print(tilables)
tile_begin, tile_depth = choice(tilables)

tile_sizes = [randint(2, 4) for i in range(tile_depth)]
print(tile_begin, tile_sizes)

tiled = tile_loop(loop, tile_begin, tile_sizes)

print('before -----------')
print(loop)
print('after ------------')
print(tiled)

# TODO: write function to replace loop in a program with the tiled loop
# TODO: generate code
