#ifdef INST
#ifeq ("$(origin INST)", "command line")
#INSTALL_DIR := $(INST)
#endif
#endif

#CFLAGS += -Wall
#OBJS	= main.o lattice.o ast-jtag.o
#EXE	= cpld
#INSTALL_DIR = /usr/sbin

#CC      = $(CROSS_COMPILE)gcc

#%.o : %.c
#	$(CC) $(CFLAGS) -c $< -o $@ -I.

#$(EXE): $(OBJS)
#	$(CC) $(CFLAGS) $" -o $@ -I.

#clean:
#	rm -f $(EXE) $(OBJS)

#install:
#	cp $(EXE) $(DESTDIR)
#	cp $(EXE) $(INSTALL_DIR)
CFLAGS += -Wall
OBJS	= lattice.o ast-jtag.o
EXE	= cpld
#CC      = $(CROSS_COMPILE)gcc
#CC      = gcc
#all=cpld
#cpld: $(OBJS)
#	$(CC) $(CFLAGS) $^ -o $@
#main.o: main.c
#	$(CC) $(CFLAGS) –c $< -o $@
#lattice.o: lattice.c
#	$(CC) $(CFLAGS) –c $< -o $@
#ast-jtag.o: ast-jtag.c
#	$(CC) $(CFLAGS) –c $< -o $@
#INSTALL_DIR = /usr/sbin

#CC      = $(CROSS_COMPILE)gcc

.c.o:
	$(CC) $(CFLAGS) -c $<

$(EXE): $(OBJS)
	$(CC) $(CFLAGS) $(OBJS) -o $@

#install:
#	cp $(EXE) $(INSTALL_DIR)
#	install $(EXE) $(INSTALL_DIR)
