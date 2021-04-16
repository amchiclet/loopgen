from loguru import logger

space_per_indent = 2

class Replacer:
    def should_replace(self, node):
        raise NotImplementedError(type(self))
    def should_skip(self, node):
        raise NotImplementedError(type(self))
    def replace(self, node):
        raise NotImplementedError(type(self))

class Node:
    def replace(self, replacer):
        raise NotImplementedError(type(self))
    def is_hole(self):
        return False
    def clone(self):
        raise NotImplementedError(type(self))

class Const(Node):
    def __init__(self, name):
        self.name = name
    def pprint(self, indent=0):
        ws = space_per_indent * indent * ' '
        return f'{ws}const {self.name};'
    def replace(self, replacer):
        self.name = replace(self.name, replacer)
    def clone(self):
        return Const(self.name)

class Declaration(Node):
    def __init__(self, name, n_dimensions, sizes=None, is_local=False):
        self.name = name
        self.n_dimensions = n_dimensions
        if sizes is None:
            self.sizes = [None] * n_dimensions
        else:
            self.sizes = sizes
        self.is_local = is_local
    def pprint(self, indent=0):
        localness = 'local' if self.is_local else 'declare'
        ws = space_per_indent * indent * ' '
        dimensions = [f'[{size if size is not None else ""}]' for size in self.sizes]
        return f'{ws}{localness} {self.name}{"".join(dimensions)};'
    def replace(self, replacer):
        self.name = replace(self.name, replacer)
    def clone(self):
        return Declaration(self.name, self.n_dimensions, self.sizes, self.is_local)

class Var(Node):
    def __init__(self, name):
        self.name = name
    def pprint(self, indent=0):
        return self.name
    def replace(self, replacer):
        self.name = replace(self.name, replacer)
    def clone(self):
        return Var(self.name)

class Op(Node):
    def __init__(self, name):
        self.name = name
    def pprint(self, indent=0):
        return self.name
    def replace(self, replacer):
        self.name = replace(self.name, replacer)
    def clone(self):
        return Op(self.name)

class Literal(Node):
    def __init__(self, ty, val):
        self.ty = ty
        self.val = val
    def pprint(self, indent=0):
        return f'{self.val}'
    def replace(self, replacer):
        self.ty = replace(self.ty, replacer)
        self.val = replace(self.val, replacer)
    def clone(self):
        return Literal(self.ty, self.val)

class Hex(Literal):
    def __init__(self, str_val):
        self.ty = bytes
        self.str_val = str_val
        self.val = bytes.fromhex(str_val[2:])  # remove the 0x
    def pprint(self, indent=0):
        return f'{self.str_val}'
    def replace(self, replacer):
        self.ty = replace(self.ty, replacer)
        self.val = replace(self.val, replacer)
        self.str_val = replace(self.str_val, replacer)
    def clone(self):
        return Hex(self.str_val)

class Assignment(Node):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
    def pprint(self, indent=0):
        ws = space_per_indent * indent * ' '
        return f'{ws}{self.lhs.pprint()} = {self.rhs.pprint()};'
    def replace(self, replacer):
        self.lhs, self.rhs = replace_each([self.lhs, self.rhs], replacer)
    def clone(self):
        return Assignment(self.lhs.clone(), self.rhs.clone())

class Hole(Node):
    def __init__(self, hole_name, family_name):
        self.hole_name = hole_name
        self.family_name = family_name
    def is_hole(self):
        return True

class NameHole(Hole):
    def pprint(self, indent=0):
        return '_'
    def replace(self, replacer):
        pass
    def clone(self):
        return NameHole(self.hole_name, self.family_name)

class StatementHole(Hole):
    def pprint(self, indent=0):
        ws = space_per_indent * indent * ' '
        return f'{ws}$'
    def replace(self, replacer):
        pass
    def clone(self):
        return StatementHole(self.hole_name, self.family_name)

class ExpressionHole(Hole):
    def pprint(self, indent=0):
        return f'#{self.hole_name}:{self.family_name}#'
    def replace(self, replacer):
        pass
    def clone(self):
        return ExpressionHole(self.hole_name, self.family_name)

class OpHole(Hole):
    def pprint(self, indent=0):
        return '@'
    def replace(self, replacer):
        pass
    def clone(self):
        return OpHole(self.hole_name, self.family_name)

def replace(i, replacer):
    if replacer.should_skip(i):
        return i

    if replacer.should_replace(i):
        return replacer.replace(i)

    if isinstance(i, Node):
        i.replace(replacer)
    return i

def replace_each(l, replacer):
    return [replace(i, replacer) for i in l]

def pprint_maybe_hole(name):
    return '_' if is_hole(name) else name

class Access(Node):
    def __init__(self, var, indices=None):
        self.var = var
        self.indices = indices if indices else []
    def is_scalar(self):
        return len(self.indices) == 0
    def pprint(self, indent=0):
        list_of_pprint = [f'[{index.pprint()}]' for index in self.indices]
        return f'{self.var.pprint()}{"".join(list_of_pprint)}'
    def replace(self, replacer):
        self.var = replace(self.var, replacer)
        self.indices = replace_each(self.indices, replacer)
    def clone(self):
        cloned_indices = [index.clone() for index in self.indices]
        return Access(self.var.clone(), cloned_indices)

def greater_eq_const_name(loop_var):
    return f'{loop_var}_greater_eq'
def less_eq_const_name(loop_var):
    return f'{loop_var}_less_eq'

def is_default_greater_eq(loop_var, expr):
    return greater_eq_const_name(loop_var) == expr.pprint()

def is_default_less_eq(loop_var, expr):
    return less_eq_const_name(loop_var) == expr.pprint()

def is_default_step(expr):
    return expr.pprint() == '1'

class LoopTrait:
    def find_stmt(self, stmt):
        return self.body.index(stmt)
    def remove_stmt(self, stmt):
        self.body.remove(stmt)
    def insert_stmts(self, i, stmts):
        self.body[i:i] = stmts
        for stmt in stmts:
            stmt.surrounding_loop = self

class LoopShapeBuilder:
    def __init__(self):
        self.loop_var = None
        self.greater_eq = None
        self.less_eq = None
        self.step = None
    def set_shape_part(self, expr, prefix=None):
        if prefix is None:
            self.loop_var = expr
        elif prefix == '>=':
            self.greater_eq = expr
        elif prefix == '<=':
            self.less_eq = expr
        elif prefix == '+=':
            self.step = expr
        else:
            raise RuntimeError(f'Unsupported prefix ({prefix})')
    def merge(self, other):
        if other.loop_var is not None:
            assert(self.loop_var is None)
            self.loop_var = other.loop_var
        if other.less_eq is not None:
            assert(self.less_eq is None)
            self.less_eq = other.less_eq
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
        less_eq = self.less_eq if self.less_eq is not None else default_less_eq
        step = self.step if self.step is not None else default_step
        return LoopShape(loop_var, greater_eq, less_eq, step)

class LoopShape(Node):
    def __init__(self, loop_var, greater_eq, less_eq, step):
        self.loop_var = loop_var
        self.greater_eq = greater_eq
        self.less_eq = less_eq
        self.step = step
    def clone(self):
        return LoopShape(self.loop_var.clone(),
                         self.greater_eq.clone(),
                         self.less_eq.clone(),
                         self.step.clone())
    def pprint(self):
        parts = []
        parts.append(self.loop_var.pprint())
        loop_var_name = self.loop_var.pprint()
        if not is_default_greater_eq(loop_var_name, self.greater_eq):
            parts.append(f'>={self.greater_eq.pprint()}')
        if not is_default_less_eq(loop_var_name, self.less_eq):
            parts.append(f'<={self.less_eq.pprint()}')
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
            self.less_eq.is_syntactically_equal(other.less_eq) and
            self.step.is_syntactically_equal(other.step)
        )
    def replace(self, replacer):
        self.loop_var = replace(self.loop_var, replacer)
        self.greater_eq = replace(self.greater_eq, replacer)
        self.less_eq = replace(self.less_eq, replacer)
        self.step = replace(self.step, replacer)

class AbstractLoop(Node, LoopTrait):
    def __init__(self, loop_shapes, body):
        self.loop_shapes = loop_shapes
        self.body = body

    def pprint(self, indent=0):
        ws = space_per_indent * indent * ' '
        shapes = [shape.pprint() for shape in self.loop_shapes]
        header = f'{ws}for [{", ".join(shapes)}] {{'
        body = [f'{stmt.pprint(indent+1)}' for stmt in self.body]
        end = f'{ws}}}'
        return '\n'.join([header] + body + [end])
    def replace(self, replacer):
        self.loop_shapes = replace_each(self.loop_shapes, replacer)
        new_body = []
        for stmt in self.body:
            stmts = replace(stmt, replacer)
            if type(stmts) == list:
                new_body += stmts
            else:
                new_body.append(stmts)
        self.body = new_body
    def clone(self):
        cloned_loop_shapes = [loop_var.clone() for loop_var in self.loop_shapes]
        cloned_body = [stmt.clone() for stmt in self.body]
        return AbstractLoop(cloned_loop_shapes, cloned_body)

class Expr(Node):
    def __init__(self, actions):
        self.actions = actions
    def pprint(self, indent=0):
        return ' '.join(action.pprint() for action in self.actions)
    def replace(self, replacer):
        self.actions = replace_each(self.actions, replacer)
    def clone(self):
        return Expr([action.clone() for action in self.actions])

class Action(Node):
    def __init__(self, op, access):
        self.op = op
        self.access = access
    def pprint(self, indent=0):
        if self.op is not None:
            return f'{self.op.pprint()} {self.access.pprint()}'
        else:
            return self.access.pprint()
    def replace(self, replacer):
        self.op = replace(self.op, replacer)
        self.access = replace(self.access, replacer)
    def clone(self):
        cloned_op = None if self.op is None else self.op.clone()
        return Action(cloned_op, self.access.clone())

class Paren(Node):
    def __init__(self, expr):
        self.expr = expr
    def pprint(self, indent=0):
        return f'({self.expr.pprint()})'
    def replace(self, replacer):
        self.expr = replace(self.expr, replacer)
    def clone(self):
        return Paren(self.expr.clone())

class Program(Node, LoopTrait):
    def __init__(self, decls, body, consts):
        self.decls = decls
        self.body = body
        self.consts = consts

    def pprint(self, indent=0):
        body = []
        body += [f'{decl.pprint(indent)}' for decl in self.decls]
        body += [f'{stmt.pprint(indent)}' for stmt in self.body]
        return '\n'.join(body)
    def replace(self, replacer):
        self.decls = replace_each(self.decls, replacer)
        self.consts = replace_each(self.consts, replacer)
        self.body = replace_each(self.body, replacer)
    def clone(self):
        return Program(
            [decl.clone() for decl in self.decls],
            [stmt.clone() for stmt in self.body],
            [const.clone() for const in self.consts]
        )
