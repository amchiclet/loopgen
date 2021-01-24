from loguru import logger

space_per_indent = 2

class Replacer:
    def should_replace(self, node):
        raise NotImplementedError(type(self))
    def replace(self, node):
        raise NotImplementedError(type(self))

class Node:
    def replace(self, replacer):
        raise NotImplementedError(type(self))

class Const(Node):
    def __init__(self, name):
        self.name = name
    def pprint(self, indent=0):
        ws = space_per_indent * indent * ' '
        return f'{ws}const {self.name};'
    def replace(self, replacer):
        self.name = replace(self.name, replacer)

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

class Literal(Node):
    def __init__(self, ty, val):
        self.ty = ty
        self.val = val
    def pprint(self, indent=0):
        return f'{self.val}'
    def replace(self, replacer):
        self.ty = replace(self.ty, replacer)
        self.val = replace(self.val, replacer)

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

class Assignment(Node):
    def __init__(self, lhs, rhs):
        assert(type(lhs) == Access)
        self.lhs = lhs
        self.rhs = rhs
    def pprint(self, indent=0):
        ws = space_per_indent * indent * ' '
        return f'{ws}{self.lhs.pprint()} = {self.rhs.pprint()};'
    def replace(self, replacer):
        self.lhs, self.rhs = replace_each([self.lhs, self.rhs], replacer)

def replace(i, replacer):
    if replacer.should_replace(i):
        return replacer.replace(i)
    else:
        if isinstance(i, Node):
            i.replace(replacer)
        return i

def replace_each(l, replacer):
    return [replace(i, replacer) for i in l]

def is_hole(name):
    return name.startswith('`') and name.endswith('`')

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
        return f'{pprint_maybe_hole(self.var)}{"".join(list_of_pprint)}'
    def replace(self, replacer):
        self.var = replace(self.var, replacer)
        self.indices = replace_each(self.indices, replacer)

def greater_eq_const_name(loop_var):
    return f'{loop_var}_greater_eq'
def less_eq_const_name(loop_var):
    return f'{loop_var}_less_eq'

def is_default_greater_eq(loop_var, expr):
    return \
        type(expr) == Access and \
        expr.is_scalar() and \
        expr.var == greater_eq_const_name(loop_var)
def is_default_less_eq(loop_var, expr):
    return \
        type(expr) == Access and \
        expr.is_scalar() and \
        expr.var == less_eq_const_name(loop_var)
def is_default_step(expr):
    return \
        type(expr) == Literal and \
        expr.ty == int and \
        expr.val == 1

class LoopTrait:
    def find_stmt(self, stmt):
        return self.body.index(stmt)
    def remove_stmt(self, stmt):
        self.body.remove(stmt)
    def insert_stmts(self, i, stmts):
        self.body[i:i] = stmts
        for stmt in stmts:
            stmt.surrounding_loop = self

class AbstractLoop(Node, LoopTrait):
    def __init__(self, loop_vars, body):
        self.loop_vars = loop_vars
        self.body = body

    def pprint(self, indent=0):
        ws = space_per_indent * indent * ' '
        loop_vars = [var.pprint() for var in self.loop_vars]
        header = f'{ws}for [{", ".join(loop_vars)}] {{'
        body = [f'{stmt.pprint(indent+1)}' for stmt in self.body]
        end = f'{ws}}}'
        return '\n'.join([header] + body + [end])
    def replace(self, replacer):
        self.loop_vars = replace_each(self.loop_vars, replacer)
        self.body = replace_each(self.body, replacer)

class Expr(Node):
    def __init__(self, actions):
        self.actions = actions
    def pprint(self, indent=0):
        return ' '.join(action.pprint() for action in self.actions)
    def replace(self, replacer):
        self.actions = replace_each(self.actions, replacer)

class Action(Node):
    def __init__(self, op, access):
        self.op = op
        self.access = access
    def pprint(self, indent=0):
        if self.op is not None:
            return f'{self.op} {self.access.pprint()}'
        else:
            return self.access.pprint()
    def replace(self, replacer):
        self.access = replace(self.access, replacer)

class Paren(Node):
    def __init__(self, expr):
        self.expr = expr
    def pprint(self, indent=0):
        return f'({self.expr.pprint()})'
    def replace(self, replacer):
        self.expr = replace(self.expr, replacer)

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

def populate(program, populate_function):
    replacer = Populator(populate_function)
    return replace(program, replacer)

class Populator(Replacer):
    def __init__(self, populate_function):
        self.populate_function = populate_function
    def should_replace(self, name):
        return type(name) == str and is_hole(name)
    def replace(self, name):
        return self.populate_function(name)

    
