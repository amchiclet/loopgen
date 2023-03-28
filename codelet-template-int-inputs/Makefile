CC=gcc
CFLAGS=-c -g -O2
LDFLAGS=-g -lm
EXEC=run

all: $(EXEC)

$(EXEC): core.o wrapper.o main.o
	$(CC) -o $@ $^ $(LDFLAGS)

main.o: main.c
	$(CC) -g -o $@ $< $(CFLAGS) -c -O0

wrapper.o: wrapper.c
	$(CC) -g -o $@ $< $(CFLAGS) -c -O0

%.o: %.s %.c
	$(CC) -o $@ $< $(CFLAGS)

clean:
	rm -rf *.o $(EXEC)
