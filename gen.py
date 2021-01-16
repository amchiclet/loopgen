from parser import parse_str
from pattern_generator import generate_pattern_v2, PatternInfo
from abstract_ast import Declaration
import copy
import sys
from pathlib import Path

def create_pattern_info():
    mul_consts = ['a1', 'a2', 'a3']
    add_consts = ['b1', 'b2', 'b3']
    data_consts = ['f1', 'f2', 'f3']
    loop_vars = ['i1', 'i2', 'i3']
    decls = [
        Declaration('A', 3),
        Declaration('B', 3),
        Declaration('C', 3),
        Declaration('D', 3),
        Declaration('E', 3),
    ]
    ops = ['+', '*', '-']
    n_loops = 1
    n_depth = 3
    n_stmts = 2
    n_ops = 1
    pattern_info = PatternInfo(decls, mul_consts, add_consts,
                               data_consts, ops,
                               loop_vars, n_loops,
                               n_depth, n_stmts, n_ops)
    return pattern_info


pattern_info = create_pattern_info()
pattern = generate_pattern_v2(pattern_info)
print(pattern.pprint())
