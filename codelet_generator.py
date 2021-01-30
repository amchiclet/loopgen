from pathlib import Path
from c_generator import CGenerator
from shutil import copytree

def conf_contents(codelet):
    return (f'<?xml version="1.0" ?>\n'
            f'<codelet>\n'
            f'  <language value="C"/>\n'
            f'  <label name="{codelet}"/>\n'
            f'  <function name="codelet"/>\n'
            f'  <binary name="wrapper"/>\n'
            f'</codelet>\n')

def meta_contents(batch, code, codelet):
    return (f'application name=LoopGen\n'
            f'batch name={batch}\n'
            f'code name={code}\n'
            f'codelet name={codelet}\n')

def data_contents(n_iterations):
    return f'{n_iterations} 0\n'

def codelet_dir(batch, code, codelet, base='.'):
    return f'{base}/{batch}/{code}/{codelet}'

def meta_file(codelet_dir):
    return f'{codelet_dir}/codelet.meta'

def conf_file(codelet_dir):
    return f'{codelet_dir}/codelet.conf'

def data_file(codelet_dir):
    return f'{codelet_dir}/codelet.data'

def prepare_output_dir(dst_dir):
    copytree('c-template', dst_dir)

# def generate_directories(batch, code, codelet, base='.'):
#     path = Path(get_codelet_dir(batch, code, codelet, base))
#     path.mkdir(parents=True, exist_ok=True)

def generate_codelet(batch, code, codelet, n_iterations, instance):
    dst_dir = codelet_dir(batch, code, codelet)
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
