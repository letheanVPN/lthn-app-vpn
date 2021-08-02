# Welcome to Lethean VPN

This project provides the interface into the VPN Marketplace.

For full documentation visit [https://lt.hn/en/doc/vpn](https://lt.hn/en/docs/vpn).

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


