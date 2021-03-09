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

int core(double A[restrict 420][420], double B[restrict 1][1], double C[restrict 420][420], double D[restrict 420][420], double E[restrict 420][420], double a, double b, double c) {
  for (int i = 0; i <= 419; i+=1) {
    for (int j = 0; j <= 419; j+=1) {
        D[i][j] = (1.5 * A[i][j]) * C[i][j];
        E[i][j] = c + a * E[i][j];
    }
  }
  return 0;
}

