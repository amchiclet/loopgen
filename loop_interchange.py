from dependence_analysis import analyze_dependence
import random

from loguru import logger
from pattern_ast import get_loops

def reorder(new_order, l):
    l[:] = [l[i] for i in new_order]

def is_positive(dv):
    for d in dv:
        if d == '>':
            return True
        if d == '<':
            return False
    return False

def iterate_direction_vectors(dependency_graph, loop):
    for deps in dependency_graph.iterate_dependences_among(loop.body):
        for dep in deps:
            yield dep.direction_vector

def randomize_loop_order(loop):
    permutation = list(range(len(loop.loop_shapes)))
    random.shuffle(permutation)
    return permutation

def is_permutable(dependence_graph, loop, new_order):
    for dv in iterate_direction_vectors(dependence_graph, loop):
        cloned = list(dv)
        reorder(new_order, cloned)
        if is_positive(cloned):
            return False
    return True

class NTries:
    def __init__(self, n):
        self.n = n
    def next(self):
        if self.n == 0:
            return False
        self.n -= 1
        return True

class LoopInterchange:
    def transform(self, pattern, tries=None):
        dependence_graph, pattern_with_ids = analyze_dependence(pattern)

        if tries is None:
            tries = NTries(10)

        while tries.next():
            cloned = pattern_with_ids.clone()
            is_legal = True
            for loop in get_loops(cloned):
                order = randomize_loop_order(loop)
                if not is_permutable(dependence_graph, loop, order):
                    is_legal = False
                    break
                reorder(order, loop.loop_shapes)
            if is_legal:
                yield cloned
