from abstract_ast import Op, Access, Declaration, Assignment, AbstractLoop, Const, Program, ConstReplacer, get_loops, VarRenamer, Literal, LoopShape, get_accesses, get_ordered_assignments
from pattern_normalizer import normalize_pattern, greater_eq_const_name, less_eq_const_name
import random

from pathlib import Path
import os

class IdGenerator:
    def __init__(self, current=0):
        self.current = current
    def next_id(self):
        r = self.current
        self.current += 1
        return r

class Generator:
    def __init__(self, next_id=None):
        if next_id is None:
            self.next_id = IdGenerator().next_id
        else:
            self.next_id = next_id

class IndexGenerator:
    def __init__(self, mul_consts, maybe_zero_mul_consts, add_consts, next_id=None):
        self.mul_consts = mul_consts
        self.maybe_zero_mul_consts = maybe_zero_mul_consts
        self.add_consts = add_consts
        if next_id is None:
            self.next_id = IdGenerator().next_id
        else:
            self.next_id = next_id
    def generate(self, loop_vars):
        all_mul_consts = self.mul_consts + self.maybe_zero_mul_consts
        a_str = random.choice(all_mul_consts)
        x_str = random.choice(loop_vars)
        b_str = random.choice(self.add_consts)
        a = Access(a_str, node_id=self.next_id())
        x = Access(x_str, node_id=self.next_id())
        b = Access(b_str, node_id=self.next_id())
        ax = Op('*', [a, x], node_id=self.next_id())
        if a_str in self.maybe_zero_mul_consts:
            additive = '+'
        else:
            additive = random.choice(['+', '-'])
        return Op(additive, [ax, b], node_id=self.next_id())

class AccessGenerator(Generator):
    def __init__(self, decls, float_consts, index_gen, next_id=None):
        super(AccessGenerator, self).__init__(next_id)
        self.decls = decls
        self.float_consts = float_consts
        self.index_gen = index_gen
    def generate(self, loop_vars):
        pool = self.decls + self.float_consts
        choice = random.choice(pool)
        if type(choice) == Declaration:
            indices = []
            for _ in range(choice.n_dimensions):
                indices.append(self.index_gen.generate(loop_vars))
            return Access(choice.name, indices, node_id=self.next_id())
        elif type(choice) == str:
            return Access(choice, node_id=self.next_id())
        else:
            raise RuntimeError(f'Node type not supported {type(choice)}')

class AccessGeneratorV2(Generator):
    def __init__(self, decls, float_consts, loop_var_order_space, next_id=None):
        super(AccessGeneratorV2, self).__init__(next_id)
        self.decls = decls
        self.float_consts = float_consts
        self.loop_var_order_space = loop_var_order_space
    def generate(self, access_constraints):
        pool = self.decls + self.float_consts
        choice = random.choice(pool)
        if type(choice) == Declaration:
            possible_orders = self.loop_var_order_space.get(choice.name)
            loop_var_order = random.choice(possible_orders)
            indices = [Access(name, node_id=self.next_id())
                       for name in loop_var_order]
            return Access(choice.name, indices, node_id=self.next_id())
        elif type(choice) == str:
            return Access(choice, node_id=self.next_id())
        else:
            raise RuntimeError(f'Node type not supported {type(choice)}')
        
class OpGenerator(Generator):
    def __init__(self, ops, access_gen, next_id=None):
        super(OpGenerator, self).__init__(next_id)
        self.ops = ops
        self.access_gen = access_gen
    def generate(self, n_ops, loop_vars):
        if n_ops == 0:
            return self.access_gen.generate(loop_vars)

        nodes = [None] * n_ops
        for next_op in random.choices(self.ops, k=n_ops):
            blanks = []
            for i, node in enumerate(nodes):
                if node is None:
                    blanks.append(i)
            which = random.choice(blanks)
            delete_left = False
            if which-1 < 0 or nodes[which-1] is None:
                left = self.access_gen.generate(loop_vars)
            else:
                left = nodes[which-1]
                delete_left = True
            delete_right = False
            if which+1 >= len(nodes) or nodes[which+1] is None:
                right = self.access_gen.generate(loop_vars)
            else:
                right = nodes[which+1]
                delete_right = True
            new_node = Op(next_op, [left, right], self.next_id())
            nodes[which] = new_node
            if delete_right:
                del nodes[which+1]
            if delete_left:
                del nodes[which-1]
        assert(len(nodes) == 1)
        return nodes[0]

class AssignmentGenerator(Generator):
    def __init__(self, access_gen, op_gen, next_id=None):
        super(AssignmentGenerator, self).__init__(next_id)
        self.access_gen = access_gen
        self.op_gen = op_gen
    def generate(self, n_ops, loop_vars):
        lhs = self.access_gen.generate(loop_vars)
        rhs = self.op_gen.generate(n_ops, loop_vars)
        return Assignment(lhs, rhs, self.next_id())

def loop_var_expr(loop_var, node_id):
    return Access(loop_var, node_id=node_id)
def greater_eq_expr(loop_var, node_id):
    return Access(greater_eq_const_name(loop_var), node_id=node_id)
def less_eq_expr(loop_var, node_id):
    return Access(less_eq_const_name(loop_var), node_id=node_id)
def step_expr(i, node_id):
    return Literal(int, i, node_id=node_id)

class LoopGenerator(Generator):
    def __init__(self, assignment_gen, next_id=None):
        super(LoopGenerator, self).__init__(next_id)
        self.assignment_gen = assignment_gen
    def generate(self, n_depth, n_stmts, n_ops, loop_vars):
        assert(len(loop_vars) >= n_depth)
        chosen_loop_vars = random.sample(loop_vars, k=n_depth)
        body = []
        for _ in range(n_stmts):
            stmt = self.assignment_gen.generate(n_ops, chosen_loop_vars)
            body.append(stmt)
        loop_shapes = []
        for loop_var_name in chosen_loop_vars:
            loop_var = loop_var_expr(loop_var_name, self.next_id())
            greater_eq = greater_eq_expr(loop_var_name, self.next_id())
            less_eq = less_eq_expr(loop_var_name, self.next_id())
            step = step_expr(1, self.next_id())
            loop_shape = LoopShape(loop_var, greater_eq, less_eq, step, self.next_id())
            loop_shapes.append(loop_shape)
        return AbstractLoop(loop_shapes, body, self.next_id())

class ProgramGenerator(Generator):
    def __init__(self, loop_gen, next_id=None):
        super(ProgramGenerator, self).__init__(next_id)
        self.loop_gen = loop_gen
    def generate(self, n_loops, n_depth, loop_vars, n_stmts, n_ops):
        access_gen = self.loop_gen.assignment_gen.op_gen.access_gen
        gen_decls = []
        for d in sorted(access_gen.decls, key=lambda d: d.name):
            gen_decls.append(Declaration(d.name, d.n_dimensions, d.sizes, d.is_local, node_id=self.next_id()))

        gen_loops = []
        for _ in range(n_loops):
            loop = self.loop_gen.generate(n_depth, n_stmts, n_ops, loop_vars)
            gen_loops.append(loop)

        non_consts = set()
        for decl in gen_decls:
            non_consts.add(decl.name)
        for stmt in gen_loops:
            for _, loop in get_loops(stmt).items():
                for shape in loop.loop_shapes:
                    non_consts.add(shape.loop_var.var)
        consts_set = set()
        for stmt in gen_loops:
            for access in get_accesses(stmt):
                if access.var not in non_consts:
                    consts_set.add(access.var)
        gen_consts = [Const(name, self.next_id())
                      for name in sorted(list(consts_set))]

        program = Program(gen_decls, gen_loops, gen_consts, self.next_id())
        return program

class PatternInfo:
    def __init__(self, decls=None, mul_consts=None, add_consts=None,
                 data_consts=None, ops=None, loop_vars=None,
                 n_loops=0, n_depth=0, n_stmts=0, n_ops=0,
                 maybe_zero_mul_consts=None):
        self.decls = decls if decls else []
        self.mul_consts = mul_consts if mul_consts else []
        self.add_consts = add_consts if add_consts else []
        self.data_consts = data_consts if data_consts else []
        self.loop_vars = loop_vars if loop_vars else []
        self.ops = ops if ops else []
        self.n_loops = n_loops
        self.n_depth = n_depth
        self.n_stmts = n_stmts
        self.n_ops = n_ops
        self.maybe_zero_mul_consts = maybe_zero_mul_consts if maybe_zero_mul_consts else []

    def pprint(self):
        from pprint import PrettyPrinter
        pp = PrettyPrinter(indent=2)
        lines = []
        decl_pairs = [(decl.name, decl.n_dimensions) for decl in self.decls]
        lines.append(f'decls = {pp.pformat(decl_pairs)}')
        lines.append(f'mul_consts = {pp.pformat(self.mul_consts)}')
        lines.append(f'maybe_zero_mul_consts = {pp.pformat(self.maybe_zero_mul_consts)}')
        lines.append(f'add_consts = {pp.pformat(self.add_consts)}')
        lines.append(f'data_consts = {pp.pformat(self.data_consts)}')
        lines.append(f'loop_vars = {pp.pformat(self.loop_vars)}')
        lines.append(f'n_loops = {self.n_loops}')
        lines.append(f'n_depth = {self.n_depth}')
        lines.append(f'n_stmts = {self.n_stmts}')
        lines.append(f'n_ops = {self.n_ops}')
        return '\n'.join(lines)

def generate(pattern_info):
    id_gen = IdGenerator()
    index_gen = IndexGenerator(pattern_info.mul_consts,
                               pattern_info.maybe_zero_mul_consts,
                               pattern_info.add_consts, id_gen.next_id)
    access_gen = AccessGenerator(pattern_info.decls,
                                 pattern_info.data_consts, index_gen,
                                 id_gen.next_id)
    op_gen = OpGenerator(pattern_info.ops, access_gen, id_gen.next_id)
    access_gen_lhs = AccessGenerator(pattern_info.decls, [],
                                     index_gen, id_gen.next_id)
    assign_gen = AssignmentGenerator(access_gen_lhs, op_gen,
                                     id_gen.next_id)
    loop_gen = LoopGenerator(assign_gen, id_gen.next_id)
    program_gen = ProgramGenerator(loop_gen, id_gen.next_id)
    node = program_gen.generate(pattern_info.n_loops,
                                pattern_info.n_depth,
                                pattern_info.loop_vars,
                                pattern_info.n_stmts,
                                pattern_info.n_ops)

    normalize_pattern(node, pattern_info.decls,
                      pattern_info.mul_consts,
                      pattern_info.maybe_zero_mul_consts,
                      pattern_info.add_consts,
                      pattern_info.data_consts,
                      pattern_info.loop_vars)

    return node, id_gen.current

class Space:
    def get(self, args=None):
        raise NotImplementedError(f'Space::get not implemented for {type(self)}')

class MapBasedSpace(Space):
    def __init__(self):
        self.the_map = {}
    def add(self, key, choice):
        if key not in self.the_map:
            self.the_map[key] = []
        self.the_map[key].append(choice)
    def get(self, key=None):
        assert(key is not None)
        return self.the_map[key]

class LoopGeneratorV2(Generator):
    def __init__(self, assignment_gen, next_id=None):
        super(LoopGeneratorV2, self).__init__(next_id)
        self.assignment_gen = assignment_gen
    def generate(self, n_depth, n_stmts, n_ops, loop_vars):
        assert(len(loop_vars) >= n_depth)
        chosen_loop_vars = loop_vars[:n_depth]
        body = []
        for _ in range(n_stmts):
            stmt = self.assignment_gen.generate(n_ops, chosen_loop_vars)
            body.append(stmt)
        loop_shapes = []
        for loop_var_name in chosen_loop_vars:
            loop_var = loop_var_expr(loop_var_name, self.next_id())
            greater_eq = greater_eq_expr(loop_var_name, self.next_id())
            less_eq = less_eq_expr(loop_var_name, self.next_id())
            step = step_expr(1, self.next_id())
            loop_shape = LoopShape(loop_var, greater_eq, less_eq, step, self.next_id())
            loop_shapes.append(loop_shape)
        return AbstractLoop(loop_shapes, body, self.next_id())

def generate_v2(pattern_info):
    id_gen = IdGenerator()
    index_gen = IndexGenerator(pattern_info.mul_consts,
                               pattern_info.maybe_zero_mul_consts,
                               pattern_info.add_consts, id_gen.next_id)
    loop_var_order_space = MapBasedSpace()
    for decl in pattern_info.decls:
        order = list(pattern_info.loop_vars)
        reversed_order = list(reversed(order))
        loop_var_order_space.add(decl.name, order)
        loop_var_order_space.add(decl.name, reversed_order)

    access_gen = AccessGeneratorV2(pattern_info.decls,
                                   pattern_info.data_consts,
                                   loop_var_order_space,
                                   id_gen.next_id)
    op_gen = OpGenerator(pattern_info.ops, access_gen, id_gen.next_id)
    access_gen_lhs = AccessGeneratorV2(pattern_info.decls, [],
                                       loop_var_order_space,
                                       id_gen.next_id)
    assign_gen = AssignmentGenerator(access_gen_lhs, op_gen,
                                     id_gen.next_id)
    loop_gen = LoopGeneratorV2(assign_gen, id_gen.next_id)
    program_gen = ProgramGenerator(loop_gen, id_gen.next_id)
    node = program_gen.generate(pattern_info.n_loops,
                                pattern_info.n_depth,
                                pattern_info.loop_vars,
                                pattern_info.n_stmts,
                                pattern_info.n_ops)

    return node, id_gen.current

def has_use_before_def(pattern):
    local_vars = {decl.name for decl in pattern.decls if decl.is_local}

    is_write_first = set()
    for assignment in get_ordered_assignments(pattern):
        for access in get_accesses(assignment.rhs):
            var = access.var
            if var in local_vars and var not in is_write_first:
                return True
        for access in get_accesses(assignment.lhs):
            var = access.var
            if var in local_vars:
                is_write_first.add(var)
    return False

def generate_pattern(pattern_info, max_tries=10):
    for _ in range(max_tries):
        pattern, _ = generate(pattern_info)
        if has_use_before_def(pattern):
            continue
        return pattern
    return None

def generate_pattern_v2(pattern_info, max_tries=10):
    for _ in range(max_tries):
        pattern, _ = generate_v2(pattern_info)
        if has_use_before_def(pattern):
            continue
        return pattern
    return None

def write_pattern_to_file(pattern, path):
    with open(path, 'w') as f:
        f.write(pattern.pprint())

def write_patterns_to_dir(pattern_name_pairs, output_dir):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    for pattern, name in pattern_name_pairs:
        pattern_path = os.path.join(output_dir, f'{name}.pattern')
        write_pattern_to_file(pattern, pattern_path)
