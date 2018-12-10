PASS=1234
CN=ItnsVPNFakeCN
DOCKER=docker

-include env.mk

all:
	@echo "Choose what you want to do."
	@echo "make install|docker-img"
	@exit 2
	

install:
	if [ -f env.mk ]; then \
	 INSTALL_PREFIX=$(INSTALL_PREFIX) \
	 FORCE=$(FORCE) \
	 LTHN_PREFIX=$(LTHN_PREFIX) \
	 OPENVPN_BIN=$(OPENVPN_BIN) \
	 PYTHON_BIN=$(PYTHON_BIN) \
	 PIP_BIN=$(PIP_BIN) \
	 SUDO_BIN=$(SUDO_BIN) \
	 HAPROXY_BIN=$(HAPROXY_BIN) \
	 OPENSSL_BIN=$(OPENSSL_BIN) \
	 LTHN_USER=$(LTHN_USER) \
	 LTHN_GROUP=$(LTHN_GROUP) \
	  ./install.sh; \
	else \
	 echo "You must configure first!" ; ./configure.sh --help; exit 1; \
	fi
	
clean:
	@echo Note this cleans only build directory. If you want to uninstall package, do it manually by removing files from install location.
	@echo Your last install dir is $(LTHN_PREFIX)
	rm -rf build

ca: build/ca/index.txt
	
build/ca/index.txt: env.mk
	./configure.sh --generate-ca --with-capass "$(PASS)" --with-cn "$CN"

docker-img:
	mkdir -p build/etc
	docker build --build-arg "HTTP_PROXY=$$HTTP_PROXY" --build-arg "HTTPS_PROXY=$$HTTPS_PROXY" $(BUILD_ARGS) -t lethean/lethean-vpn:devel .

docker: docker-img

docker-clean:
	docker rm -v lethean-vpn:devel 

docker-shell:
	 docker run -i -t lethean/lethean-vpn:devel bash
	 