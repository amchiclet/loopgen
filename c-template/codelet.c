#set param_vars = ['double (*'+v+')[n]' if $vartypes[v] == 'A' else 'double *'+v for v in $vars]
#set $args = ', '.join($param_vars)
int codelet_ (int n, int, $args, int, double);
int codelet_(int n, int m, $args, int ${cStride}, double g) {

    int ${cNonStride};
    int k; /* needed for matmul */
    for (${cNonStride}=0; ${cNonStride}<m; ${cNonStride}++) {
      for (${cStride}=0; ${cStride}<n; ${cStride}++) {
        #for $stmt in $stmts
        $stmt
        #end for
      }
    }
    return m*n;
}
