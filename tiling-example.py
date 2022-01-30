from pattern import parse_str
from pattern_ast import Literal, Access, Op, AbstractLoop

code = """
declare A[][][][];

for [
(i, >=0, <=100, +=1),
(j, >=0, <=100, +=1),
(k, >=0, <=100, +=1),
(l, >=0, <=100, +=1)
] {
  A[i][j][k][l] = A[i][j][k][l] + 0.01;
}
"""

def tile_loop(loop, tile_begin, tile_sizes):
    new_shapes = []
    tile_end = tile_begin + len(tile_sizes)

    prefix = [shape.clone() for shape in loop.loop_shapes[:tile_begin]]

    tiled_big_step = []
    tiled_small_step = []
    for shape, tile_size in zip(loop.loop_shapes[tile_begin:tile_end], tile_sizes):
        tile_var = Access(shape.loop_var.var + '_tile')
        tile_step = Literal(int, tile_size)

        big = shape.clone()
        big.loop_var = tile_var.clone()
        big.step = tile_step.clone()
        tiled_big_step.append(big)

        small = shape.clone()
        small.greater_eq = tile_var.clone()
        step_minus_one = Op('-', [tile_step.clone(), Literal(int, 1)])
        small_less_eq = Op('+', [tile_var.clone(), step_minus_one])
        small.less_eq.append(small_less_eq)
        tiled_small_step.append(small)

    suffix = [shape.clone() for shape in loop.loop_shapes[tile_end:]]

    new_shapes = prefix + tiled_big_step + tiled_small_step + suffix
    new_body = [stmt.clone() for stmt in loop.body]
    new_loop = AbstractLoop(new_shapes, new_body)
    return new_loop


from api import Skeleton, CodegenConfig

original = parse_str(code)
tiled = original.clone()
tiled_loop = tile_loop(tiled.body[0], 1, [3, 5])
tiled.replace_body([tiled_loop])

config = CodegenConfig()
config.possible_values = {}
config.types = {
    'A': 'double',
}
config.initial_values = {
    'A': 'drand(0.0, 1.0)',
}
config.template_dir = 'codegen'

config.output_dir = 'output/original'
program = Skeleton(original.pprint())
program.generate_code(config)

config.output_dir = 'output/tiled'
program = Skeleton(tiled.pprint())
program.generate_code(config)
