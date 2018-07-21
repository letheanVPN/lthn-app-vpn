PASS=1234
CN=ItnsVPNFakeCN

-include env.mk

all:
env.mk:
	@if ! [ -f env.mk ]; then echo "You must configure first!" ; ./configure.sh --help; exit 1; fi
	@echo "Seems to be configured. Run make install."	

install: env.mk
	INSTALL_PREFIX=$(INSTALL_PREFIX) \
	FORCE=$(FORCE) \
	ITNS_PREFIX=$(ITNS_PREFIX) \
	OPENVPN_BIN=$(OPENVPN_BIN) \
	PYTHON_BIN=$(PYTHON_BIN) \
	PIP_BIN=$(PIP_BIN) \
	SUDO_BIN=$(SUDO_BIN) \
	HAPROXY_BIN=$(HAPROXY_BIN) \
	OPENSSL_BIN=$(OPENSSL_BIN) \
	ITNS_USER=$(ITNS_USER) \
	ITNS_GROUP=$(ITNS_GROUP) \
	./install.sh
	
clean:
	@echo Note this cleans only build directory. If you want to uninstall package, do it manually by removing files from install location.
	@echo Your last install dir is $(ITNS_PREFIX)
	rm -rf build

ca: build/ca/index.txt
	
build/ca/index.txt: env.mk
	./configure.sh --generate-ca --with-capass "$(PASS)" --with-cn "$CN"

