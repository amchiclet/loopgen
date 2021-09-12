#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <assert.h>
#include <limits.h>
#include <string.h>

void checksum();
void measure(int n_iterations);

int main(int argc, char **argv) {
  if (argc < 2) {
    printf("Not enough number of arguments\n"
           "Usage:\n\n"
           " To run the program N times and print out the time it takes to execute:\n"
           "   <program> --measure N\n\n"
           " To run the program once and calculate the checksum of the output:\n"
           "   <program> --checksum\n\n");
    return 1;
  }

  if (strcmp(argv[1], "--measure") == 0) {
    if (argc < 3) {
      printf("Not enough number of arguments for measure mode\n");
      return 1;
    }
    int n_iterations = atoi(argv[2]);
    printf("Measuring with %d iterations\n", n_iterations);
    measure(n_iterations);
    return 0;
  } else if (strcmp(argv[1], "--checksum") == 0) {
    printf("Calculating checksum\n");
    checksum();
    return 0;
  } else {
    printf("Unsupported command %s\n", argv[1]);
    return 1;
  }
}

