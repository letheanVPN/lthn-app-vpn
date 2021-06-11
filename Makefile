all: build

.PHONY: config
config:
	chmod +x scripts/create-provider-config.sh
	scripts/create-provider-config.sh || true # Ensure we remove +x perm on fail
	chmod -x scripts/create-provider-config.sh

.PHONY: run
run:
	chmod +x scripts/run-exit-node.sh
	scripts/run-exit-node.sh || true # Ensure we remove +x perm on fail
	chmod -x scripts/run-exit-node.sh

.PHONY: shell
shell:
	chmod +x scripts/interactive-shell.sh
	scripts/interactive-shell.sh || true # Ensure we remove +x perm on fail
	chmod -x scripts/interactive-shell.sh

.PHONY: build
build:
	cd src
	 $(MAKE) -C src docker

.PHONY: push
push:
	docker push lthn/vpn:latest

