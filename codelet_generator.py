from pathlib import Path
from c_generator import CGenerator
from shutil import copytree

def conf_contents(codelet):
    return (f'<?xml version="1.0" ?>\n'
            f'<codelet>\n'
            f'  <language value="C"/>\n'
            f'  <label name="{codelet}"/>\n'
            f'  <function name="core"/>\n'
            f'  <binary name="wrapper"/>\n'
            f'</codelet>\n')

def meta_contents(batch, code, codelet):
    return (f'application name=LoopGen\n'
            f'batch name={batch}\n'
            f'code name={code}\n'
            f'codelet name={codelet}\n')

def data_contents(n_iterations):
    return f'{n_iterations} 0\n'

def codelet_dir(application, batch, code, codelet, base='.'):
    return f'{base}/{application}/{batch}/{code}/{codelet}'

def meta_file(codelet_dir):
    return f'{codelet_dir}/codelet.meta'

def conf_file(codelet_dir):
    return f'{codelet_dir}/codelet.conf'

def data_file(codelet_dir):
    return f'{codelet_dir}/codelet.data'

def prepare_output_dir(dst_dir):
    copytree('c-template', dst_dir, dirs_exist_ok=True)

def name_many(nodes, delimiter=''):
    return delimiter.join([name(node) for node in nodes])

def name(node):
    from pattern_ast import Hex, Assignment, AbstractLoop, Literal, Access, Program, Op
    ty = type(node)
    if ty == Literal:
        return 'X'
    if ty == Hex:
        return node.str_val
    if ty == Assignment:
        return f'_set_{name(node.lhs)}{name(node.rhs)}'
    if ty == Access:
        return f'{node.var}{name_many(node.indices)}'
    if ty == AbstractLoop:
        return '_then_'.join([name(stmt) for stmt in node.body])
    if ty == Op:
        op_map = {
            '+': '_add_',
            '*': '_mul_'
        }
        return f'{op_map[node.op]}{name_many(node.args)}'
    if ty == Program:
        assert(len(node.body) == 1)
        return name(node.body[0])
    print(ty)

def generate_codelet_full(application, batch, code, codelet, n_iterations, instance):
    dst_dir = codelet_dir(application, batch, code, codelet)
    prepare_output_dir(dst_dir)

    Path(meta_file(dst_dir)).write_text(meta_contents(batch, code, codelet))
    Path(conf_file(dst_dir)).write_text(conf_contents(codelet))
    Path(data_file(dst_dir)).write_text(data_contents(n_iterations))

    cgen = CGenerator(instance)
    print(cgen.core())
    wrapper_path = f'{dst_dir}/wrapper.c'
    cgen.write_kernel_wrapper(wrapper_path)
    core_path = f'{dst_dir}/core.c'
    cgen.write_core(core_path)

def generate_codelet(batch, instance):
    # C code generation
    application = 'LoopGen'
    code_prefix = f'{name(instance.pattern)}'
    code = f'{code_prefix}.c'
    codelet = f'{code_prefix}.c_de'
    n_iterations = 10

    generate_codelet_full(application, batch, code, codelet, n_iterations, instance)
