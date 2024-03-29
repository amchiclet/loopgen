from loguru import logger

space_per_indent = 2

# TODO: make this non-global
array_as_ptr = False

def is_list_syntactically_equal(list1, list2):
    if len(list1) != len(list2):
        return False
    for i1, i2 in zip(list1, list2):
        if not i1.is_syntactically_equal(i2):
            return False
    return True

class Replacer:
    def should_replace(self, node):
        raise NotImplementedError(type(self))
    def should_skip(self, node):
        raise NotImplementedError(type(self))
    def replace(self, node):
        raise NotImplementedError(type(self))

class Node:
    # clone the node including the node ids
    def clone(self):
        raise NotImplementedError(type(self))
    def is_syntactically_equal(self, other):
        raise NotImplementedError(type(self))
    def precedence(self):
        raise NotImplementedError(type(self))
    def replace(self, replacer, dfs=False):
        raise NotImplementedError(type(self))
    def pprint(self):
        raise NotImplementedError(type(self))
    def __str__(self):
        return self.pprint()

class Const(Node):
    def __init__(self, name, attributes=None):
        self.name = name
        self.attributes = {} if attributes is None else attributes
    def pprint(self, indent=0):
        ws = space_per_indent * indent * ' '
        return f'{ws}const {self.name};'
    def clone(self):
        return Const(self.name, self.attributes.copy())
    def is_syntactically_equal(self, other):
        return type(other) == Const and self.name == other.name
    def replace(self, replacer, dfs=False):
        self.name = replace(self.name, replacer, dfs)

class Declaration(Node):
    def __init__(self, name, n_dimensions, sizes=None, is_local=False, ty=None, attributes=None):
        self.name = name
        self.n_dimensions = n_dimensions
        if sizes is None:
            self.sizes = [None] * n_dimensions
        else:
            self.sizes = sizes
        self.is_local = is_local
        self.ty = ty
        self.attributes = {} if attributes is None else attributes
    def pprint(self, indent=0):
        localness = 'local' if self.is_local else 'declare'
        ty = ' ' if self.ty is None else f' {self.ty} '
        ws = space_per_indent * indent * ' '
        dimensions = [f'[{size.pprint() if size is not None else ""}]' for size in self.sizes]
        return f'{ws}{localness}{ty}{self.name}{"".join(dimensions)};'
    def clone(self):
        return Declaration(self.name, self.n_dimensions,
                           list(self.sizes), self.is_local, self.ty,
                           self.attributes.copy())
    def is_syntactically_equal(self, other):
        return (
            type(other) == Declaration and
            self.name == other.name and
            self.n_dimensions == other.n_dimensions and
            self.is_local == other.is_local and
            self.sizes == other.sizes
        )
    def replace(self, replacer, dfs=False):
        self.name = replace(self.name, replacer, dfs)
        self.sizes = replace_each(self.sizes, replacer, dfs)

class Literal(Node):
    def __init__(self, ty, val, attributes=None):
        self.ty = ty
        self.val = val
        self.attributes = {} if attributes is None else attributes
    def pprint(self, indent=0):
        return f'{self.val}'
    def clone(self):
        return Literal(self.ty, self.val, self.attributes.copy())
    def is_syntactically_equal(self, other):
        return self.ty == other.ty and self.val == other.val
    def replace(self, replacer, dfs=False):
        self.ty = replace(self.ty, replacer, dfs)
        self.val = replace(self.val, replacer, dfs)
    def dep_print(self, refs):
        return f'{self.val}'

class Hex(Literal):
    def __init__(self, str_val, attributes=None):
        self.ty = bytes
        self.str_val = str_val
        self.val = bytes.fromhex(str_val[2:])  # remove the 0x
        self.attributes = {} if attributes is None else attributes
    def pprint(self, indent=0):
        return f'{self.str_val}'
    def clone(self):
        return Hex(self.str_val, self.attributes.copy())
    def is_syntactically_equal(self, other):
        return (type(other) == Hex and
                self.ty == other.ty and
                self.val == other.val)
    def replace(self, replacer, dfs=False):
        self.ty = replace(self.ty, replacer, dfs)
        self.val = replace(self.val, replacer, dfs)
        self.str_val = replace(self.str_val, replacer, dfs)
    def dep_print(self, refs):
        return f'{self.str_val}'

class NoOp(Node):
    def __init__(self, attributes=None):
        self.surrounding_loop = None
        self.attributes = {} if attributes is None else attributes
    def pprint(self, indent=0):
        ws = space_per_indent * indent * ' '
        return f'{ws};'
    def dep_print(self, refs):
        return f';'
    def clone(self):
        return NoOp()
    def is_syntactically_equal(self, other):
        return type(other) == NoOp
    def replace(self, replacer, dfs=False):
        pass
    def clone(self):
        return NoOp(self.attributes.copy())

class Assignment(Node):
    def __init__(self, lhs, rhs, attributes=None):
        self.lhs = lhs
        self.lhs.is_write = True
        self.rhs = rhs
        self.surrounding_loop = None
        for access in get_accesses(self):
            access.parent_stmt = self
            for index in access.indices:
                index.parent_stmt = self
        self.attributes = {} if attributes is None else attributes
    def pprint(self, indent=0):
        ws = space_per_indent * indent * ' '
        return f'{ws}{self.lhs.pprint()} = {self.rhs.pprint()};'
    def dep_print(self, refs):
        return f'{self.lhs.dep_print(refs)} = {self.rhs.dep_print(refs)};'
    def clone(self):
        cloned = Assignment(self.lhs.clone(), self.rhs.clone(), self.attributes.copy())
        return cloned
    def is_syntactically_equal(self, other):
        return (
            type(other) == Assignment and
            self.lhs.is_syntactically_equal(other.lhs) and
            self.rhs.is_syntactically_equal(other.rhs)
        )
    def replace(self, replacer, dfs=False):
        self.lhs, self.rhs = replace_each([self.lhs, self.rhs], replacer, dfs)
        for access in get_accesses(self):
            access.parent_stmt = self
            for index in access.indices:
                index.parent_stmt = self

def replace(i, replacer, dfs=False):
    if dfs:
        if isinstance(i, Node):
            i.replace(replacer, dfs)

    if replacer.should_skip(i):
        return i

    # replace this node otherwise recurse
    if replacer.should_replace(i):
        return replacer.replace(i)

    if not dfs:
        if isinstance(i, Node):
            i.replace(replacer, dfs)

    return i

def replace_each(l, replacer, dfs=False):
    return [replace(i, replacer, dfs) for i in l]

class Access(Node):
    def __init__(self, var, indices=None, attributes=None):
        self.var = var
        self.indices = indices if indices else []
        self.is_write = False
        self.parent_stmt = None
        self.attributes = {} if attributes is None else attributes
    def is_scalar(self):
        return len(self.indices) == 0
    def pprint(self, indent=0):
        if self.is_scalar() or not array_as_ptr:
            name = self.var
        else:
            name = f'(*{self.var})'
        list_of_pprint = [f'[{index.pprint()}]' for index in self.indices]
        return f'{name}{"".join(list_of_pprint)}'
    def dep_print(self, refs):
        from termcolor import colored
        if self in refs:
            return colored(f'{self.pprint()}', 'green')
        else:
            return self.pprint()
    def clone(self):
        cloned_indices = [i.clone() for i in self.indices]
        cloned = Access(self.var, cloned_indices, self.attributes.copy())
        cloned.is_write = self.is_write
        return cloned
    def is_syntactically_equal(self, other):
        return (
            type(other) == Access and
            self.var == other.var and
            is_list_syntactically_equal(self.indices, other.indices)
        )
    def replace(self, replacer, dfs=False):
        self.var = replace(self.var, replacer, dfs)
        self.indices = replace_each(self.indices, replacer, dfs)

class LoopShapeBuilder:
    def __init__(self):
        self.loop_var = None
        self.greater_eq = None
        self.less_eq = []
        self.step = None
    def set_shape_part(self, expr, prefix=None):
        if prefix is None:
            self.loop_var = expr
        elif prefix == '>=':
            self.greater_eq = expr
        elif prefix == '<=':
            self.less_eq = [expr]
        elif prefix == '+=':
            self.step = expr
        else:
            raise RuntimeError(f'Unsupported prefix ({prefix})')
    def merge(self, other):
        if other.loop_var is not None:
            assert(self.loop_var is None)
            self.loop_var = other.loop_var
        if other.less_eq is not None:
            self.less_eq += other.less_eq
        if other.greater_eq is not None:
            assert(self.greater_eq is None)
            self.greater_eq = other.greater_eq
        if other.step is not None:
            assert(self.step is None)
            self.step = other.step
    def build(self, default_greater_eq, default_less_eq, default_step):
        assert(self.loop_var is not None)
        loop_var = self.loop_var
        greater_eq = self.greater_eq if self.greater_eq is not None else default_greater_eq
        less_eq = self.less_eq if len(self.less_eq) > 0 else [default_less_eq]
        step = self.step if self.step is not None else default_step
        return LoopShape(loop_var, greater_eq, less_eq, step)

def greater_eq_const_name(loop_var):
    return f'{loop_var}_greater_eq'
def less_eq_const_name(loop_var):
    return f'{loop_var}_less_eq'

def is_default_greater_eq(loop_var, expr):
    return \
        type(expr) == Access and \
        expr.is_scalar() and \
        expr.var == greater_eq_const_name(loop_var)
def is_default_less_eq(loop_var, exprs):
    return (
        len(exprs) == 1 and
        type(exprs[0]) == Access and
        exprs[0].is_scalar() and \
        exprs[0].var == less_eq_const_name(loop_var)
    )
def is_default_step(expr):
    return \
        type(expr) == Literal and \
        expr.ty == int and \
        expr.val == 1

class LoopShape(Node):
    def __init__(self, loop_var, greater_eq, less_eq, step):
        self.loop_var = loop_var
        self.greater_eq = greater_eq
        self.less_eq = less_eq
        self.step = step
    def clone(self):
        return LoopShape(self.loop_var.clone(),
                         self.greater_eq.clone(),
                         [expr.clone() for expr in self.less_eq],
                         self.step.clone())
    def pprint(self):
        parts = []
        parts.append(self.loop_var.pprint())
        loop_var_name = self.loop_var.var
        if not is_default_greater_eq(loop_var_name, self.greater_eq):
            parts.append(f'>={self.greater_eq.pprint()}')
        if not is_default_less_eq(loop_var_name, self.less_eq):
            for expr in self.less_eq:
                parts.append(f'<={expr.pprint()}')
        if not is_default_step(self.step):
            parts.append(f'+={self.step.pprint()}')
        if len(parts) == 1:
            return parts[0]
        else:
            return '(' + ', '.join(parts) + ')'

    def is_syntactically_equal(self, other):
        return (
            type(other) == LoopShape and
            self.loop_var.is_syntactically_equal(other.loop_var) and
            self.greater_eq.is_syntactically_equal(other.greater_eq) and
            is_list_syntactically_equal(self.less_eq, other.less_eq) and
            self.step.is_syntactically_equal(other.step)
        )
    def replace(self, replacer, dfs=False):
        self.loop_var = replace(self.loop_var, replacer, dfs)
        self.greater_eq = replace(self.greater_eq, replacer, dfs)
        self.less_eq = replace_each(self.less_eq, replacer, dfs)
        self.step = replace(self.step, replacer, dfs)

class LoopTrait():
    def find_stmt(self, stmt):
        return self.body.index(stmt)
    def remove_stmt(self, stmt):
        self.body.remove(stmt)
    def insert_stmts(self, i, stmts):
        self.body[i:i] = stmts
        for stmt in stmts:
            stmt.surrounding_loop = self
    def append_stmt(self, stmt):
        self.body.append(stmt)
        stmt.surrounding_loop = self
    def replace_body(self, stmts):
        self.body = []
        for stmt in stmts:
            self.append_stmt(stmt)

class AbstractLoop(Node, LoopTrait):
    def __init__(self, loop_shapes, body, attributes=None):
        self.loop_shapes = loop_shapes
        for loop_shape in loop_shapes:
            for access in get_accesses(loop_shape):
                access.parent_stmt = self
        self.body = body
        self.surrounding_loop = None
        for stmt in body:
            stmt.surrounding_loop = self
        self.attributes = {} if attributes is None else attributes
    def pprint(self, indent=0):
        ws = space_per_indent * indent * ' '
        loop_vars = []
        shapes = [shape.pprint() for shape in self.loop_shapes]
        header = f'{ws}for [{", ".join(shapes)}] {{'
        body = [f'{stmt.pprint(indent+1)}' for stmt in self.body]
        end = f'{ws}}}'
        return '\n'.join([header] + body + [end])
    def clone(self):
        cloned_loop_shapes = [shape.clone() for shape in self.loop_shapes]
        cloned_body = [stmt.clone() for stmt in self.body]
        cloned_loop = AbstractLoop(cloned_loop_shapes, cloned_body, self.attributes.copy())
        return cloned_loop
    def is_syntactically_equal(self, other):
        return (
            type(other) == AbstractLoop and
            is_list_syntactically_equal(self.loop_shapes, other.loop_shapes) and
            is_list_syntactically_equal(self.body, other.body)
        )
    def replace(self, replacer, dfs=False):
        self.loop_shapes = replace_each(self.loop_shapes, replacer, dfs)
        self.body = replace_each(self.body, replacer, dfs)
        for stmt in self.body:
            stmt.surrounding_loop = self

class Op(Node):
    def __init__(self, op, args, attributes=None):
        self.op = op
        self.args = args
        self.attributes = {} if attributes is None else attributes
    def precedence(self):
        if len(self.args) == 1:
            return 200
        if self.op in ['*', '/', '%'] or type(self.op) == OpHole:
            return 150
        if self.op in ['+', '-']:
            return 140
        if self.op == '<<' or self.op == '>>':
            return 130
        if self.op in ['<', '>', '<=', '>=']:
            return 120
        if self.op in ['==', '!=']:
            return 110
        if self.op == '&':
            return 100
        if self.op == '^':
            return 95
        if self.op == '|':
            return 93
        if self.op == '&&':
            return 90
        if self.op == '||':
            return 80
        if self.op == '?:':
            return 70
        raise RuntimeError(f'Unsupported op {self.op}')
    def generic_print(self, formatter):
        args = []
        for arg in self.args:
            arg_str = formatter(arg)
            is_atom = type(arg) in [Access, Literal, ExpressionHole]
            if not is_atom and self.precedence() >= arg.precedence():
                arg_str = f'({arg_str})'
            args.append(arg_str)
        if len(args) == 1:
            return f'{self.op}{args[0]}'
        elif len(args) == 2:
            if isinstance(self.op, Node):
                op = self.op.pprint()
            else:
                op = self.op
            return f'{args[0]} {op} {args[1]}'
        elif len(args) == 3:
            assert(self.op == '?:')
            return f'{args[0]} ? {args[1]} : {args[2]}'
        raise RuntimeError('Unsuppored argument length: {args}')

    def pprint(self, indent=0):
        def formatter(arg):
            return arg.pprint(indent)
        return self.generic_print(formatter)

    def dep_print(self, refs):
        def formatter(arg):
            return arg.dep_print(refs)
        return self.generic_print(formatter)
    def clone(self):
        cloned_args = [arg.clone() for arg in self.args]
        return Op(self.op, cloned_args, self.attributes.copy())
    def is_syntactically_equal(self, other):
        return (
            type(other) == Op and
            self.op == other.op and
            is_list_syntactically_equal(self.args, other.args)
        )
    def replace(self, replacer, dfs=False):
        if type(self.op) == OpHole:
            self.op = replace(self.op, replacer, dfs)
        self.args = replace_each(self.args, replacer, dfs)

def plus_one(expr):
    if type(expr) == int:
        return Literal(int, expr + 1)
    elif isinstance(expr, Node):
        return Op('+', [expr.clone(), Literal(int, 1)])
    else:
        raise RuntimeError(f'plus_one: unsupported type {type(expr)}')

class Program(Node, LoopTrait):
    def __init__(self, decls, body, consts, attributes=None):
        self.decls = decls
        self.body = body
        self.consts = consts

        # These fields are defined so dependence analysis
        # can proceed in a uniform way with loops
        self.surrounding_loop = None
        self.loop_shapes = []
        for stmt in body:
            stmt.surrounding_loop = self
        self.attributes = {} if attributes is None else attributes
    def is_local(self, name):
        for decl in self.decls:
            if decl.name == name:
                return decl.is_local
        return False
    def get_decl(self, name):
        for decl in self.decls:
            if decl.name == name:
                return decl
        return None
    def pprint(self, indent=0):
        body = []
        # body += [f'{decl.pprint(indent)}' for decl in self.decls]
        # body += [f'{const.pprint(indent)}' for const in self.consts]
        body += [f'{stmt.pprint(indent)}' for stmt in self.body]
        return '\n'.join(body)
    def clone(self):
        cloned_decls = [decl.clone() for decl in self.decls]
        cloned_body = [stmt.clone() for stmt in self.body]
        cloned_consts = [const.clone() for const in self.consts]
        return Program(cloned_decls, cloned_body, cloned_consts, self.attributes.copy())
    def is_syntactically_equal(self, other):
        return (
            type(other) == Program and
            is_list_syntactically_equal(self.decls, other.decls) and
            is_list_syntactically_equal(self.body, other.body) and
            is_list_syntactically_equal(self.consts, other.consts)
        )
    def merge(self, other):
        cloned = other.clone()

        consts = set()
        for const in self.consts:
            consts.add(const.name)

        var_shapes = {}
        for decl in self.decls:
            var_shapes[decl.name] = decl.n_dimensions
        # check array shapes match
        for decl in cloned.decls:
            if decl.name in var_shapes:
                if decl.n_dimensions != var_shapes[decl.name]:
                    return
        # merge declarations
        for decl in cloned.decls:
            if decl.name not in var_shapes:
                self.decls.append(decl)
        # merge constants
        for const in cloned.consts:
            if const.name not in consts:
                self.consts.append(const)
        # merge body
        self.body += cloned.body
        for stmt in cloned.body:
            stmt.surrounding_loop = self
    def replace(self, replacer, dfs=False):
        self.decls = replace_each(self.decls, replacer, dfs)
        self.consts = replace_each(self.consts, replacer, dfs)
        self.loop_shapes = replace_each(self.loop_shapes, replacer, dfs)
        self.body = replace_each(self.body, replacer, dfs)
        for stmt in self.body:
            stmt.surrounding_loop = self
    def populate_decls(self, possible_values = None):
        possible_values = {} if possible_values is None else possible_values
        accesses = get_accesses(self)
        loop_vars = gather_loop_vars(gather_loop_shapes(get_loops(self)))
        undeclared = []
        for access in accesses:
            name = access.var
            if name in loop_vars:
                continue
            if self.get_decl(name):
                continue
            undeclared.append(access)
        unique_names = set()
        unique_undeclared = []
        for access in undeclared:
            if access.var in unique_names:
                continue
            unique_names.add(access.var)
            unique_undeclared.append(access)
        unique_undeclared.sort(key = lambda access: access.var)
        # sorted_unique_undeclared = sorted(unique_undeclared, lambda access: access.var)
        for access in unique_undeclared:
            sizes = []
            n_dimensions = len(access.indices)
            for dim in range(n_dimensions):
                dim_size_key = f'{access.var}{"[]" *  (dim+1)}'
                print(dim_size_key, dim_size_key in possible_values)
                if dim_size_key not in possible_values:
                    sizes.append(None)
                    continue
                dim_size = possible_values[dim_size_key]
                if isinstance(dim_size, int):
                    sizes.append(Literal(int, dim_size))
                elif isinstance(dim_size, tuple):
                    sizes.append(Literal(int, dim_size[1]))
            decl = Declaration(access.var, len(access.indices), sizes)
            self.decls.append(decl)

def get_accesses(node, ignore_indices=False):
    accesses = set()
    if isinstance(node, Assignment):
        accesses.update(get_accesses(node.lhs, ignore_indices))
        accesses.update(get_accesses(node.rhs, ignore_indices))
        return accesses
    elif isinstance(node, NoOp):
        return accesses
    elif isinstance(node, StatementHole):
        return accesses
    elif isinstance(node, ExpressionHole):
        return accesses
    elif isinstance(node, Access):
        accesses.add(node)
        if ignore_indices:
            return accesses
        for index in node.indices:
            accesses.update(get_accesses(index, ignore_indices))
        return accesses
    elif isinstance(node, Op):
        for arg in node.args:
            accesses.update(get_accesses(arg, ignore_indices))
        return accesses
    elif isinstance(node, LoopShape):
        accesses.update(get_accesses(node.loop_var, ignore_indices))
        accesses.update(get_accesses(node.greater_eq, ignore_indices))
        for expr in node.less_eq:
            accesses.update(get_accesses(expr, ignore_indices))
        accesses.update(get_accesses(node.step, ignore_indices))
        return accesses
    elif isinstance(node, AbstractLoop):
        for shape in node.loop_shapes:
            accesses.update(get_accesses(shape, ignore_indices))
        for stmt in node.body:
            accesses.update(get_accesses(stmt, ignore_indices))
        return accesses
    elif isinstance(node, Program):
        for stmt in node.body:
            accesses.update(get_accesses(stmt, ignore_indices))
        return accesses
    elif isinstance(node, Literal):
        return accesses
    else:
        raise RuntimeError('Unhandled type of node ' + str(type(node)))

def count_ops(node, ignore_indices=False):
    if isinstance(node, Assignment):
        return count_ops(node.lhs, ignore_indices) + count_ops(node.rhs, ignore_indices)
    elif isinstance(node, NoOp):
        return 0
    elif isinstance(node, StatementHole):
        return 0
    elif isinstance(node, ExpressionHole):
        return 0
    elif isinstance(node, Access):
        if ignore_indices:
            return 0
        n_ops = 0
        for index in node.indices:
            n_ops += count_ops(index, ignore_indices)
        return n_ops
    elif isinstance(node, Op):
        n_ops = 1
        for arg in node.args:
            n_ops += count_ops(arg, ignore_indices)
        return n_ops
    elif isinstance(node, LoopShape):
        n_ops = 0
        n_ops += count_ops(node.greater_eq, ignore_indices)
        for expr in node.less_eq:
            n_ops += count_ops(expr, ignore_indices)
        n_ops += count_ops(node.step, ignore_indices)
        return n_ops
    elif isinstance(node, AbstractLoop):
        n_ops = 0
        for shape in node.loop_shapes:
            n_ops += count_ops(shape, ignore_indices)
        for stmt in node.body:
            n_ops += count_ops(stmt, ignore_indices)
        return n_ops
    elif isinstance(node, Program):
        n_ops = 0
        for stmt in node.body:
            n_ops += count_ops(stmt, ignore_indices)
        return n_ops
    elif isinstance(node, Literal):
        return 0
    else:
        raise RuntimeError('count_ops: unhandled type of node ' + str(type(node)))

def get_ordered_assignments(node):
    if isinstance(node, Assignment):
        return [node]
    elif isinstance(node, Assignment):
        return []
    elif isinstance(node, NoOp):
        return []
    elif isinstance(node, AbstractLoop):
        assignments = []
        for stmt in node.body:
            assignments += get_ordered_assignments(stmt)
        return assignments
    elif isinstance(node, Program):
        assignments = []
        for stmt in node.body:
            assignments += get_ordered_assignments(stmt)
        return assignments
    else:
        raise RuntimeError('Unhandled type of node ' + str(type(node)))

def get_loops(node):
    if isinstance(node, AbstractLoop):
        loops = {node}
        for stmt in node.body:
            loops.update(get_loops(stmt))
        return loops
    elif isinstance(node, Program):
        loops = set()
        for stmt in node.body:
            loops.update(get_loops(stmt))
        return loops
    elif isinstance(node, Assignment):
        return set()
    elif isinstance(node, StatementHole):
        return set()
    elif isinstance(node, NoOp):
        return set()
    else:
        raise RuntimeError('get_loops: Unhandled type of node ' + str(type(node)))

def get_ordered_loops(node):
    if isinstance(node, AbstractLoop):
        loops = [node]
        for stmt in node.body:
            loops += get_ordered_loops(stmt)
        return loops
    elif isinstance(node, Program):
        loops = []
        for stmt in node.body:
            loops += get_ordered_loops(stmt)
        return loops
    elif isinstance(node, Assignment):
        return []
    elif isinstance(node, StatementHole):
        return []
    elif isinstance(node, NoOp):
        return []
    else:
        raise RuntimeError('get_loops: Unhandled type of node ' + str(type(node)))

# returns a map from array name to the number of dimensions for that array
def get_arrays(program):
    arrays = {}
    for access in get_accesses(program):
        array_name = access.var
        n_dimensions = len(access.indices)
        if not array_name in arrays:
            arrays[array_name] = n_dimensions
        else:
            assert(arrays[array_name] == n_dimensions)
    return arrays

class ConstReplacer(Replacer):
    def __init__(self, replace_map):
        self.replace_map = replace_map
    def should_skip(self, node):
        return not isinstance(node, Node)
    def should_replace(self, node):
        return type(node) == Access and node.var in self.replace_map
    def replace(self, node):
        return Literal(type(self.replace_map[node.var]), self.replace_map[node.var])

class VarRenamer(Replacer):
    def __init__(self, replace_map):
        self.replace_map = replace_map
    def should_skip(self, node):
        return False
    def should_replace(self, node):
        return type(node) == str and node in self.replace_map
    def replace(self, node):
        return self.replace_map[node]

def is_zero(node):
    return type(node) == Literal and node.ty == int and node.val == 0

def is_one(node):
    return type(node) == Literal and node.ty == int and node.val == 1

class Times0(Replacer):
    def should_skip(self, node):
        return False
    def should_replace(self, node):
        if type(node) != Op or node.op != '*':
            return False
        return is_zero(node.args[0]) or is_zero(node.args[1])
    def replace(self, node):
        return Literal(int, 0)

class Plus0(Replacer):
    def should_skip(self, node):
        return False
    def should_replace(self, node):
        if type(node) != Op or node.op != '+':
            return False
        return is_zero(node.args[0]) or is_zero(node.args[1])
    def replace(self, node):
        if is_zero(node.args[0]):
            return node.args[1].clone()
        return node.args[0].clone()

class Times1(Replacer):
    def should_skip(self, node):
        return False
    def should_replace(self, node):
        if type(node) != Op or node.op != '*':
            return False
        return is_one(node.args[0]) or is_one(node.args[1])
    def replace(self, node):
        if is_one(node.args[0]):
            return node.args[1].clone()
        return node.args[0].clone()

def simplify_0s_and_1s(node):
    node.replace(Times0())
    node.replace(Times1(), dfs=True)
    node.replace(Plus0(), dfs=True)

def gather_surrounding_loops(stmt):
    def recurse(s, acc):
        outer = s.surrounding_loop
        if not outer:
            return acc
        return recurse(outer, [outer] + acc)
    return recurse(stmt, [])

def gather_loop_shapes(loops):
    loop_shapes = []
    for loop in loops:
        loop_shapes += loop.loop_shapes
    return  loop_shapes

def gather_loop_vars(loop_shapes):
    loop_vars = []
    for shape in loop_shapes:
        assert(type(shape.loop_var) == Access)
        loop_vars.append(shape.loop_var.var)
    return loop_vars

class Hole(Node):
    def __init__(self, hole_name, family_name):
        self.hole_name = hole_name
        self.family_name = family_name
    def is_hole(self):
        return True

class NameHole(Hole):
    def pprint(self, indent=0):
        return '_'
    def replace(self, replacer, dfs=False):
        pass
    def clone(self):
        return NameHole(self.hole_name, self.family_name)

class StatementHole(Hole):
    def pprint(self, indent=0):
        ws = space_per_indent * indent * ' '
        return f'{ws}${self.hole_name}:{self.family_name}$'
    def replace(self, replacer, dfs=False):
        pass
    def clone(self):
        return StatementHole(self.hole_name, self.family_name)

class ExpressionHole(Hole):
    def pprint(self, indent=0):
        return f'#{self.hole_name}:{self.family_name}#'
    def replace(self, replacer, dfs=False):
        pass
    def clone(self):
        return ExpressionHole(self.hole_name, self.family_name)

class OpHole(Hole, Op):
    def pprint(self, indent=0):
        return '@'
    def replace(self, replacer, dfs=False):
        pass
    def clone(self):
        return OpHole(self.hole_name, self.family_name)
    def precedence(self):
        return 150 # same precedence as multiplicatives
