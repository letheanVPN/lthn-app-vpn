PASS=1234
CN=ItnsVPNFakeCN

all:
	@echo "Use make config|install|clean|ca PASS=password"

config: build/env.sh

build/env.sh:
	./configure.sh

install: build/env.sh
	INSTALL_PREFIX=$(INSTALL_PREFIX) ./install.sh

clean:
	@echo Note this cleans only build directory. If you want to uninstall package, do it manually by removing files from install location.
	@. build/env.sh ; echo Your last install dir is $$ITNS_PREFIX
	rm -rf build

ca: build/ca/index.txt

build/ca/index.txt: build/env.sh
	if [ -z "$(PASS)" ]; then echo "make ca PASS=password"; exit 2; fi
	./configure.sh --generate-ca --with-capass "$(PASS)" --with-cn "$CN"
