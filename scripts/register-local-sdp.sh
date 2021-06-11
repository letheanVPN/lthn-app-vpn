#!/usr/bin/env bash

docker run --mount type=bind,source=$(pwd)/settings,target=/opt/lthn/etc \
   --mount type=bind,source=/dev/log,target=/dev/log \
   lthn/vpn upload-sdp