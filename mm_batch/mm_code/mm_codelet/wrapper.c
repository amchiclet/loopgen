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

unsigned long long core(float A[restrict 692][657], float B[restrict 789][657], float C[restrict 789][692]);

struct Data {
  float (*A)[692][657];
  float (*B)[789][657];
  float (*C)[789][692];
};

float frand(float min, float max) {
  float scale = rand() / (float) RAND_MAX;
  return min + scale * (max - min);
}

float irand(int min, int max) {
  return min + (rand() % (max - min));
}

void *allocate() {
  struct Data *data = malloc(sizeof(struct Data));
  data->A = malloc(sizeof(float) * 692 * 657);
  data->B = malloc(sizeof(float) * 789 * 657);
  data->C = malloc(sizeof(float) * 789 * 692);
  return (void*)data;
}

int init_inner(float A[restrict 692][657], float B[restrict 789][657], float C[restrict 789][692]) {
  for (int i0 = 260; i0 <= 691; ++i0) {
    for (int i1 = 270; i1 <= 656; ++i1) {
      float v = frand(0.0, 1.0);
      A[i0][i1] = v;
    }
  }
  for (int i0 = 733; i0 <= 788; ++i0) {
    for (int i1 = 270; i1 <= 656; ++i1) {
      float v = frand(0.0, 1.0);
      B[i0][i1] = v;
    }
  }
  for (int i0 = 733; i0 <= 788; ++i0) {
    for (int i1 = 260; i1 <= 691; ++i1) {
      float v = frand(0.0, 1.0);
      C[i0][i1] = v;
    }
  }
  return 0;
}

int init(void *void_ptr) {
  struct Data *data = (struct Data*)void_ptr;
  return init_inner(*data->A, *data->B, *data->C);
};

int kernel(void *void_ptr) {
  struct Data *data = (struct Data*)void_ptr;
  return core(*data->A, *data->B, *data->C);
};

