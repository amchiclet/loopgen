from pattern import parse_str, parse_stmt_str, parse_expr_str, Program
from pattern_ast import get_accesses
from populator import PopulateParameters, populate_stmt, populate_expr, populate_op
from constant_assignment import VariableMap
from random import choice
from instance import try_create_instance
from type_assignment import TypeAssignment
from codegen.c_generator import generate_code
from pathlib import Path
from dependence_analysis import analyze_dependence, calculate_distance_vectors

class Mapping:
    def __init__(self, family_name, choices, is_finite=False, choice_function=choice):
        self.family_name = family_name
        self.choices = choices
        self.is_finite = is_finite
        self.choice_function = choice
    def __str__(self):
        return f'{self.family_name} = {{{",".join([str(c) for c in self.choices])}}}'

class Skeleton:
    def __init__(self, code):
        if isinstance(code, str):
            self.program = parse_str(code)
        elif isinstance(code, Program):
            self.program = code
        else:
            raise RuntimeError(f"Unknown type for code: {type(code)}")

    def __str__(self):
        return self.program.pprint()

    def fill(self, mappings, parse_function, populate_function, matching_function):
        populator = PopulateParameters()
        for mapping in mappings:
            parsed = [parse_function(choice) for choice in mapping.choices]
            populator.add(mapping.family_name,
                          parsed,
                          mapping.is_finite,
                          mapping.choice_function)
        populated = populate_function(self.program.clone(), populator.populate, matching_function)
        return Skeleton(populated)

    # matching_function takes in two family names
    # 1) the node's family name
    # 2) the family name specified in mappings
    # and returns True iff they are considered a match.
    def fill_expressions(self, mappings, matching_function=None):
        return self.fill(mappings, parse_expr_str, populate_expr, matching_function)
    def fill_statements(self, mappings, matching_function=None):
        return self.fill(mappings, parse_stmt_str, populate_stmt, matching_function)
    def fill_operations(self, mappings, matching_function=None):
        # An op is just a string. Return it.
        def parse_op(s):
            return s
        return self.fill(mappings, parse_op, populate_op, matching_function)

    # Single threaded
    def generate_code(self, config):
        if '_' in config.possible_values:
            default_range = config.possible_values['_']
            if len(default_range) == 1:
                min_val = 0
                max_val = default_range
            else:
                min_val = default_range[0]
                max_val = default_range[1]
            var_map = VariableMap(default_min = min_val, default_max = max_val)
        else:
            var_map = VariableMap()

        for var, value in config.possible_values.items():
            if isinstance(value, int):
                var_map.set_value(var, value)
            elif isinstance(value, tuple):
                var_map.set_range(var, value[0], value[1])
            else:
                raise RuntimeError(f"Unknown type for value: {type(value)}")

        type_assignment = TypeAssignment(default_types=['int'])

        for var, ty in config.types.items():
            type_assignment.set(var, ty)

        # Infer non-explicit decls
        possible_values = None
        if config.array_size_depends_on_possible_values:
            possible_values = config.possible_values
        self.program.populate_decls(possible_values)

        instance = try_create_instance(self.program, var_map, type_assignment, config.force)
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)

        import pattern_ast
        old_array_as_ptr = pattern_ast.array_as_ptr
        pattern_ast.array_as_ptr = config.array_as_ptr

        generate_code(config.output_dir,
                      instance,
                      init_value_map=config.initial_values,
                      template_dir=config.template_dir)

        pattern_ast.array_as_ptr = old_array_as_ptr

class CodegenConfig:
    def __init__(self):
        self.possible_values = None
        self.types = None
        self.initial_values = None
        self.output_dir = None
        self.template_dir = None
        self.array_as_ptr = False
        self.array_size_depends_on_possible_values = False
        self.force = False
