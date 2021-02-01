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

int core(float A[restrict 692][657], float B[restrict 789][657], float C[restrict 789][692]) {
  for (int i = 733; i <= 788; i+=1) {
    for (int j = 270; j <= 656; j+=1) {
      for (int k = 260; k <= 691; k+=1) {
          B[i][j] = C[i][j] + C[i][k] * A[k][j];
      }
    }
  }
  return 0;
}

