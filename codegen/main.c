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
float checksum(void*);
unsigned long long kernel(void *);

void run(int n_iterations, void *data) {
  for (int i = 0; i < n_iterations; ++i) {
    unsigned long long runtime = kernel(data);
    printf("Iteration %d %llu\n", i+1, runtime);
  }
}

int main(int argc, char **argv) {
  if (argc < 2) {
    printf("Not enough number of arguments\n");
    printf("Usage:\n\n");
    printf(" To run the program N times and print out the time it takes to execute:\n");
    printf("   <program> --measure N\n\n");
    printf(" To run the program once and calculate the checksum of the output:\n");
    printf("   <program> --checksum\n\n");
    return 1;
  }

  srand(0);
  if (strcmp(argv[1], "--measure") == 0) {
    if (argc < 3) {
      printf("Not enough number of arguments for measure mode\n");
      return 1;
    }
    int n_iterations = atoi(argv[2]);
    printf("Measuring with %d iterations\n", n_iterations);
    void *data = allocate();
    init(data);
    run(n_iterations, data);
    return 0;
  } else if (strcmp(argv[1], "--checksum") == 0) {
    printf("Calculating checksum\n");
    void *data = allocate();
    init(data);
    kernel(data);
    float cs = checksum(data);
    printf("Checksum is %f\n", cs);
    return 0;
  } else {
    printf("Unsupported command %s\n", argv[1]);
    return 1;
  }
}

