#include <x86intrin.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <assert.h>
#include <limits.h>
#include <math.h>
#include <string.h>

int core(double A[restrict 1][1], double B[restrict 850][850], double C[restrict 1][1], double D[restrict 850][850], double E[restrict 850][850], double a, double b, double c) {
  for (int i = 0; i <= 849; i+=1) {
    for (int j = 0; j <= 849; j+=1) {
        D[i][j] = (b + 1.5) + c;
        E[i][j] = (1.5 * B[i][j]) * b;
    }
  }
  return 0;
}

