#!/usr/bin/env bash

docker run -p 8080:8080 --mount type=bind,source=$(pwd)/settings,target=/opt/lthn/etc \
   --mount type=bind,source=/dev/log,target=/dev/log \
   lthn/vpn run