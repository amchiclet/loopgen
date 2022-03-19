from dependence_analysis import analyze_dependence
from pattern_ast import get_loops, AbstractLoop, Access, Literal, Op
from pattern import parse_str, parse_stmt_str, parse_expr_str
from dependence_analysis import analyze_dependence, calculate_distance_vectors

def iterate_direction_vectors(dependency_graph, loop):
    for deps in dependency_graph.iterate_dependences_among(loop.body):
        for dep in deps:
            yield dep.direction_vector

def is_completely_permutable(dependence_graph, loop, start, depth):
    for dv in iterate_direction_vectors(dependence_graph, loop):
        # if anything before "start" is negative, then the nest
        # begining at "start" is interchangable
        for d in dv[:start]:
            if d == '<':
                return True
        # At this point, everything leading before "start" is = so
        # nothing in [start, start+depth) should be positive because
        # if it's positive, it can be swapped to "start" and cause the
        # interchange to be invalid.
        for d in dv[start: start+depth]:
            if d == '>':
                return False
    return True

def tilable_loop_nests(dependence_graph, loop):
    max_depth = len(loop.loop_shapes)
    whole_loop = list(range(max_depth))
    for depth in range(max_depth, 0, -1):
        for start in range(max_depth + 1 - depth):
            if is_completely_permutable(dependence_graph, loop, start, depth):
                yield (start, depth)

def tile_loop(loop, tile_begin, tile_sizes):
    new_shapes = []
    tile_end = tile_begin + len(tile_sizes)

    prefix = [shape.clone() for shape in loop.loop_shapes[:tile_begin]]

    tiled_big_step = []
    tiled_small_step = []
    for shape, tile_size in zip(loop.loop_shapes[tile_begin:tile_end], tile_sizes):
        tile_var = Access(shape.loop_var.var + '_tile')
        tile_step = Op('*', [shape.step.clone(), Literal(int, tile_size)])

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

# pick random loop


# code = """
# declare A[][];

# for [
#   (a, >=0, <=100, +=10),
#   (b, >=0, <=100, +=10)
# ] {
#   A[a][b] = 1;
# }
# """

# program = parse_str(code)
# loop = program.body[0]
# body = []
# def append_top_level(stmt):
#     body.append(stmt)

# tile_loop(append_top_level, loop, [7] * len(loop.loop_shapes), [loop], loop.body, True)
# print('result')
# for stmt in body:
#     print(stmt)

# exit()

# # tile a, b tile size = 33
# for a_tile >=0 <=100-(100%33)-1 +=33
#   for b_tile >=0 <=100-(100%33)-1 +=33
#     body
#   for b
#     body
# for a >= 100-(100%33) <=100 +=1
#   for b_tile >=0 <=100-(100%33) +=33
#     body
#   for b
#     body

