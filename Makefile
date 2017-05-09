GDBUS_APPS = bmcctl \
	     op-flasher \
	     op-pwrctl \
	     pwrbutton \
	     idbutton \
	     cable-led \
	     op-pwrctl-sthelens

SUBDIRS = hacks \
	  libopenbmc_intf \
	  libopenbmc_sdbus \
	  ledctl \
	  fanctl \
	  fan_tool \
	  pychassisctl \
	  pydownloadmgr \
	  pyeventctl \
	  pyfanctl \
	  pyflashbmc \
	  pyhwmon \
	  pyinventorymgr \
	  pyipmitest \
	  pysensormgr \
	  pystatemgr \
	  pysystemmgr \
	  pytools \
	  fan_algorithm \
	  info \
	  gpu \
	  node-init-sthelens \
	  pybmchealth_ctl  \
	  pex9797_ctl

REVERSE_SUBDIRS = $(shell echo $(SUBDIRS) $(GDBUS_APPS) | tr ' ' '\n' | tac |tr '\n' ' ')

.PHONY: subdirs $(SUBDIRS) $(GDBUS_APPS)

subdirs: $(SUBDIRS) $(GDBUS_APPS)

$(SUBDIRS):
	$(MAKE) -C $@

$(GDBUS_APPS): libopenbmc_intf
	$(MAKE) -C $@ CFLAGS="-I ../$^" LDFLAGS="-L ../$^"

install: subdirs
	@for d in $(SUBDIRS) $(GDBUS_APPS); do \
		$(MAKE) -C $$d $@ DESTDIR=$(DESTDIR) PREFIX=$(PREFIX) || exit 1; \
	done
clean:
	@for d in $(REVERSE_SUBDIRS); do \
		$(MAKE) -C $$d $@ || exit 1; \
	done
