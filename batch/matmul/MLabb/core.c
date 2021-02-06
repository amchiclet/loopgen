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

int core(float A[restrict 850][850], float B[restrict 850][850], float C[restrict 1][1]) {
  for (int i = 0; i <= 849; i+=1) {
    for (int j = 0; j <= 849; j+=1) {
      for (int k = 0; k <= 849; k+=1) {
          A[j][i] = A[j][i] + B[j][k] * B[k][i];
      }
    }
  }
  return 0;
}

