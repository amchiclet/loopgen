from skeleton import parse_str as parse_skeleton
from skeleton_ast import Var
from populator import PopulateParameters, populate_name

def fill_name_hole():
    # A name hole is surrounded by backticks
    # It has two portions:
    # * its name
    # * its family name
    # For example, the hole x1:X has name x1 and family X
    code = """
        declare A[];
        declare B[];
        declare C[];
        declare D[];

        for [i] {
            `x1:X`[i] = `x2:X`[i];
            `y1:Y`[i] = `y2:Y`[i];
        }
    """

    skeleton = parse_skeleton(code)
    print(skeleton.pprint())

    # For each family, we add the possible options to fill that hole.
    # Name holes are filled with variables, so we need to provide
    # Var nodes as options.
    parameters = PopulateParameters()
    parameters.add('X', [Var('A'), Var('B')])
    parameters.add('Y', [Var('C'), Var('D')])

    filled_skeleton = populate_name(skeleton, parameters.populate)
    print(filled_skeleton.pprint())

fill_name_hole()

def fill_hole_with_default_family():
    # The family name is optional. It defaults to the family named "_"
    # (an underscore).
    code = """
        declare A[];
        declare B[];
        declare C[];
        declare D[];

        for [i] {
            `x1`[i] = `x2`[i];
            `y1:_`[i] = `y2:_`[i];
        }
    """

    skeleton = parse_skeleton(code)
    print(skeleton.pprint())

    # x1, x2, y1, and y2 all belonw to family _.
    parameters = PopulateParameters()
    parameters.add('_', [Var('A'), Var('B'), Var('C'), Var('D')])

    filled_skeleton = populate_name(skeleton, parameters.populate)
    print(filled_skeleton.pprint())

fill_hole_with_default_family()

def fill_hole_with_same_name():
    # Holes with the same name will be filled with the same choice.
    #
    # The name "_" (an underscore) is special. Two "_" are always
    # considered to be different. As a result, two "_" holes may be
    # filled with different options.
    #
    # Holes with different names may be different (but can also be the
    # same by random choice).
    #
    # In this code, all x1 holes should look the same. The x2 hole may
    # be anything. The two _ holes may be anything and don't have to
    # be the same.
    code = """
        declare A[];
        declare B[];
        declare C[];
        declare D[];

        for [i] {
            `x1`[i] = `_`[i];
            `x1`[i] = `_`[i];
            `x1`[i] = `x2`[i];
        }
    """

    skeleton = parse_skeleton(code)
    print(skeleton.pprint())

    parameters = PopulateParameters()
    parameters.add('_', [Var('A'), Var('B'), Var('C'), Var('D')])

    filled_skeleton = populate_name(skeleton, parameters.populate)
    print(filled_skeleton.pprint())
    
fill_hole_with_same_name()
