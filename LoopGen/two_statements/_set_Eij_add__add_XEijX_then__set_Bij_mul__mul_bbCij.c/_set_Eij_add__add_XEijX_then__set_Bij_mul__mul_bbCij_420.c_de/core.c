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

int core(double A[restrict 1][1], double B[restrict 420][420], double C[restrict 420][420], double D[restrict 1][1], double E[restrict 420][420], double a, double b, double c) {
  for (int i = 0; i <= 419; i+=1) {
    for (int j = 0; j <= 419; j+=1) {
        E[i][j] = (1.5 + E[i][j]) + 1.5;
        B[i][j] = (b * b) * C[i][j];
    }
  }
  return 0;
}

