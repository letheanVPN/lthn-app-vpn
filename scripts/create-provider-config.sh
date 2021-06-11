#!/usr/bin/env bash

docker run --name=lethean-vpn -t -i \
   --mount type=bind,source=$(pwd)/settings,target=/opt/lthn/etc \
   --mount type=bind,source=/dev/log,target=/dev/log \
   lthn/vpn easy-deploy
