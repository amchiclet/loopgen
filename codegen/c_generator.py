from pathlib import Path
from shutil import copy2
from string import Template
from pattern_ast import (Declaration, Literal, Hex, Assignment,
                         Access, LoopShape, AbstractLoop, Op, Program)

def loop_header(loop_var, begin, end):
    return (f'for (int {loop_var} = {begin}; '
            f'{loop_var} <= {end}; '
            f'++{loop_var}) {{')

def spaces(indent):
    return '  ' * indent

default_type = 'float'

def is_nonlocal(decl):
    return not decl.is_local

def is_array(decl):
    return decl.n_dimensions > 0

def is_nonlocal_array(decl):
    return is_nonlocal(decl) and is_array(decl)

def is_nonlocal_scalar(decl):
    return is_nonlocal(decl) and not is_array(decl)

def ptr(decl):
    if is_array(decl):
        cloned = decl.clone()
        cloned.name = f'{decl.name}_ptr'
        return cloned
    assert(False)

def access(name, loop_vars):
    return f'{name}' + ''.join(f'[{v}]' for v in loop_vars)

class CGenerator:
    def __init__(self, instance):
        self.pattern = instance.pattern
        self.sorted_var_names = sorted([decl.name for decl in self.pattern.decls])
        self.decls = {decl.name:decl for decl in self.pattern.decls}

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
        self.indent -= 1
        return spaces(self.indent)

    def no_indent(self):
        return spaces(self.indent)

    def decl(self, ty, decl, is_ptr=False, is_restrict=False):
        assert(not(is_ptr and is_restrict))
        brackets = ''.join([f'[{size}]' for size in decl.sizes])
        name = decl.name
        if is_ptr:
            name = f'(*{name})'
        declaration = f'{ty} {name}{brackets}'
        if is_restrict:
            declaration = declaration.replace('[', '[restrict ', 1)
        return declaration

    def data_defs(self):
        lines = []
        for decl in self.iterate_decls(is_nonlocal):
            if is_array(decl):
                lines.append(f'{self.decl(default_type, ptr(decl), is_ptr=True)};')
            else:
                lines.append(f'{self.decl(default_type, decl)};')
        return '\n'.join(lines)

    def allocate_var(self, decl):
        n_elements = ' * '.join([str(size) for size in decl.sizes])
        return f'{decl.name} = malloc(sizeof({default_type}) * {n_elements});'

    def allocate_heap_vars_code(self):
        ws = self.indent_in()
        code = '\n'.join([
            f'{ws}{self.allocate_var(ptr(decl))}'
            for decl in self.iterate_decls(is_nonlocal_array)
        ])
        self.indent_out()
        return code

    def array_only_params(self):
        return ', '.join([
            self.decl(default_type, decl, is_restrict=True)
            for decl in self.iterate_decls(is_nonlocal_array)
        ])

    def nested_loops_full(self, loop_vars, min_indices, max_indices, generate_body):
        lines = []

        n_dimensions = len(loop_vars)
        assert(n_dimensions == len(min_indices))
        assert(n_dimensions == len(max_indices))

        # open loop header
        for loop_var, begin, end in zip(loop_vars, min_indices, max_indices):
            lines.append(f'{self.indent_in()}{loop_header(loop_var, begin, end)}')

        # body
        self.indent_in()
        lines.append(generate_body(loop_vars))

        # close loop header
        for _ in range(n_dimensions):
            lines.append(f'{self.indent_out()}}}')
        self.indent_out()
        return '\n'.join(lines)
        
    def nested_loops(self, bound, generate_body):
        loop_vars = [f'i{depth}' for depth in range(len(bound.min_indices))]
        return self.nested_loops_full(loop_vars,
                                      bound.min_indices,
                                      bound.max_indices,
                                      generate_body)

    def canonicalize_name(self, decl):
        ws = self.no_indent()
        if is_array(decl):
            return [f'{ws}{self.decl(default_type, decl)} = *{ptr(decl).name};']
        else:
            return []

    def initialize_value(self, decl):
        lines = []
        def generate_body(loop_vars):
            name = decl.name if not is_array(decl) else f'(*{ptr(decl).name})'
            return f'{self.no_indent()}{access(name, loop_vars)} = frand(0.1, 1.0);'
        lines.append(self.nested_loops(self.access_bounds[decl.name],
                                       generate_body))
        return '\n'.join(lines)

    def initialize_values_code(self):
        lines = []
        for decl in self.iterate_decls():
            lines.append(self.initialize_value(decl))
        return '\n'.join(lines)

    def accumulate_checksum(self, decl):
        lines = []
        def generate_body(loop_vars):
            name = decl.name if not is_array(decl) else f'(*{ptr(decl).name})'
            return f'{self.no_indent()}total += {access(name, loop_vars)};'
        lines.append(self.nested_loops(self.access_bounds[decl.name],
                                       generate_body))
        return '\n'.join(lines)

    def calculate_checksum_code(self):
        lines = []
        ws = self.indent_in()
        lines.append(f'{ws}{default_type} total = 0.0;')
        self.indent_out()

        for decl in self.iterate_decls():
            lines.append(self.accumulate_checksum(decl))

        lines.append(f'{ws}return total;')
        return '\n'.join(lines)

    def core_externs(self):
        return '\n'.join([
            f'extern {self.decl(default_type, decl)};'
            for decl in self.iterate_decls(is_nonlocal_scalar)
        ])

    def core_params(self):
        return ', '.join([
            self.decl(default_type, decl, is_restrict=True)
            for decl in self.iterate_decls(is_nonlocal_array)
        ])

    def core_args(self):
        return ', '.join([
            f'*{ptr(decl).name}'
            for decl in self.iterate_decls(is_nonlocal_array)
        ])

    def ast(self, node):
        ty = type(node)
        if ty == Program:
            lines = []
            for stmt in node.body:
                lines.append(self.ast(stmt))
            return '\n'.join(lines)
        elif ty == AbstractLoop:
            # get loop vars, min_indices, max_indices
            loop_vars = []
            min_indices = []
            max_indices = []
            for shape in node.loop_shapes:
                loop_vars.append(self.ast(shape.loop_var))
                min_indices.append(self.ast(shape.greater_eq))
                max_indices.append(self.ast(shape.less_eq))
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
        else:
            assert(False)

    def core_code(self):
        return self.ast(self.pattern)

def generate_code(output_dir, instance):
    # setup directories
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # main
    src_main_c_path = f'codegen/main.template.c'
    dst_main_c_path = f'{output_dir}/main.c'
    copy2(src_main_c_path, dst_main_c_path)

    # make file
    src_make_path = f'codegen/Makefile'
    dst_make_path = f'{output_dir}/Makefile'
    copy2(src_make_path, dst_make_path)

    # prepare template dictionary
    cgen = CGenerator(instance)
    template_dict = {
        'data_defs': cgen.data_defs(),

        'allocate_heap_vars_code': cgen.allocate_heap_vars_code(),
        'initialize_values_code': cgen.initialize_values_code(),
        'calculate_checksum_code': cgen.calculate_checksum_code(),

        'core_externs': cgen.core_externs(),
        'core_params': cgen.core_params(),
        'core_args': cgen.core_args(),
        'core_code': cgen.core_code()
    }

    # wrapper
    # fill template
    wrapper_template_path = Path('codegen/wrapper.template.c')
    wrapper_template_str = wrapper_template_path.read_text()
    wrapper_template = Template(wrapper_template_str)
    wrapper_str = wrapper_template.substitute(template_dict)

    # write
    wrapper_dst_path = Path(f'{output_dir}/wrapper.c')
    wrapper_dst_path.write_text(wrapper_str)

    # core
    # fill template
    core_template_path = Path('codegen/core.template.c')
    core_template_str = core_template_path.read_text()
    core_template = Template(core_template_str)
    core_str = core_template.substitute(template_dict)

    # write
    core_dst_path = Path(f'{output_dir}/core.c')
    core_dst_path.write_text(core_str)
