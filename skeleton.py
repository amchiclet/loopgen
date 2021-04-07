from lark import Lark, Transformer

# Note:
# Operator precedence is based on
# https://docs.microsoft.com/en-us/cpp/c-language/precedence-and-order-of-evaluation?view=vs-2019

#    abstract_loop: "for" "[" loop_vars "]" "{" seq "}"
#    loop_vars: access ("," access)*
grammar = '''
    start: (declaration)+ statement+

    declaration: param | local
    param: "declare" array (dimension)* ";"
    local: "local" array (dimension)* ";"
    dimension: "[" INT? "]"
    abstract_loop: "for" "[" loop_shapes "]" "{" seq "}"

    loop_shapes: loop_shape ("," loop_shape)*
    loop_shape: single_loop_shape | multi_loop_shape
    single_loop_shape: expr
    multi_loop_shape: "(" loop_shape_parts ")"
    loop_shape_parts: loop_shape_part ("," loop_shape_part)*
    loop_shape_part: LOOP_SHAPE_PREFIX? expr
    LOOP_SHAPE_PREFIX: "<=" | ">=" | "+="

    seq: statement*

    statement: assignment | abstract_loop | statement_hole
    assignment: expr "=" expr ";"
    statement_hole: "$" CNAME (":" CNAME)? "$"

    expr: action+
    action: op? atom
    op: CONDITIONAL | LOGICAL | BITWISE | EQUAL | RELATION | BITWISE_SHIFT | ADDITIVE | MULTIPLICATIVE | UNARY | op_hole
    op_hole: "@" CNAME (":" CNAME)? "@"
    atom: access | paren | expr_hole
    paren: "(" expr ")"
    expr_hole: "#" CNAME (":" CNAME)? "#"

    access: scalar_access | array_access | literal
    scalar_access: scalar
    array_access: array ("[" expr "]")+
    literal: float_literal | int_literal | hex_literal
    float_literal: FLOAT
    int_literal: INT
    hex_literal: HEX_NUMBER

    scalar: CNAME | name_hole
    array: CNAME | name_hole
    name_hole: "`" CNAME (":" CNAME)? "`"

    CONDITIONAL: "?" | ":"
    LOGICAL: "||" | "&&"
    BITWISE: "|" | "^" | "&"
    EQUAL: "==" | "!="
    RELATION: "<=" | ">=" | "<" | ">"
    BITWISE_SHIFT: "<<" | ">>"
    ADDITIVE: "+" | "-"
    MULTIPLICATIVE: "*" | "/" | "%"
    UNARY: "+" | "-" | "!" | "~"

    HEX_NUMBER: /0x[\\da-f]*/i

    COMMENT: /##[^\\n]*/
    %import common.WS
    %import common.LETTER
    %import common.DIGIT
    %import common.LCASE_LETTER
    %import common.UCASE_LETTER
    %import common.CNAME
    %import common.INT
    %import common.FLOAT
    %ignore WS
    %ignore COMMENT
'''

# _NEWLINE: ( /\r?\n[\t ]*/ | COMMENT )+


# STRING : /[ubf]?r?("(?!"").*?(?<!\\)(\\\\)*?"|'(?!'').*?(?<!\\)(\\\\)*?')/i
# LONG_STRING: /[ubf]?r?(""".*?(?<!\\)(\\\\)*?"""|'''.*?(?<!\\)(\\\\)*?''')/is

# DEC_NUMBER: /0|[1-9]\d*/i


from skeleton_ast import AbstractLoop, Assignment, Expr, Access, Action, Program, Declaration, Const, Literal, Hex, Paren, NameHole, StatementHole, ExpressionHole, Var, Hole, OpHole, Op, LoopShapeBuilder, LoopShape

class TreeSimplifier(Transformer):
    def dimension(self, args):
        if len(args) > 0:
            return int(args[0])
        else:
            return None
    def declaration(self, args):
        return args[0]
    def param(self, args):
        sizes = args[1:]
        n_dimensions = len(args) - 1
        return Declaration(args[0].name, n_dimensions, sizes, is_local=False)
    def local(self, args):
        sizes = args[1:]
        n_dimensions = len(args) - 1
        return Declaration(args[0].name, n_dimensions, sizes, is_local=True)
    def array(self, args):
        if isinstance(args[0], Hole):
            return args[0]
        else:
            return Var(args[0])
    def name_hole(self, args):
        if len(args) == 1:
            return NameHole(args[0], '_')
        elif len(args) == 2:
            return NameHole(args[0], args[1])
        assert(False)
    def const(self, args):
        return Const(args[0])
    def scalar(self, args):
        if isinstance(args[0], Hole):
            return args[0]
        else:
            return Var(args[0])
    def index(self, args):
        return args[0]
    def literal(self, args):
        return args[0]
    def float_literal(self, args):
        return Literal(float, float(args[0]))
    def int_literal(self, args):
        return Literal(int, int(args[0]))
    def hex_literal(self, args):
        return Hex(args[0])
    def scalar_access(self, args):
        return Access(args[0])
    def array_access(self, args):
        return Access(args[0], args[1:])
    def access(self, args):
        return args[0]
    def expr(self, args):
        # return Expr(args[0])
        return Expr(args)
    def action(self, args):
        if len(args) == 1:
            return Action(None, args[0])
        if len(args) == 2:
            return Action(*args)
        assert(False)
    def op(self, args):
        if isinstance(args[0], Hole):
            return args[0]
        else:
            return Op(args[0])
    def atom(self, args):
        return args[0]
    def paren(self, args):
        return Paren(args[0])
    def assignment(self, args):
        return Assignment(args[0], args[1])
    def statement(self, args):
        stmt = args[0]
        return stmt
    def seq(self, args):
        return args
    def statement_hole(self, args):
        if len(args) == 1:
            return StatementHole(args[0], '_')
        elif len(args) == 2:
            return StatementHole(args[0], args[1])
        assert(False)
    def expr_hole(self, args):
        if len(args) == 1:
            return ExpressionHole(args[0], '_')
        elif len(args) == 2:
            return ExpressionHole(args[0], args[1])
        assert(False)
    def op_hole(self, args):
        if len(args) == 1:
            return OpHole(args[0], '_')
        elif len(args) == 2:
            return OpHole(args[0], args[1])
        assert(False)

    # def loop_vars(self, args):
    #     return args

    def loop_shapes(self, args):
        return args
    def loop_shape(self, args):
        return args[0]
    def single_loop_shape(self, args):
        loop_var = args[0].var
        default_greater_eq = Access(f'{loop_var}_greater_eq')
        default_less_eq = Access(f'{loop_var}_less_eq')
        default_step = Literal(int, 1)
        return LoopShape(args[0],
                         default_greater_eq,
                         default_less_eq,
                         default_step)
    def multi_loop_shape(self, args):
        return args[0]
    def loop_shape_parts(self, args):
        merged = None
        for loop_shape_builder in args:
            if merged is None:
                merged = loop_shape_builder
            else:
                merged.merge(loop_shape_builder)
        assert(merged is not None)
        assert(merged.loop_var is not None)
        loop_var = merged.loop_var.pprint()
        default_greater_eq = Access(f'{loop_var}_greater_eq')
        default_less_eq = Access(f'{loop_var}_less_eq')
        default_step = Literal(int, 1)
        return merged.build(default_greater_eq,
                            default_less_eq,
                            default_step)
    def loop_shape_part(self, args):
        loop_shape_builder = LoopShapeBuilder()
        if len(args) == 1:
            loop_shape_builder.set_shape_part(args[0])
        elif len(args) == 2:
            loop_shape_builder.set_shape_part(args[1], args[0])
        else:
            raise RuntimeError(f'Unsupported loop shape ({args})')
        return loop_shape_builder

    def abstract_loop(self, args):
        loop_shapes = args[0]
        body = args[1]
        loop = AbstractLoop(loop_shapes, body)
        return loop

    def start(self, args):
        decls = []
        body = []
        # consts = []
        for arg in args:
            if type(arg) == Declaration:
                decls.append(arg)
            elif type(arg) in [AbstractLoop, Assignment]:
                body.append(arg)
            # elif type(arg) == Const:
            #     consts.append(arg)
            else:
                raise RuntimeError('Unsupported syntax in main program')
        # Add implicit constants that are created when the bounds and steps
        # of loop vars are not explicitly stated
        # non_consts = set()
        # for decl in decls:
        #     non_consts.add(decl.name)
        # for stmt in body:
        #     for loop in get_loops(stmt):
        #         for loop_shape in loop.loop_shapes:
        #             non_consts.add(loop_var.var)
        # consts_set = set()
        # for stmt in body:
        #     for access in get_accesses(stmt):
        #         if not access.var.is_hole():
        #             if access.var.name not in non_consts:
        #                 consts_set.add(access.var.name)
        # consts = [Const(name)
        #           for name in sorted(list(consts_set))]
        # return Program(decls, body, consts)
        return Program(decls, body, [])

def parse_str(code, start="start"):
    parser = Lark(grammar)
    lark_ast = parser.parse(code, start=start)
    tree_simplifier = TreeSimplifier()
    abstract_ast = tree_simplifier.transform(lark_ast)
    return abstract_ast

def parse_stmt_str(code):
    return parse_str(code, "statement")

def parse_seq_str(code):
    return parse_str(code, "seq")

def parse_expr_str(code):
    return parse_str(code, "expr")

def parse_file(path):
    with open(path) as f:
        return parse_str(f.read())

def get_accesses(node):
    accesses = set()
    if isinstance(node, Assignment):
        accesses.update(get_accesses(node.lhs))
        accesses.update(get_accesses(node.rhs))
        return accesses
    elif isinstance(node, Access):
        accesses.add(node)
        for index in node.indices:
            accesses.update(get_accesses(index))
        return accesses
    elif isinstance(node, AbstractLoop):
        for loop_var in node.loop_vars:
            accesses.update(get_accesses(loop_var))
        for stmt in node.body:
            accesses.update(get_accesses(stmt))
        return accesses
    elif isinstance(node, Program):
        for stmt in node.body:
            accesses.update(get_accesses(stmt))
        return accesses
    elif isinstance(node, Expr):
        for action in node.actions:
            accesses.update(get_accesses(action))
        return accesses
    elif isinstance(node, Action):
        accesses.update(get_accesses(node.access))
        return accesses
    elif isinstance(node, Paren):
        accesses.update(get_accesses(node.expr))
        return accesses
    elif isinstance(node, StatementHole):
        return accesses
    elif isinstance(node, ExpressionHole):
        return accesses
    elif isinstance(node, Literal):
        return accesses
    else:
        raise RuntimeError('Unhandled type of node ' + str(type(node)))

def get_loops(node):
    if isinstance(node, AbstractLoop):
        loops = {node}
        for stmt in node.body:
            loops.update(get_loops(stmt))
        return loops
    elif isinstance(node, Program):
        loops = {}
        for stmt in node.body:
            loops.update(get_loops(stmt))
        return loops
    elif isinstance(node, Assignment):
        return {}
    elif isinstance(node, StatementHole):
        return {}
    else:
        raise RuntimeError('get_loops: Unhandled type of node ' + str(type(node)))
