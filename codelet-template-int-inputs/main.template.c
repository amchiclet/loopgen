#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <assert.h>
#include <limits.h>
#include <string.h>

void read_arguments (int argc, char **argv, int inputs[16]) {
  for (int i = 0; i < argc; i += 1) {
    inputs[i] = atoi(argv[i]);
  }
}

void measure(int inputs[16]);

int main(int argc, char **argv) {
  int inputs[16];
  read_arguments(argc, argv, inputs);
  measure(inputs);
  return 0;
}
