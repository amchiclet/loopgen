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

int core(double A[restrict 850][850], double B[restrict 850][850], double C[restrict 1][1], double D[restrict 850][850], double E[restrict 850][850], double a, double b, double c) {
  for (int i = 0; i <= 849; i+=1) {
    for (int j = 0; j <= 849; j+=1) {
        E[i][j] = (1.5 + 1.5) + A[i][j];
        D[i][j] = (1.5 + B[i][j]) + c;
    }
  }
  return 0;
}

