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

int core(${array_params}) {
${locals}
${core_code}
  return 0;
}
