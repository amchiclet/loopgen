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

int core(double A[restrict 1][1], double B[restrict 420][420], double C[restrict 420][420], double D[restrict 420][420], double E[restrict 1][1], double a, double b, double c) {
  for (int i = 0; i <= 419; i+=1) {
    for (int j = 0; j <= 419; j+=1) {
        C[i][j] = 1.5 + 1.5 * 1.5;
        B[i][j] = D[i][j] * b + b;
    }
  }
  return 0;
}
