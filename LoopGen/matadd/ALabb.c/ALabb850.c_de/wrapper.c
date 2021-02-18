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

unsigned long long core(double A[restrict 850][850], double B[restrict 850][850], double C[restrict 1][1]);

struct Data {
  double (*A)[850][850];
  double (*B)[850][850];
  double (*C)[1][1];
};

float frand(float min, float max) {
  float scale = rand() / (float) RAND_MAX;
  return min + scale * (max - min);
}

float irand(int min, int max) {
  return min + (rand() % (max - min));
}

double drand(double min, double max) {
  double scale = rand() / (double) RAND_MAX;
  return min + scale * (max - min);
}

void *allocate() {
  struct Data *data = malloc(sizeof(struct Data));
  data->A = malloc(sizeof(double) * 850 * 850);
  data->B = malloc(sizeof(double) * 850 * 850);
  data->C = malloc(sizeof(double) * 1 * 1);
  return (void*)data;
}

int init_inner(double A[restrict 850][850], double B[restrict 850][850], double C[restrict 1][1]) {
  for (int i0 = 0; i0 <= 849; ++i0) {
    for (int i1 = 0; i1 <= 849; ++i1) {
      double v = drand(0.0, 1.0);
      A[i0][i1] = v;
    }
  }
  for (int i0 = 0; i0 <= 849; ++i0) {
    for (int i1 = 0; i1 <= 849; ++i1) {
      double v = drand(0.0, 1.0);
      B[i0][i1] = v;
    }
  }
  for (int i0 = 0; i0 <= 0; ++i0) {
    for (int i1 = 0; i1 <= 0; ++i1) {
      double v = drand(0.0, 1.0);
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

