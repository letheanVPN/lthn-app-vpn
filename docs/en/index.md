# Virtual Private Network Documentation

Our exit node is deployed from Docker/OCI images, running a VPN node can be quite complex, we simplify this process by launching a fully contained VPS directly on your machine.

The ports are exposed to the host operating system and your configuration files are saved in the settings folder, after you made edits, restart the dispatcher for them to take effect.

## Install
1) Download [docker-compose.yml](https://gitlab.com/lthn.io/projects/vpn/node/-/raw/master/docker-compose.yml) to the installation directory you have made locally.
```shell
wget https://gitlab.com/lthn.io/projects/vpn/node/-/raw/master/docker-compose.yml >> ./docker-compose.yml
```

2) Create containers & start lethean vpn
```shell
docker-compose up -d
```

3) Configure your SDP
```shell
docker container exec -it dispatcher /lethean-vpn.sh easy-deploy
```
