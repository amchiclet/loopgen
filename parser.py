from lark import Lark, Transformer

# Note:
# Operator precedence is based on
# https://docs.microsoft.com/en-us/cpp/c-language/precedence-and-order-of-evaluation?view=vs-2019

grammar = '''
    start: (declaration)+ statement+

    declaration: param | local
    param: "declare" array (dimension)* ";"
    local: "local" array (dimension)* ";"
    dimension: "[" INT? "]"
    abstract_loop: "for" "[" loop_shapes "]" "{" statement+ "}"

    loop_shapes: loop_shape ("," loop_shape)*
    loop_shape: single_loop_shape | multi_loop_shape
    single_loop_shape: expr
    multi_loop_shape: "(" loop_shape_parts ")"
    loop_shape_parts: loop_shape_part ("," loop_shape_part)*
    loop_shape_part: LOOP_SHAPE_PREFIX? expr
    LOOP_SHAPE_PREFIX: "<=" | ">=" | "+="

    statement: assignment | abstract_loop
    assignment: access "=" expr ";"

    expr: conditional
    conditional: logical_or "?" logical_or ":" conditional | logical_or
    logical_or: logical_or "||" logical_and | logical_and
    logical_and: logical_and "&&" bitwise_or | bitwise_or
    bitwise_or: bitwise_or "|" bitwise_xor | bitwise_xor
    bitwise_xor: bitwise_xor "^" bitwise_and | bitwise_and
    bitwise_and: bitwise_and "&" equality | equality
    equality: equality EQUAL relational | relational
    relational: relational RELATION bitwise_shift | bitwise_shift
    bitwise_shift: bitwise_shift BITWISE_SHIFT additive | additive
    additive: additive ADDITIVE multiplicative | multiplicative
    multiplicative: multiplicative MULTIPLICATIVE unary | unary
    unary: UNARY unary | atom
    atom: access | "(" expr ")"

    access: scalar_access | array_access | literal
    scalar_access: scalar
    array_access: array ("[" expr "]")+
    literal: float_literal | int_literal | hex_literal
    float_literal: FLOAT
    int_literal: INT
    hex_literal: HEX_NUMBER

    scalar: CNAME
    array: CNAME

    EQUAL: "==" | "!="
    RELATION: "<=" | ">=" | "<" | ">"
    BITWISE_SHIFT: "<<" | ">>"
    ADDITIVE: "+" | "-"
    MULTIPLICATIVE: "*" | "/" | "%"
    UNARY: "+" | "-" | "!" | "~"

    HEX_NUMBER: /0x[\\da-f]*/i

    COMMENT: /#[^\\n]*/
    %import common.WS
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


from abstract_ast import Assignment, Access, AbstractLoop, Program, get_accesses, Declaration, Const, Literal, Op, LoopShape, get_loops, get_accesses, LoopShapeBuilder, Hex

class TreeSimplifier(Transformer):
    def __init__(self, start_node_id=0):
        self.current_node_id = start_node_id
    def next_node_id(self):
        self.current_node_id += 1
        return self.current_node_id
    def dimension(self, args):
        if len(args) > 0:
            return int(args[0])
        else:
            return None
    def declaration(self, args):
        return args[0]
        # n_dimensions = len(args) - 1
        # return Declaration(args[0], n_dimensions, self.next_node_id())    
    def param(self, args):
        sizes = args[1:]
        n_dimensions = len(args) - 1
        return Declaration(args[0], n_dimensions, sizes, is_local=False, node_id=self.next_node_id())
    def local(self, args):
        sizes = args[1:]
        n_dimensions = len(args) - 1
        return Declaration(args[0], n_dimensions, sizes, is_local=True, node_id=self.next_node_id())
    def array(self, args):
        return ''.join(args)
    def const(self, args):
        return Const(args[0], self.next_node_id())
    def scalar(self, args):
        return ''.join(args)
    def index(self, args):
        return args[0]
    def literal(self, args):
        return args[0]
    def float_literal(self, args):
        return Literal(float, float(args[0]), self.next_node_id())
    def int_literal(self, args):
        return Literal(int, int(args[0]), self.next_node_id())
    def hex_literal(self, args):
        return Hex(args[0], self.next_node_id())
    def scalar_access(self, args):
        return Access(args[0], node_id=self.next_node_id())
    def array_access(self, args):
        return Access(args[0], args[1:], self.next_node_id())
    def access(self, args):
        return args[0]

    def expr(self, args):
        return args[0]
    def conditional(self, args):
        if len(args) == 1:
            return args[0]
        return Op('?:', args, self.next_node_id())
    def logical_or(self, args):
        if len(args) == 1:
            return args[0]
        return Op('||', args, self.next_node_id())
    def logical_and(self, args):
        if len(args) == 1:
            return args[0]
        return Op('&&', args, self.next_node_id())
    def equality(self, args):
        if len(args) == 1:
            return args[0]
        return Op(args[1], [args[0], args[2]], self.next_node_id())
    def relational(self, args):
        if len(args) == 1:
            return args[0]
        return Op(args[1], [args[0], args[2]], self.next_node_id())
    def additive(self, args):
        if len(args) == 1:
            return args[0]
        return Op(args[1], [args[0], args[2]], self.next_node_id())
    def multiplicative(self, args):
        if len(args) == 1:
            return args[0]
        return Op(args[1], [args[0], args[2]], self.next_node_id())
    def bitwise_shift(self, args):
        if len(args) == 1:
            return args[0]
        return Op(args[1], [args[0], args[2]], self.next_node_id())
    def bitwise_or(self, args):
        if len(args) == 1:
            return args[0]
        return Op('|', args, self.next_node_id())
    def bitwise_xor(self, args):
        if len(args) == 1:
            return args[0]
        return Op('^', args, self.next_node_id())
    def bitwise_and(self, args):
        if len(args) == 1:
            return args[0]
        return Op('&', args, self.next_node_id())
    def unary(self, args):
        if len(args) == 1:
            return args[0]
        return Op(args[0], [args[1]], self.next_node_id())
    def atom(self, args):
        return args[0]

    def assignment(self, args):
        return Assignment(args[0], args[1], self.next_node_id())
    def statement(self, args):
        stmt = args[0]
        return stmt
    def loop_shapes(self, args):
        return args
    def loop_shape(self, args):
        return args[0]
    def single_loop_shape(self, args):
        loop_var = args[0].var
        default_greater_eq = Access(f'{loop_var}_greater_eq', node_id=self.next_node_id())
        default_less_eq = Access(f'{loop_var}_less_eq', node_id=self.next_node_id())
        default_step = Literal(int, 1, self.next_node_id())
        return LoopShape(args[0],
                         default_greater_eq,
                         default_less_eq,
                         default_step,
                         self.next_node_id())
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
        # print(merged)
        loop_var = merged.loop_var.var
        default_greater_eq = Access(f'{loop_var}_greater_eq', node_id=self.next_node_id())
        default_less_eq = Access(f'{loop_var}_less_eq', node_id=self.next_node_id())
        default_step = Literal(int, 1, self.next_node_id())
        return merged.build(default_greater_eq,
                            default_less_eq,
                            default_step,
                            self.next_node_id())
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
        body = args[1:]
        loop = AbstractLoop(loop_shapes, body, self.next_node_id())
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
        non_consts = set()
        for decl in decls:
            non_consts.add(decl.name)
        for stmt in body:
            for _, loop in get_loops(stmt).items():
                for shape in loop.loop_shapes:
                    non_consts.add(shape.loop_var.var)
        consts_set = set()
        for stmt in body:
            for access in get_accesses(stmt):
                if access.var not in non_consts:
                    consts_set.add(access.var)
        consts = [Const(name, self.next_node_id())
                  for name in sorted(list(consts_set))]
        return Program(decls, body, consts, self.next_node_id())

def parse_str(code, node_id=0):
    parser = Lark(grammar)
    lark_ast = parser.parse(code)
    tree_simplifier = TreeSimplifier(node_id)
    abstract_ast = tree_simplifier.transform(lark_ast)
    return abstract_ast, tree_simplifier.next_node_id()

def parse_file(path, node_id=0):
    with open(path) as f:
        return parse_str(f.read(), node_id)
