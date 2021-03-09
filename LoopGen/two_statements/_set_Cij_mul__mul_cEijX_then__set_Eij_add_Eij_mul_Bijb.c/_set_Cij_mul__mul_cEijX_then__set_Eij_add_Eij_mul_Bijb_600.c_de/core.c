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

int core(double A[restrict 1][1], double B[restrict 600][600], double C[restrict 600][600], double D[restrict 1][1], double E[restrict 600][600], double a, double b, double c) {
  for (int i = 0; i <= 599; i+=1) {
    for (int j = 0; j <= 599; j+=1) {
        C[i][j] = (c * E[i][j]) * 1.5;
        E[i][j] = E[i][j] + B[i][j] * b;
    }
  }
  return 0;
}

