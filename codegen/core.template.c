#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <assert.h>
#include <limits.h>
#include <math.h>
#include <string.h>

${scalar_externs}

unsigned long long core(${array_params}) {
${locals}
  struct timespec before, after;
  clock_gettime(CLOCK_MONOTONIC, &before);

${core_code}

  clock_gettime(CLOCK_MONOTONIC, &after);
  unsigned long long duration = (after.tv_sec - before.tv_sec) * 1e9;
  duration += after.tv_nsec - before.tv_nsec;
  return duration;
}
