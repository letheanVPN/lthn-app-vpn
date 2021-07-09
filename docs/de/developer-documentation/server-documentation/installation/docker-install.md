### Docker version
You can build docker image for your instalation. It is probably easiest way for all of us because there are differences between systems.
Docker image is based on latest debian. It contains all tools needed to run. We did not upload our image into any repository yet. 
Only build script is available. In future, we plan to create more containers (dispatcher, proxy, vpn) but now only all-in-one version is available.

To build docker image:
```bash
make docker BUILD_ARGS='--build-arg PROVIDERID=1234 --build-arg BRANCH=master ...'
```

To run dispatcher, pointing its config data into local directory /opt/lthn/etc
Note: without pointing volume outside of dispatcher, you can loose your data after removing container!
```
docker run \
  -v /opt/lthn/etc:/opt/lthn/etc \
  -p 8080:8080 -p 8088:8088 \
  lethean/lethean-vpn:devel [easy-deploy|run|lthnvpnc|lthnvpnd|lvmgmt]
```
