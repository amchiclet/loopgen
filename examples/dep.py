from pattern import parse_str as parse_pattern
from instance import create_instance
from constant_assignment import VariableMap

code = """
declare A[100][100];
declare B[100][100];

for [(i, >=10, <=90), (j, >=10, <=90)] {
  A[i][j] = A[i-1][j-1] + 5;
}
"""

pattern = parse_pattern(code)
print(pattern.pprint())

instance = create_instance(pattern, VariableMap())
print(instance.pprint())

from dependence_analysis import analyze_dependence, calculate_distance_vectors

graph, annotated_instance = analyze_dependence(instance.pattern)
calculate_distance_vectors(graph)
print(graph.pprint())
