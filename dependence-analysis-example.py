from pattern import parse_str, parse_stmt_str, parse_expr_str
from dependence_analysis import analyze_dependence, calculate_distance_vectors

code_tiled = """
declare I;
declare J;
declare K;
declare A[][][];
declare B[][][];

for [
  (i, >=0, <=100, +=10),
  (j, >=0, <=100, +=10),
  (k, >=0, <=100, +=10),
  (ii, >=i, <=i+10, +=1),
  (jj, >=j, <=j+10, +=1),
  (kk, >=k, <=k+10, +=1)
] {
  A[i][j+1][k] = A[i][j][k+1];
}
"""

program = parse_str(code_tiled)
print(program)
dg, program_ex = analyze_dependence(program)
print(dg)
