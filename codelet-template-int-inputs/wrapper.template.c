#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <assert.h>
#include <limits.h>
#include <math.h>
#include <string.h>

${define_scalars}
${define_arrays_as_pointers}

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

void init_scalars(int inputs[16]) {
${init_scalars_code}
}

void init_arrays(${array_params_as_ptr}) {
${init_arrays_code_as_ptr}
}

void init_array_ptrs() {
  init_arrays(${array_args_as_ptr});
}

int core(${array_params});

void measure(int inputs[16]) {
  srand(0);
  init_scalars(inputs);
  allocate_arrays();
  init_array_ptrs();

  struct timespec before, after;
  clock_gettime(CLOCK_MONOTONIC, &before);
  core(${array_args});
  clock_gettime(CLOCK_MONOTONIC, &after);
  unsigned long long duration =
      (after.tv_sec - before.tv_sec) * 1e9 +
      (after.tv_nsec - before.tv_nsec);
  printf("Runtime = %llu nanosecs\n", duration);
}
