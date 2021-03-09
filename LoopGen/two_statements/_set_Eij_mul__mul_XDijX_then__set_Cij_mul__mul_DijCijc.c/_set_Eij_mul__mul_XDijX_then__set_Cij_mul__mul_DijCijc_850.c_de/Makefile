CC=icc
CFLAGS=-c -g -std=c99 -O3 -xSSE4.2
LDFLAGS=-g -lm
EXEC=wrapper
LIBS=-lmeasure
# For now
LIBPATH=../../../../lib

all: $(EXEC)

$(EXEC): core.o wrapper.o main.o
	$(CC) -o $@ $^ $(LDFLAGS) $(LIBS) -L$(LIBPATH)

main.o: main.c
	$(CC) -g -o $@ $< $(CFLAGS) -c -O0

wrapper.o: wrapper.c
	$(CC) -g -o $@ $< $(CFLAGS) -c -O0

%.o: %.s %.c
	$(CC) -o $@ $< $(CFLAGS)

clean:
	rm -rf *.o $(EXEC)
