DEVICE := /media/$(USER)/CIRCUITPY/
ifeq ($(wildcard $(DEVICE).),)
	DEVICE := /run/media/$(USER)/CIRCUITPY/
endif

MPYCROSS = ./bin/mpy-cross

LIB_SRCS := \
	menu
LIB_MPY = $(LIB_SRCS:%=%.mpy)

SRCS := $(LIB_MPY)

MONOPHONIC = monophonic.py

all: clean compile upload

clean:
	@rm $(LIB_MPY) || true

compile: $(LIB_MPY:%=./%)

%.mpy: %.py
	$(MPYCROSS) -o $@ $<

upload: $(SRCS)
	@for file in $^ ; do \
		echo $${file} "=>" $(DEVICE)$${file} ; \
		cp $${file} $(DEVICE)$${file} ; \
	done

monophonic:
	echo ./$(MONOPHONIC) "=>" $(DEVICE)code.py
	@cp ./$(MONOPHONIC) $(DEVICE)code.py
