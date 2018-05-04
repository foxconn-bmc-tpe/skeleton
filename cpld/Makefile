BINS=cpld
EXTRA_OBJS+=ast-jtag.o \
            lattice.o

#ALL_CFLAGS+=-Ipflash
include ../gdbus.mk
include ../rules.mk

%.o: cpld_1/%.c
	$(CC) -c $(ALL_CFLAGS) -o $@ $<

#BINS=lettice
#BINS+=ast-jtag
#BINS+=main
#LDLIBS+=-lopenbmc_sdbus
#include ../sdbus.mk
#include ../rules.mk
