from lark import Lark, Transformer

# Note:
# Operator precedence is based on
# https://docs.microsoft.com/en-us/cpp/c-language/precedence-and-order-of-evaluation?view=vs-2019

# TODO: Add blocks so statements aren't arrays of statements any more
#       but actual block data structures
#       This will be convenient when generating, for example, programs
#       with 1 to 5 statements. We can then have one statement hole to
#       be filled with blocks of different sizes

grammar = '''
    start: (declaration)+ statement+

    declaration: param | local
    param: "declare" array (dimension)* ";"
    local: "local" array (dimension)* ";"
    dimension: "[" expr? "]"
    abstract_loop: "for" "[" loop_shapes "]" "{" statement+ "}"

    loop_shapes: loop_shape ("," loop_shape)*
    loop_shape: single_loop_shape | multi_loop_shape
    single_loop_shape: expr
    multi_loop_shape: "(" loop_shape_parts ")"
    loop_shape_parts: loop_shape_part ("," loop_shape_part)*
    loop_shape_part: LOOP_SHAPE_PREFIX? expr
    LOOP_SHAPE_PREFIX: "<=" | ">=" | "+="

    statement: assignment | abstract_loop | no_op | statement_hole
    assignment: expr "=" expr ";"
    no_op: ";"
    statement_hole: "$" CNAME (":" CNAME)? "$"

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
    multiplicative: multiplicative op_hole unary | multiplicative MULTIPLICATIVE unary | unary
    unary: UNARY unary | atom
    atom: access | "(" expr ")" | expr_hole
    expr_hole: "#" CNAME (":" CNAME)? "#"

    access: scalar_access | array_access | literal
    scalar_access: scalar
    array_access: array ("[" expr "]")+
    literal: float_literal | int_literal | hex_literal
    float_literal: FLOAT
    int_literal: INT
    hex_literal: HEX_NUMBER

    scalar: CNAME | name_hole
    array: CNAME
    name_hole: "`" CNAME (":" CNAME)? "`"

    EQUAL: "==" | "!="
    RELATION: "<=" | ">=" | "<" | ">"
    BITWISE_SHIFT: "<<" | ">>"
    ADDITIVE: "+" | "-"
    MULTIPLICATIVE: "*" | "/" | "%"
    UNARY: "+" | "-" | "!" | "~"

    op_hole: "@" CNAME (":" CNAME)? "@"

    HEX_NUMBER: /0x[\\da-f]*/i

    COMMENT: /##[^\\n]*/
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


from pattern_ast import Assignment, Access, AbstractLoop, Program, get_accesses, Declaration, Const, Literal, Op, LoopShape, get_loops, get_accesses, LoopShapeBuilder, Hex, NoOp, StatementHole, ExpressionHole, NameHole, OpHole

class TreeSimplifier(Transformer):
    def dimension(self, args):
        if len(args) > 0:
            return args[0]
        else:
            return None
    def declaration(self, args):
        return args[0]

    def param(self, args):
        sizes = args[1:]
        n_dimensions = len(args) - 1
        return Declaration(args[0], n_dimensions, sizes, is_local=False)
    def local(self, args):
        sizes = args[1:]
        n_dimensions = len(args) - 1
        return Declaration(args[0], n_dimensions, sizes, is_local=True)
    def array(self, args):
        return ''.join(args)
    def const(self, args):
        return Const(args[0])
    def scalar(self, args):
        return ''.join(args)
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
        return args[0]
    def conditional(self, args):
        if len(args) == 1:
            return args[0]
        return Op('?:', args)
    def logical_or(self, args):
        if len(args) == 1:
            return args[0]
        return Op('||', args)
    def logical_and(self, args):
        if len(args) == 1:
            return args[0]
        return Op('&&', args)
    def equality(self, args):
        if len(args) == 1:
            return args[0]
        return Op(args[1], [args[0], args[2]])
    def relational(self, args):
        if len(args) == 1:
            return args[0]
        return Op(args[1], [args[0], args[2]])
    def additive(self, args):
        if len(args) == 1:
            return args[0]
        return Op(args[1], [args[0], args[2]])
    def multiplicative(self, args):
        if len(args) == 1:
            return args[0]
        return Op(args[1], [args[0], args[2]])
    def bitwise_shift(self, args):
        if len(args) == 1:
            return args[0]
        return Op(args[1], [args[0], args[2]])
    def bitwise_or(self, args):
        if len(args) == 1:
            return args[0]
        return Op('|', args)
    def bitwise_xor(self, args):
        if len(args) == 1:
            return args[0]
        return Op('^', args)
    def bitwise_and(self, args):
        if len(args) == 1:
            return args[0]
        return Op('&', args)
    def unary(self, args):
        if len(args) == 1:
            return args[0]
        return Op(args[0], [args[1]])
    def atom(self, args):
        return args[0]

    def assignment(self, args):
        return Assignment(args[0], args[1])
    def no_op(self, args):
        return NoOp()
    def statement(self, args):
        stmt = args[0]
        return stmt
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
                         [default_less_eq],
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
        loop_var = merged.loop_var.var
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
        body = args[1:]
        loop = AbstractLoop(loop_shapes, body)
        return loop
    def start(self, args):
        decls = []
        body = []
        # consts = []
        for arg in args:
            if type(arg) == Declaration:
                decls.append(arg)
            elif type(arg) in [AbstractLoop, Assignment, NoOp]:
                body.append(arg)
            else:
                raise RuntimeError('Unsupported syntax in main program')
        # Add implicit constants that are created when the bounds and steps
        # of loop vars are not explicitly stated
        non_consts = set()
        for decl in decls:
            non_consts.add(decl.name)
        for stmt in body:
            for loop in get_loops(stmt):
                for shape in loop.loop_shapes:
                    non_consts.add(shape.loop_var.var)
        consts_set = set()
        for stmt in body:
            for access in get_accesses(stmt):
                if access.var not in non_consts:
                    consts_set.add(access.var)
        consts = [Const(name)
                  for name in sorted(list(consts_set))]
        return Program(decls, body, consts)

    # holes
    def expr_hole(self, args):
        if len(args) == 1:
            return ExpressionHole(args[0], '_')
        elif len(args) == 2:
            return ExpressionHole(args[0], args[1])
    def op_hole(self, args):
        if len(args) == 1:
            return OpHole(args[0], '_')
        elif len(args) == 2:
            return OpHole(args[0], args[1])
        assert(False)
    def name_hole(self, args):
        if len(args) == 1:
            return NameHole(args[0], '_')
        elif len(args) == 2:
            return NameHole(args[0], args[1])
        assert(False)
    def statement_hole(self, args):
        if len(args) == 1:
            return StatementHole(args[0], '_')
        elif len(args) == 2:
            return StatementHole(args[0], args[1])
        assert(False)

def parse_str(code, start_rule="start"):
    parser = Lark(grammar, start=start_rule)
    lark_ast = parser.parse(code)
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

def generate_patterns_from_skeleton(
        generate,
        skeleton,
        n_wanted=1,
        existing_hashes=None,
        max_tries=10000):
    from hashlib import md5
    patterns = []

    hashes = set() if existing_hashes is None else existing_hashes

    n_generated = 0
    for _ in range(max_tries):
        body = generate(skeleton.clone())
        pattern = parse_str(body.pprint())
        code = pattern.pprint()

        code_hash = md5(code.encode('utf-8')).hexdigest()
        if code_hash in hashes:
            print('duplicate')
            continue

        patterns.append(pattern)
        hashes.add(code_hash)
        n_generated += 1
        print(f'Progress: {n_generated} / {n_wanted}')
        if n_generated == n_wanted:
            break

    return patterns
