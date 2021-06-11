# Welcome to Lethean VPN

This project provides the interface into the network, docker is a required dependency, for now.

Please get docker here: https://docs.docker.com/get-docker/

```
make config
```
or
```dockerfile
docker run -t -i \
   --mount type=bind,source=$(pwd)/settings,target=/opt/lthn/etc \
   lthn/vpn easy-deploy
```

your configuration will be placed in the settings folder.

```
make run
```
or
```dockerfile
 docker run -p 8080:8080 --mount type=bind,source=$(pwd)/settings,target=/opt/lthn/etc \
   --mount type=bind,source=/dev/log,target=/dev/log \
   lthn/vpn run
```