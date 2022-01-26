# Welcome to Lethean VPN

This project provides the interface into the VPN sub systems.

This does work; the project not being enabled is more to do with network hashrate concerns.

Feb 6th; once the network establishes I will reassess the safety of the network with this enable and report back.

Until then; this project will work to a programmer.

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


