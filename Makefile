all: qaTools snpCaller
clean:
	cd metaSNV/qaTools && $(MAKE) clean
	cd metaSNV/snpCaller && $(MAKE) clean

qaTools:
	cd metaSNV/$@ && $(MAKE)
snpCaller:
	cd metaSNV/$@ && $(MAKE)

.PHONY: all clean
