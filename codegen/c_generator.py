from pathlib import Path
from shutil import copy2
from string import Template
from pattern_ast import (Declaration, Literal, Hex, Assignment,
                         Access, LoopShape, AbstractLoop, Op, Program, NoOp)
from constant_assignment import VariableMap

def loop_header(loop_var, loop_var_ty, begin, ends):
    decl = f'{loop_var_ty} {loop_var}' if loop_var_ty else loop_var
    end_clauses = ' && '.join([f'{loop_var} <= {end}' for end in ends])
    return (f'for ({decl} = {begin}; '
            f'{end_clauses}; '
            f'++{loop_var}) {{')

def spaces(indent):
    return '  ' * indent

def is_local(decl):
    return decl.is_local

def is_nonlocal(decl):
    return not is_local(decl)

def is_array(decl):
    return decl.n_dimensions > 0

def is_nonlocal_array(decl):
    return is_nonlocal(decl) and is_array(decl)

def is_nonlocal_scalar(decl):
    return is_nonlocal(decl) and not is_array(decl)

def ptr(decl):
    cloned = decl.clone()
    sizes = ''.join([f'[{size.pprint()}]' for size in decl.sizes])
    cloned.name = f'{decl.name}_ptr'
    cloned.ty = f'{decl.ty}(*){sizes}'
    return cloned

def access(name, loop_vars):
    return f'{name}' + ''.join(f'[{v}]' for v in loop_vars)

class CGenerator:
    def __init__(self, instance, init_value_map):
        self.pattern = instance.pattern
        self.sorted_var_names = sorted([decl.name for decl in self.pattern.decls])
        self.decls = {decl.name:decl for decl in self.pattern.decls}

        self.init_value_map = init_value_map
        self.access_bounds = instance.array_access_bounds
        self.indent = 0

    # TODO: make this a closure
    def iterate_decls(self, filter_function=None):
        if filter_function is None:
            filter_function = lambda _: True
        for var_name in self.sorted_var_names:
            decl = self.decls[var_name]
            if filter_function(decl):
                yield decl

    def indent_in(self):
        self.indent += 1
        return spaces(self.indent)

    def indent_out(self):
        assert(self.indent > 0)
        self.indent -= 1
        return spaces(self.indent)

    def no_indent(self):
        return spaces(self.indent)

    def decl(self, decl, is_ptr=False, is_restrict=False):
        brackets = ''.join([f'[{size.pprint()}]' for size in decl.sizes])
        name = decl.name
        if is_ptr:
            if is_restrict:
                declaration = f'{decl.ty} (*restrict {name}){brackets}'
            else:
                declaration = f'{decl.ty} (*{name}){brackets}'
        else:
            declaration = f'{decl.ty} {name}{brackets}'
            if is_restrict:
                declaration = declaration.replace('[', '[restrict ', 1)
        return declaration

    def define_scalars(self):
        lines = []
        for decl in self.iterate_decls(is_nonlocal_scalar):
            lines.append(f'{self.decl(decl)};')
        return '\n'.join(lines)

    def define_arrays(self):
        lines = []
        for decl in self.iterate_decls(is_nonlocal_array):
            lines.append(f'{self.decl(decl)};')
        return '\n'.join(lines)

    def define_arrays_as_pointers(self):
        lines = []
        for decl in self.iterate_decls(is_nonlocal_array):
            decl_ptr = ptr(decl)
            scalar = Declaration(decl_ptr.name, 0, ty=decl.ty)
            lines.append(f'{self.decl(scalar, is_ptr=True)};')
        return '\n'.join(lines)

    def allocate_array(self, decl):
        n_elements = ' * '.join([f'({size.pprint()})' for size in decl.sizes])
        return f'{ptr(decl).name} = malloc(sizeof({decl.ty}) * {n_elements});'

    def allocate_arrays_code(self):
        ws = self.indent_in()
        code = '\n'.join([
            f'{ws}{self.allocate_array(decl)}'
            for decl in self.iterate_decls(is_nonlocal_array)
        ])
        self.indent_out()
        return code

    def array_only_params(self):
        return ', '.join([
            self.decl(decl, is_restrict=True)
            for decl in self.iterate_decls(is_nonlocal_array)
        ])

    def nested_loops_full(self, loop_vars, min_indices, max_indices, generate_body):
        lines = []

        n_dimensions = len(loop_vars)
        assert(n_dimensions == len(min_indices))
        assert(n_dimensions == len(max_indices))

        # open loop header
        ws = self.no_indent()
        for loop_var, begin, ends in zip(loop_vars, min_indices, max_indices):
            loop_var_ty = 'int'
            for decl in self.iterate_decls():
                if loop_var == decl.name:
                    loop_var_ty = ''
                    break
            lines.append(f'{ws}{loop_header(loop_var, loop_var_ty, begin, ends)}')
            ws = self.indent_in()

        # body
        lines.append(generate_body(loop_vars))

        # close loop header
        for _ in range(n_dimensions):
            lines.append(f'{self.indent_out()}}}')

        return '\n'.join(lines)
        
    def nested_loops(self, min_indices, max_indices, generate_body):
        loop_vars = [f'i{depth}' for depth in range(len(min_indices))]
        return self.nested_loops_full(loop_vars,
                                      min_indices,
                                      max_indices,
                                      generate_body)

    def canonicalize_name(self, decl):
        ws = self.no_indent()
        if is_array(decl):
            return [f'{ws}{self.decl(decl)} = *{ptr(decl).name};']
        else:
            return []

    def determine_max_indices(self, decl):
        max_indices = []
        for declared_size, analyzed_bound in zip(decl.sizes, self.access_bounds[decl.name].max_indices):
            if type(declared_size) == Literal:
                max_index = analyzed_bound
            else:
                max_index = Op('-', [declared_size.clone(), Literal(int, 1)]).pprint()
            max_indices.append(max_index)
        return max_indices

    def initialize_value(self, decl, is_ptr=False):
        lines = []
        def generate_body(loop_vars):
            if decl.ty == 'float':
                val = 'frand(0.0, 1.0)'
            elif decl.ty == 'double':
                val = 'drand(0.0, 1.0)'
            elif decl.ty == 'int':
                val = 'irand(0, 10)'
            else:
                raise RuntimeError(f'Unsupported type {decl.ty}')

            # Override default if it is in init_value_map
            if decl.name in self.init_value_map:
                val = self.init_value_map[decl.name]

            if is_ptr:
                name = f'(*{decl.name})'
            else:
                name = decl.name
            return f'{self.no_indent()}{access(name, loop_vars)} = {val};'
        begins = self.access_bounds[decl.name].min_indices
        ends = [[max_index] for max_index in self.determine_max_indices(decl)]
        lines.append(self.nested_loops(begins, ends, generate_body))
        return '\n'.join(lines)

    def initialize_arrays_code(self, is_ptr=False):
        lines = []
        self.indent_in()
        for decl in self.iterate_decls(is_nonlocal_array):
            lines.append(self.initialize_value(decl, is_ptr))
        self.indent_out()
        return '\n'.join(lines)

    def initialize_scalars_code(self):
        lines = []
        self.indent_in()
        for decl in self.iterate_decls(is_nonlocal_scalar):
            lines.append(self.initialize_value(decl))
        self.indent_out()
        return '\n'.join(lines)

    def accumulate_checksum(self, decl, is_ptr=False):
        lines = []
        def generate_body(loop_vars):
            if is_array(decl):
                if is_ptr:
                    name = f'(*{decl.name})'
                else:
                    name = decl.name
            else:
                name = decl.name
            return f'{self.no_indent()}total += {access(name, loop_vars)};'
        max_indices = [[max_index] for max_index in self.determine_max_indices(decl)]
        lines.append(self.nested_loops(self.access_bounds[decl.name].min_indices,
                                       max_indices,
                                       generate_body))
        return '\n'.join(lines)

    def calculate_checksum_code(self, is_ptr=False):
        lines = []
        ws = self.indent_in()
        lines.append(f'{ws}float total = 0.0;')

        for decl in self.iterate_decls(is_nonlocal):
            lines.append(self.accumulate_checksum(decl, is_ptr))

        lines.append(f'{ws}return total;')
        self.indent_out()
        return '\n'.join(lines)

    def scalar_externs(self):
        return '\n'.join([
            f'extern {self.decl(decl)};'
            for decl in self.iterate_decls(is_nonlocal_scalar)
        ])

    def array_externs(self):
        return '\n'.join([
            f'extern {self.decl(decl)};'
            for decl in self.iterate_decls(is_nonlocal_array)
        ])

    def define_locals(self):
        lines = []
        ws = self.no_indent()
        for decl in self.iterate_decls(is_local):
            lines.append(f'{self.decl(decl)};')
            if decl.name in self.init_value_map:
                lines.append(self.initialize_value(decl))
        return '\n'.join(lines)

    def array_params(self, is_ptr=False):
        return ', '.join([
            self.decl(decl, is_ptr=is_ptr, is_restrict=True)
            for decl in self.iterate_decls(is_nonlocal_array)
        ])

    def cast_array_ptr(self, decl):
        ptr_decl = ptr(decl)
        return f'({ptr_decl.ty})({ptr_decl.name})'

    def array_args(self, is_ptr=False):
        if is_ptr:
            return ', '.join([
                f'{self.cast_array_ptr(decl)}'
                for decl in self.iterate_decls(is_nonlocal_array)
            ])
        else:
            return ', '.join([
                f'*{self.cast_array_ptr(decl)}'
                for decl in self.iterate_decls(is_nonlocal_array)
            ])

    def ast(self, node):
        ty = type(node)
        if ty == Program:
            self.indent_in()
            lines = []
            for stmt in node.body:
                lines.append(self.ast(stmt))
            self.indent_out()
            return '\n'.join(lines)
        elif ty == AbstractLoop:
            # get loop vars, min_indices, max_indices
            loop_vars = []
            min_indices = []
            max_indices = []
            for shape in node.loop_shapes:
                loop_vars.append(self.ast(shape.loop_var))
                min_indices.append(self.ast(shape.greater_eq))
                max_indices.append([self.ast(expr) for expr in shape.less_eq])
                assert(type(shape.step) == Literal and
                       shape.step.ty == int and
                       shape.step.val == 1)
            def generate_body(loop_vars):
                return '\n'.join([
                    self.ast(stmt) for stmt in node.body
                ])
            return self.nested_loops_full(loop_vars,
                                          min_indices,
                                          max_indices,
                                          generate_body)
        elif ty == Assignment:
            return f'{self.no_indent()}{node.pprint()}'
        elif ty == Op or ty == Access or ty == Hex or ty == Literal:
            return node.pprint()
        elif ty == NoOp:
            return f'{self.no_indent()}{node.pprint()}'
        else:
            assert(False)

    def core_code(self):
        return self.ast(self.pattern)

def generate_code(output_dir, instance, init_value_map=None, template_dir=None):
    if template_dir is None:
        template_dir = 'codegen'
    if init_value_map is None:
        init_value_map = {}

    # setup directories
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # main
    src_main_c_path = f'{template_dir}/main.template.c'
    dst_main_c_path = f'{output_dir}/main.c'
    copy2(src_main_c_path, dst_main_c_path)

    # make file
    src_make_path = f'{template_dir}/Makefile'
    dst_make_path = f'{output_dir}/Makefile'
    copy2(src_make_path, dst_make_path)

    # prepare template dictionary
    cgen = CGenerator(instance, init_value_map)
    template_dict = {
        'define_scalars': cgen.define_scalars(),
        'define_arrays': cgen.define_arrays(),
        'define_arrays_as_pointers': cgen.define_arrays_as_pointers(),
        'locals': cgen.define_locals(),
        'init_scalars_code': cgen.initialize_scalars_code(),
        'init_arrays_code': cgen.initialize_arrays_code(is_ptr=False),
        'init_arrays_code_as_ptr': cgen.initialize_arrays_code(is_ptr=True),
        'allocate_arrays_code': cgen.allocate_arrays_code(),
        'calculate_checksum_code': cgen.calculate_checksum_code(is_ptr=False),
        'calculate_checksum_code_as_ptr': cgen.calculate_checksum_code(is_ptr=True),
        'core_code': cgen.core_code(),

        'scalar_externs': cgen.scalar_externs(),
        'array_externs': cgen.array_externs(),
        'array_params': cgen.array_params(is_ptr=False),
        'array_args': cgen.array_args(is_ptr=False),
        'array_params_as_ptr': cgen.array_params(is_ptr=True),
        'array_args_as_ptr': cgen.array_args(is_ptr=True),
    }

    # wrapper
    # fill template
    wrapper_template_path = Path(f'{template_dir}/wrapper.template.c')
    wrapper_template_str = wrapper_template_path.read_text()
    wrapper_template = Template(wrapper_template_str)
    wrapper_str = wrapper_template.substitute(template_dict)

    # write
    wrapper_dst_path = Path(f'{output_dir}/wrapper.c')
    wrapper_dst_path.write_text(wrapper_str)

    # core
    # fill template
    core_template_path = Path(f'{template_dir}/core.template.c')
    core_template_str = core_template_path.read_text()
    core_template = Template(core_template_str)
    core_str = core_template.substitute(template_dict)

    # write
    core_dst_path = Path(f'{output_dir}/core.c')
    core_dst_path.write_text(core_str)
