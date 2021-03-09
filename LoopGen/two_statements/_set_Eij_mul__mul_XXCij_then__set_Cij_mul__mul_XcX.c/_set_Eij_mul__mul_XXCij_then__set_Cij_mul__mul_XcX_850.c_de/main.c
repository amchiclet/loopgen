#include <x86intrin.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <assert.h>
#include <limits.h>
#include <string.h>

void *allocate();
void init(void*);
int kernel(void *);

void measure_init_();
void measure_start_();
void measure_stop_();

int read_arguments (int *n_iterations) {
	FILE *file = fopen ("codelet.data", "r");
  if (file == NULL) {
    return 0;
  }

  int dont_care;
  int n_read = fscanf(file, "%d %d", n_iterations, &dont_care);
  fclose(file);
  return n_read == 2;
}

void run(int n_iterations, void *data) {
  measure_init_();
  measure_start_();
  for (int i = 0; i < n_iterations; ++i) {
    kernel(data);
  }
  measure_stop_();
}

int main(int argc, char **argv) {
  // read arguments
  int n_iterations;
  if (!read_arguments(&n_iterations)) {
    printf("Failed to load codelet.data\n");
    return 1;
  }

  // allocate
  void *data = allocate();

  // initialize
  srand(0);
  init(data);

  // measure
  printf("Measuring with %d iterations\n", n_iterations);
  run(n_iterations, data);

  return 0;
}

