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
POLYPHONIC = polyphonic.py
DRUM_MACHINE = drum_machine.py
SAMPLER = sampler.py

all: clean compile upload requirements

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

requirements:
	circup install -r requirements.txt

monophonic:
	echo ./$(MONOPHONIC) "=>" $(DEVICE)code.py
	@cp ./$(MONOPHONIC) $(DEVICE)code.py

polyphonic:
	echo ./$(POLYPHONIC) "=>" $(DEVICE)code.py
	@cp ./$(POLYPHONIC) $(DEVICE)code.py

drum_machine:
	echo ./$(DRUM_MACHINE) "=>" $(DEVICE)code.py
	@cp ./$(DRUM_MACHINE) $(DEVICE)code.py

sampler:
	echo ./$(SAMPLER) "=>" $(DEVICE)code.py
	@cp ./$(SAMPLER) $(DEVICE)code.py
