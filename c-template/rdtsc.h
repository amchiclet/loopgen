#ifndef _RDTSC_H_
#define _RDTSC_H_

// Define rdtscll for x86_64 arch
#ifdef __x86_64__
	#define rdtscll(val) do { \
			unsigned int __a,__d; \
			asm volatile("rdtsc" : "=a" (__a), "=d" (__d)); \
			(val) = ((unsigned long)__a) | (((unsigned long)__d)<<32); \
	} while(0)
#endif


#endif

