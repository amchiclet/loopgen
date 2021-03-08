from skeleton import parse_str as parse_skeleton

code = """
declare A[];
declare B[];

for [i] {
  `_`[i] = `_`[i];
}
"""

skeleton = parse_skeleton(code)
print(skeleton.pprint())
