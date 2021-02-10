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

int core(double A[restrict 850][850], double B[restrict 850][850], double C[restrict 1][1]) {
  for (int i = 0; i <= 849; i+=1) {
    for (int j = 0; j <= 849; j+=1) {
      for (int k = 0; k <= 849; k+=1) {
          A[i][j] = A[i][j] + B[i][k] * A[k][j];
      }
    }
  }
  return 0;
}

