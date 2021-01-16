from abstract_ast import Op, Access, Declaration, Assignment, AbstractLoop, Const, Program, VarRenamer

def greater_eq_const_name(loop_var):
    return f'{loop_var}_greater_eq'
def less_eq_const_name(loop_var):
    return f'{loop_var}_less_eq'

def rename_to_order(pattern, original_order, sorted_order):
    replace_map_1 = {}
    for i, name in enumerate(original_order):
        replace_map_1[name] = '__' + str(i)
    renamer_1 = VarRenamer(replace_map_1)
    pattern.replace(renamer_1)

    replace_map_2 = {}
    for i, name in enumerate(sorted_order):
        replace_map_2['__' + str(i)] = name
    renamer_2 = VarRenamer(replace_map_2)
    pattern.replace(renamer_2)

def rename_decls(pattern, original_decls, sorted_decls):
    pass

def normalize_loop_var_order(pattern, sorted_loop_vars):
    ordered_loop_vars = []
    def populate_loop_vars(node):
        if isinstance(node, AbstractLoop):
            for shape in node.loop_shapes:
                assert(type(shape.loop_var) == Access)
                loop_var = shape.loop_var.var
                if loop_var not in ordered_loop_vars:
                    ordered_loop_vars.append(loop_var)
            for stmt in node.body:
                populate_loop_vars(stmt)
        elif isinstance(node, Program):
            for stmt in node.body:
                populate_loop_vars(stmt)
        elif isinstance(node, Assignment):
            pass
        else:
            raise RuntimeError('populate_loop_vars: Unhandled {type(node)}')
    populate_loop_vars(pattern)
    rename_to_order(pattern, ordered_loop_vars, sorted_loop_vars)

    ordered_greater_eq = list(map(greater_eq_const_name, ordered_loop_vars))
    sorted_greater_eq = list(map(greater_eq_const_name, sorted_loop_vars))
    rename_to_order(pattern, ordered_greater_eq, sorted_greater_eq)

    ordered_less_eq = list(map(less_eq_const_name, ordered_loop_vars))
    sorted_less_eq = list(map(less_eq_const_name, sorted_loop_vars))
    rename_to_order(pattern, ordered_less_eq, sorted_less_eq)

def normalize_access_order(pattern, sorted_decls, sorted_muls,
                           sorted_maybe_zero_muls, sorted_adds, sorted_datas):
    def populate_var_usage(node, var_pool):
        ordered_var_usage = []
        def recurse(node):
            if isinstance(node, AbstractLoop):
                for stmt in node.body:
                    recurse(stmt)
            elif isinstance(node, Program):
                for stmt in node.body:
                    recurse(stmt)
            elif isinstance(node, Assignment):
                recurse(node.lhs)
                recurse(node.rhs)
            elif isinstance(node, Access):
                if node.var not in ordered_var_usage and node.var in var_pool:
                    ordered_var_usage.append(node.var)
                for index in node.indices:
                    recurse(index)
            elif isinstance(node, Op):
                for arg in node.args:
                    recurse(arg)
            elif isinstance(node, Literal):
                pass
            else:
                raise RuntimeError(f'normalized_decl_order: Unhandled {type(node)}')
        recurse(node)
        return ordered_var_usage

    def get_decl_map(decls):
        decl_map = {}
        for decl in decls:
            key = (decl.n_dimensions, decl.is_local)
            if key not in decl_map:
                decl_map[key] = []
            decl_map[key].append(decl.name)
        return decl_map

    all_decl_names = [decl.name for decl in sorted_decls]
    original_decl_names = populate_var_usage(pattern, all_decl_names)
    # print(f'original decl names {original_decl_names}')
    pattern.decls[:] = [pattern.get_decl(name) for name in original_decl_names]
    original_decls = [decl for decl in pattern.decls]
    original_decl_map = get_decl_map(pattern.decls)
    sorted_decl_map = get_decl_map(sorted_decls)
    for k, original_decl_order in original_decl_map.items():
        sorted_decl_order= sorted_decl_map[k]
        # print(f'renaming {original_decl_order} {sorted_decl_order}')
        rename_to_order(pattern, original_decl_order, sorted_decl_order)

    original_muls = populate_var_usage(pattern, sorted_muls)
    pattern.consts[:] = [c for c in pattern.consts
                         if c.name not in sorted_muls or c.name in original_muls]
    rename_to_order(pattern, original_muls, sorted_muls)

    original_maybe_zero_muls = populate_var_usage(pattern, sorted_maybe_zero_muls)
    pattern.consts[:] = [c for c in pattern.consts
                         if c.name not in sorted_maybe_zero_muls or c.name in original_maybe_zero_muls]
    rename_to_order(pattern, original_maybe_zero_muls, sorted_maybe_zero_muls)

    original_adds = populate_var_usage(pattern, sorted_adds)
    pattern.consts[:] = [c for c in pattern.consts
                         if c.name not in sorted_adds or c.name in original_adds]
    rename_to_order(pattern, original_adds, sorted_adds)

    original_datas = populate_var_usage(pattern, sorted_datas)
    pattern.consts[:] = [c for c in pattern.consts
                         if c.name not in sorted_datas or c.name in original_datas]
    rename_to_order(pattern, original_datas, sorted_datas)

    pattern.decls.sort(key=lambda decl: decl.name)
    pattern.consts.sort(key=lambda const: const.name)

def normalize_pattern(pattern, decls, mul_consts,
                      maybe_zero_mul_consts, add_consts, data_consts, loop_vars):
    normalize_loop_var_order(pattern, sorted(loop_vars))
    normalize_access_order(pattern,
                           sorted(decls, key=lambda decl:decl.name),
                           sorted(mul_consts),
                           sorted(maybe_zero_mul_consts),
                           sorted(add_consts),
                           sorted(data_consts))
