#!/bin/sh
# Copyright 2019-2021 the Deno authors & Lethean VPN. All rights reserved. MIT license.
# TODO(everyone): Keep this script simple and easily auditable.

set -e

if ! command -v unzip >/dev/null; then
	echo "Error: unzip is required to install lthn." 1>&2
	exit 1
fi

if [ "$OS" = "Windows_NT" ]; then
	target="windows"
else
	case $(uname -sm) in
	"Darwin x86_64") target="macos-intel" ;;
	"Darwin arm64") target="macos-arm64" ;;
	*) target="linux" ;;
	esac
fi

	lthn_uri="https://gitlab.com/lthn/projects/vpn/node/-/jobs/artifacts/dvpn-v2/download?job=${target}"


deno_install="${HOME}/Lethean"
bin_dir="$deno_install"
exe="$bin_dir/lthn"

if [ ! -d "$bin_dir" ]; then
	mkdir -p "$bin_dir"
fi

curl --fail --location --progress-bar --output "$exe.zip" "$lthn_uri"
unzip -d "$bin_dir" -o "$exe.zip"
chmod +x "$exe"
rm "$exe.zip"

echo "Lethean CLI was installed successfully to $exe"
if command -v lthn >/dev/null; then
	echo "Run 'lthn --help' to get started"
else
	case $SHELL in
	/bin/zsh) shell_profile=".zshrc" ;;
	*) shell_profile=".bash_profile" ;;
	esac
	echo "Manually add the directory to your \$HOME/$shell_profile (or similar)"
	echo "  export LETHEAN_CLI=\"$deno_install:$deno_install/cli\""
	echo "  export PATH=\"\$LETHEAN_CLI:\$PATH\""
	echo "Run '$exe --help' to get started"
fi

