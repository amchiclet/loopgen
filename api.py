from pattern import parse_str, parse_stmt_str, parse_expr_str, Program
from populator import PopulateParameters, populate_stmt, populate_expr
from constant_assignment import VariableMap
from random import choice
from instance import try_create_instance
from type_assignment import TypeAssignment
from codegen.c_generator import generate_code
from pathlib import Path

class Mapping:
    def __init__(self, family_name, choices, is_finite=False, choice_function=choice):
        self.family_name = family_name
        self.choices = choices
        self.is_finite = is_finite
        self.choice_function = choice

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

    def fill(self, mappings, parse_function, populate_function):
        populator = PopulateParameters()
        for mapping in mappings:
            parsed = [parse_function(choice) for choice in mapping.choices]
            populator.add(mapping.family_name,
                          parsed,
                          mapping.is_finite,
                          mapping.choice_function)
        populated = populate_function(self.program.clone(), populator.populate)
        return Skeleton(populated)
    def fill_expressions(self, mappings):
        return self.fill(mappings, parse_expr_str, populate_expr)
    def fill_statements(self, mappings):
        return self.fill(mappings, parse_stmt_str, populate_stmt)

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

        instance = try_create_instance(self.program, var_map, type_assignment)
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
