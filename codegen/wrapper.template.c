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

${data_defs}

void allocate_arrays() {
${allocate_arrays_code}
}

float frand(float min, float max) {
  float scale = rand() / (float) RAND_MAX;
  return min + scale * (max - min);
}

int irand(int min, int max) {
  return min + (rand() % (max - min + 1));
}

double drand(double min, double max) {
  double scale = rand() / (double) RAND_MAX;
  return min + scale * (max - min);
}

void init_scalars() {
${init_scalars_code}
}

void init_arrays(${array_params}) {
${init_arrays_code}
}

void init_array_ptrs() {
  init_arrays(${array_args});
}

float calculate_checksum(${array_params}) {
${calculate_checksum_code}
}

void checksum() {
  srand(0);
  init_scalars();
  allocate_arrays();
  init_array_ptrs();
  float cs = calculate_checksum(${array_args});
  printf("Checksum is %f\n", cs);    
}

unsigned long long core(${array_params});

void measure(int n_iterations) {
  srand(0);
  init_scalars();
  allocate_arrays();
  init_array_ptrs();
  for (int i = 0; i < n_iterations; ++i) {
    unsigned long long runtime = core(${array_args});
    printf("Iteration %d %llu\n", i+1, runtime);
  }
}
