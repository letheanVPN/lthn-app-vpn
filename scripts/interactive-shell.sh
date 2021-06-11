#!/usr/bin/env bash

docker run -i -t --mount type=bind,source=$(pwd)/settings,target=/opt/lthn/etc \
   --mount type=bind,source=/dev/log,target=/dev/log \
   lthn/vpn sh