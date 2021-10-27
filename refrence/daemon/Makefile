.PHONY: config run run-it shell all build

all: build


config:
	chmod +x scripts/create-provider-config.sh
	scripts/create-provider-config.sh || true # Ensure we remove +x perm on fail
	chmod -x scripts/create-provider-config.sh


run:
	chmod +x scripts/run-exit-node.sh
	scripts/run-exit-node.sh || true # Ensure we remove +x perm on fail
	chmod -x scripts/run-exit-node.sh

run-it:
	chmod +x scripts/interactive-shell.sh
	scripts/interactive-shell.sh || true # Ensure we remove +x perm on fail
	chmod -x scripts/interactive-shell.sh


build:
	docker build -t lthn/vpn -f Dockerfile ./src
