\#include "rdtsc.h"

void getticks_(unsigned long *tick)
{
     rdtscll(*tick);
}
