CC=gcc
CFLAGS=-c -g -std=c99 -O3 -xSSE4.2
CFLAGS=-c -g -std=c99 -O3
LDFLAGS=-g -lm
EXEC=wrapper
LIBS=-lmeasure
# For now
LIBPATH=../../../../nr-codelets/codeletProbe

all: \$(EXEC)

\$(EXEC): codelet.o driver.o
	\$(CC) -o \$@ \$^ \$(LDFLAGS) \$(LIBS) -L\$(LIBPATH)

driver.o: driver.c
	\$(CC) -g -o \$@ \$< -c -O0

%.o: %.s %.c
	\$(CC) -o \$@ \$< \$(CFLAGS)

clean:
	rm -rf *.o \$(EXEC)
