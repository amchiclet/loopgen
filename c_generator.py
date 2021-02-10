from math import floor

def loop_header(indent, loop_var, begin, end):
    return '  ' * indent + \
        (f'for (int {loop_var} = {begin}; '
         f'{loop_var} <= {end}; '
         f'++{loop_var}) {{')

def frand():
    return """float frand(float min, float max) {
  float scale = rand() / (float) RAND_MAX;
  return min + scale * (max - min);
}"""

def drand():
    return """double drand(double min, double max) {
  double scale = rand() / (double) RAND_MAX;
  return min + scale * (max - min);
}"""

def irand():
    return """float irand(int min, int max) {
  return min + (rand() % (max - min));
}"""

def include():
    return """#include <x86intrin.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <assert.h>
#include <limits.h>
#include <math.h>
#include <string.h>"""

def spaces(indent):
    return '  ' * indent

default_type = 'double'

# TODO: test program needs to be a different program
class CGenerator:
    def __init__(self, instance):
        self.pattern = instance.pattern
        self.sorted_decl_names = sorted([decl.name for decl in self.pattern.decls])
        self.decl_map = {decl.name:decl for decl in self.pattern.decls}
        self.array_sizes = instance.array_sizes
        self.indent = 0

    def array_param(self, ty, name, sizes):
        brackets = ''
        is_first = True
        for size in sizes:
            if is_first:
                brackets += f'[restrict {size}]'
                is_first = False
            else:
                brackets += f'[{size}]'
        return f'{ty} {name}{brackets}'

    def array_local(self, ty, name, sizes):
        brackets = ''.join([f'[{size}]' for size in sizes])
        return f'{ty} {name}{brackets}'

    def array_decl(self, ty, name, sizes):
        ws = spaces(self.indent)
        return f'{ws}{ty} (*{name})' + (''.join([f'[{size}]' for size in sizes]) + ';')

    def declare_data(self):
        lines = []
        ws = spaces(self.indent)
        lines.append('struct Data {')
        self.indent += 1
        for array_name in sorted(self.array_sizes.keys()):
            array = self.array_sizes[array_name]
            sizes = [max_index + 1 for max_index in array.max_indices]
            if not array.is_local:
                lines.append(self.array_decl(default_type, array_name, sizes))
        self.indent -= 1
        lines.append('};')
        return '\n'.join(lines)

    def nested_loop(self, loop_vars, min_indices, max_indices, body_lines):
        lines = []
        # loop headers
        for loop_var, min_index, max_index in zip(loop_vars, min_indices, max_indices):
            lines.append(loop_header(self.indent, loop_var, min_index, max_index))
            self.indent += 1
        ws = spaces(self.indent)
        for body_line in body_lines:
            lines.append(f'{ws}{body_line}')

        # close brackets
        for _ in range(len(loop_vars)):
            self.indent -= 1
            lines.append('  ' * self.indent + '}')
        return '\n'.join(lines)

    def checksum_inner(self):
        lines = []
        ws = spaces(self.indent)

        params = []
        for array_name in sorted(self.array_sizes.keys()):
            array = self.array_sizes[array_name]
            sizes = [max_index + 1 for max_index in array.max_indices]
            if not array.is_local:
                params.append(self.array_param(default_type, array_name, sizes))

        lines.append(f'{ws}{default_type} checksum_inner({", ".join(params)}) {{')

        self.indent += 1
        ws = spaces(self.indent)

        lines.append(f'{ws}{default_type} total = 0.0;')

        for array_name in sorted(self.array_sizes.keys()):
            array = self.array_sizes[array_name]
            if array.is_local:
                continue
            loop_vars = [f'i{dimension}' for dimension in range(array.n_dimensions)]
            indices_str = ''.join([f'[{loop_var}]' for loop_var in loop_vars])
            access = f'{array_name}{indices_str}'
            body_lines = [
                f'if (isnormal({access})) {{ total += {access}; }}',
                f'else {{ total += 0.1; }}',
            ]

            lines.append(self.nested_loop(loop_vars, array.min_indices, array.max_indices, body_lines))

        lines.append(f'{ws}return total;')
        self.indent -= 1
        ws = spaces(self.indent)
        lines.append(f'{ws}}}')
        return '\n'.join(lines)

    def cast_data(self):
        ws = spaces(self.indent)
        return f'{ws}struct Data *data = (struct Data*)void_ptr;'
    def return_inner(self, function_name, scalar_as_array=False):
        ws = spaces(self.indent)
        params = []
        for array_name in sorted(self.array_sizes.keys()):
            array = self.array_sizes[array_name]
            if not array.is_local:
                if array.n_dimensions == 0 and scalar_as_array:
                    params.append(f'*({default_type} (*)[1])data->{array_name}')
                else:
                    params.append(f'*data->{array_name}')

        # params = [f'*data->{field}' for field in sorted(self.array_sizes.keys())]
        return f'{ws}return {function_name}({", ".join(params)});'

    def wrapper(self, return_type, wrapper_name, inner_name, scalar_as_array=False):
        lines = []
        ws = spaces(self.indent)
        lines.append(f'{ws}{return_type} {wrapper_name}(void *void_ptr) {{')
        self.indent += 1
        lines.append(self.cast_data())
        lines.append(self.return_inner(inner_name, scalar_as_array))
        self.indent -= 1
        lines.append(f'{ws}}};')
        return '\n'.join(lines)

    def init(self):
        return self.wrapper('int', 'init', 'init_inner', scalar_as_array=True)
    def checksum(self):
        return self.wrapper(default_type, 'checksum', 'checksum_inner')
    def kernel(self):
        return self.wrapper('int', 'kernel', 'core')
    def declare_core(self):
        params = []
        for name in self.sorted_decl_names:
            decl = self.decl_map[name]
            if not decl.is_local:
                params.append(self.array_param(default_type, name, decl.sizes))
        ws = spaces(self.indent)
        return f'{ws}unsigned long long core({", ".join(params)});'
    def array_allocate(self, ty, array_names, sizes):
        lines = []
        ws = spaces(self.indent)
        
        # malloc
        if len(sizes) == 0:
            total_size_str = '1'
        else:
            total_size_str = ' * '.join([f'{size}' for size in sizes])
        for array_name in array_names:
            lines.append(f'{ws}{array_name} = malloc(sizeof({ty}) * {total_size_str});')
        return '\n'.join(lines)

    def array_init(self, ty, array_names, min_indices, max_indices, init_value):
        lines = []
        ws = spaces(self.indent)
        loop_vars = [f'i{dimension}' for dimension in range(len(min_indices))]
        n_dimensions = len(loop_vars)

        # loop headers
        if n_dimensions > 0:
            for dimension, loop_var in enumerate(loop_vars):
                lines.append(loop_header(self.indent, loop_var, min_indices[dimension], max_indices[dimension]))
                self.indent += 1
        else:
            lines.append(f'{ws}{{')
            self.indent += 1

        # loop body
        ws = spaces(self.indent)
        init_var = 'v'
        init_stmt = f'{ws}{ty} {init_var} = {init_value};'
        lines.append(init_stmt)
        indices_str = ''.join([f'[{loop_var}]' for loop_var in loop_vars])
        for array_name in array_names:
            lines.append(f'{ws}{array_name}{indices_str} = {init_var};')

        # close brackets
        if n_dimensions > 0:
            for _ in range(n_dimensions):
                self.indent -= 1
                lines.append('  ' * self.indent + '}')
        else:
            self.indent -= 1
            lines.append('  ' * self.indent + '}')

        return '\n'.join(lines)

    def allocate(self):
        lines = []
        lines.append(f'void *allocate() {{')
        self.indent += 1
        ws = spaces(self.indent)
        lines.append(f'{ws}struct Data *data = malloc(sizeof(struct Data));')
        for array_name in sorted(self.array_sizes.keys()):
            array = self.array_sizes[array_name]
            if not array.is_local:
                lhs = f'data->{array_name}'
                sizes = [max_index + 1 for max_index in array.max_indices]
                lines.append(self.array_allocate(default_type, [lhs], sizes))
        lines.append(f'{ws}return (void*)data;')
        self.indent -= 1
        lines.append('}')

        return '\n'.join(lines)

    # TODO: create initialization program
    def init_inner(self):
        lines = []

        # array parameters
        params = []
        for array_name in sorted(self.array_sizes.keys()):
            array = self.array_sizes[array_name]
            if not array.is_local:
                if array.n_dimensions == 0:
                    params.append(self.array_param(default_type, array_name, [1]))
                else:
                    sizes = [max_index + 1 for max_index in array.max_indices]
                    params.append(self.array_param(default_type, array_name, sizes))
    
        # function header
        lines.append(f'int init_inner({", ".join(params)}) {{')
        self.indent += 1

        # Seed the randomizer
        ws = spaces(self.indent)
        # lines.append(f'{ws}allocate();')

        init_value = 'drand(0.0, 1.0)'
        for array_name in sorted(self.array_sizes.keys()):
            array = self.array_sizes[array_name]
            if not array.is_local:
                # for scalars, the initialization treats it as a one element array
                if array.n_dimensions == 0:
                    lines.append(self.array_init(default_type, [array_name],
                                                 [0], [0],
                                                 init_value))
                else:
                    loop_ends = [size - 1 for size in sizes]
                    lines.append(self.array_init(default_type, [array_name],
                                                 array.min_indices, array.max_indices,
                                                 init_value))

        lines.append(f'{ws}return 0;')

        # close function
        self.indent -= 1
        lines.append('}')

        return '\n'.join(lines)

    # TODO: create run program
    def run(self):
        return run()
    def main(self):
        return main()
    def core(self):
        lines = []
        ws = spaces(self.indent)

        params = []
        for name in self.sorted_decl_names:
            decl = self.decl_map[name]
            if not decl.is_local:
                params.append(self.array_param(default_type, name, decl.sizes))
        lines.append(f'{ws}int core({", ".join(params)}) {{')
        self.indent += 1
        ws = spaces(self.indent)
        for name in self.sorted_decl_names:
            decl = self.decl_map[name]
            if decl.is_local:
                local_decl = self.array_local(default_type, name, decl.sizes)
                lines.append(f'{ws}{local_decl};')
        lines.append(self.pattern.cprint(self.indent))
        lines.append(f'{ws}return 0;')
        self.indent -= 1
        ws = spaces(self.indent)
        lines.append(f'{ws}}}')
        return '\n'.join(lines)

    def write_kernel_wrapper(self, file_name):
        with open(file_name, 'w') as f:
            f.write(include())
            f.write('\n\n')
            f.write(self.declare_core())
            f.write('\n\n')
            f.write(self.declare_data())
            f.write('\n\n')
            f.write(frand())
            f.write('\n\n')
            f.write(irand())
            f.write('\n\n')
            f.write(drand())
            f.write('\n\n')
            f.write(self.allocate())
            f.write('\n\n')
            f.write(self.init_inner())
            f.write('\n\n')
            f.write(self.init())
            f.write('\n\n')
            f.write(self.kernel())
            f.write('\n\n')
        
    def write_core(self, file_name):
        with open(file_name, 'w') as f:
            f.write(include())
            f.write('\n\n')
            f.write(self.core())
            f.write('\n\n')
