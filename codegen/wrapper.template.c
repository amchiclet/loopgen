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

void allocate_heap_vars() {
${allocate_heap_vars_code}
}

void init() {
  srand(0);
${initialize_values_code}
}

float calculate_checksum() {
${calculate_checksum_code}
}

void checksum() {
  allocate_heap_vars();
  init();
  float cs = calculate_checksum();
  printf("Checksum is %f\n", cs);    
}

unsigned long long core(${core_params});

void measure(int n_iterations) {
  allocate_heap_vars();
  init();
  for (int i = 0; i < n_iterations; ++i) {
    unsigned long long runtime = core(${core_args});
    printf("Iteration %d %llu\n", i+1, runtime);
  }
}
