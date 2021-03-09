\#include <stdio.h>
\#include <stdlib.h>
\#include <string.h>

\#include "rdtsc.h"

#set param_vars = ['double (*'+v+')[n]' for v in $vars]
#set $args = ', '.join($param_vars)
int codelet_ (int n, int, $args, int, double);
/* int codelet_ (int n, int, double(*a)[n], int, double); */

void measure_init_();
void measure_start_();
void measure_stop_();

unsigned long long alignUp(unsigned long long original, unsigned int align) {
        return (original +align - (original % align));
}


int read_arguments (int* nb_elements,int* repetitions)
{
	FILE* file;

	file = fopen ("codelet.data", "r");

	if (file != NULL)
	{
		int res;

		res = fscanf (file, "%d %d", repetitions, nb_elements);
		if (res != 2)
		{
			fclose (file);
			return -1;
		}

		fclose (file);

		return 0;
	}
	return -1;
}


int main (int argc, char** argv)
{
	unsigned long long int before, after;
	int nb_elements, repetitions;


	unsigned long long int nb_iters = 0;

	int i, n;

	if (read_arguments (&nb_elements, &repetitions) == -1){
		printf ("Failed to load codelet.data!\n");
		return -1;
	}

	printf ("Nb elements: %d.\n", nb_elements);
	printf ("Nb repetitions: %d.\n", repetitions);

	unsigned int align = 32;
        int m = nb_elements;
	n = nb_elements;
        double g = 1.0;

	unsigned long long alignedSize = alignUp(sizeof(double)*n*m, align);

#for $var in $vars
	double (*$var)[m] = (double(*)[m]) malloc (alignedSize);
#end for

#set not_vars = ['!'+v for v in $vars]
#set conds = '||'.join($not_vars)
	if ($conds)
	{
		printf ("Could not allocate one of the main arrays.\n");
		return -1;
	}

#for $var in $vars
	memset ($var, 0, n * m * sizeof(double));
#end for


//	rdtscll (before);
 	measure_init_();
        measure_start_();

	for (i = 0; i < repetitions; i++)
	{
		#set args = ','.join($vars)
		nb_iters += codelet_ (n, m, $args, 0, g);
	}
        measure_stop_();

//	rdtscll (after);

	nb_iters /= repetitions;

	printf ("Nb iters: %llu.\n", nb_iters);
//	printf ("RDTSC: %lf.\n", ((double)(after - before)) / (double)repetitions / (double)nb_iters );


	return 0;

}
