from pattern import parse_str
from pattern_ast import Literal, Access, Op, AbstractLoop, get_ordered_assignments, get_ordered_loops
from dependence_analysis import analyze_dependence

# transitive closure of backward dependencies
class BackwardDependencies:
    def __init__(self):
        self.l = []
    def add(self, id1, id2):
        for s in self.l:
            if id1 in s or id2 in s:
                s.add(id1)
                s.add(id2)
                return
        new_s = set()
        new_s.add(id1)
        new_s.add(id2)
        self.l.append(new_s)
    def __str__(self):
        return '\n'.join([str(s) for s in self.l])
    def is_same_group(self, id1, id2):
        for s in self.l:
            if id1 in s:
                return id2 in s
            if id2 in s:
                return id1 in s
        return False

def get_backward_deps(loop_with_ids, stmt_deps):
    ordered_ids = [stmt.attributes['node_id'] for stmt in get_ordered_assignments(loop_with_ids)]
    print(ordered_ids)

    backward_deps = BackwardDependencies()

    reversed_ordered_ids = list(reversed(ordered_ids))
    n_ids = len(ordered_ids)
    for i in range(n_ids):
        latter = reversed_ordered_ids[i]
        for j in range(i+1, n_ids):
            former = reversed_ordered_ids[j]
            # detect backward dependencies
            if latter in stmt_deps and former in stmt_deps[latter]:
                print('back')
                backward_deps.add(latter, former)
    return backward_deps

# returns
def get_distributable(p):
    # statement-level dependency map: source_id => sink_id
    stmt_deps = {}

    dependence_graph, pattern_with_ids = analyze_dependence(p)
    for deps in dependence_graph.iterate_dependences():
        representive_dep = deps[0]
        source_id = representive_dep.source_ref.parent_stmt.attributes['node_id']
        sink_id = representive_dep.sink_ref.parent_stmt.attributes['node_id']
        if source_id not in stmt_deps:
            stmt_deps[source_id] = set()
            stmt_deps[source_id].add(sink_id)

    distributable = {}

    for loop in get_ordered_loops(pattern_with_ids):
        backward_deps = get_backward_deps(loop, stmt_deps)
        
        assert(len(loop.body) > 1)
        for i in range(len(loop.body)-1):
            current_id = loop.body[i].attributes['node_id']
            next_id = loop.body[i+1].attributes['node_id']
            if not backward_deps.is_same_group(current_id, next_id):
                loop_id = loop.attributes['node_id']
                if loop_id not in distributable:
                    distributable[loop_id] = []
                distributable[loop_id].append((i, i+1))
                print(f'cannot split {current_id} and {next_id}')
        print(backward_deps)
    return distributable, pattern_with_ids

code = """
declare A[];
declare B[];
declare C[];
declare D[];

for [(i, >=0, <=100, +=1)] {
  A[i] = B[i-1];
  B[i] = C[i-1];
  C[i] = B[i];
  D[i] = 0;
}
"""
p = parse_str(code)
distributable, pattern_with_ids = get_distributable(p)
for stmt in pattern_with_ids.body:
    stmt_id = stmt.attributes['node_id']
    if stmt_id in distributable:
        print(stmt)
        print(distributable[stmt_id])
# for loop, stmt_pairs in distributable.items():
#     print(loop)
#     print(stmt_pairs)
