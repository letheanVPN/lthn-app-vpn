# syntax=docker/dockerfile:1
FROM python:3.8-slim-buster
MAINTAINER Lukas Macura <lukas@lethean.io>
MAINTAINER Snider <snider@lethean.io>

LABEL "io.lthn.vpn-server"="Lethean.IO"
LABEL version="1.0"
LABEL description="Lethean VPN Server"

ARG DAEMON_HOST="seed.lethean.io"

ENV LTHNPREFIX="/home/lthn"
# Daemon host. Set to empty string to use local daemon with complete copy of blockchain.
ENV DAEMON_HOST="$DAEMON_HOST"
# Wallet file. It is relative to etc directory.
ENV WALLET_FILE="vpn"
# If you want to use external wallet, set this to RPC of external wallet host
ENV WALLET_RPC_URI=""
# Wallet password. Default is to generate random password
ENV WALLET_PASSWORD=""
# Wallet RPC password. Default is to generate random password. Username used by dispatcher is 'dispatcher'
ENV WALLET_RPC_PASSWORD=""
# To restore wallet from this height. Only applicable for local wallet.
ENV WALLET_RESTORE_HEIGHT=349516
# CA password. Default to generate random password
ENV CA_PASSWORD=""
# Common Name for CN
ENV CA_CN="LTHNEasyDeploy"
# If you already have providerid. In other case, autogenerate
ENV PROVIDER_ID=""
# If you already have providerkey. In other case, autogenerate
ENV PROVIDER_KEY=""
# Provider name
ENV PROVIDER_NAME="EasyProvider"
# Provider type
ENV PROVIDER_TYPE="residential"
# Service endpoint. You need to change this in SDP later
ENV ENDPOINT="127.0.0.1"
# Service port
ENV PORT="$PORT"


RUN useradd -ms /bin/bash lthn; \
  apt-get update; \
  apt-get install -y make build-essential sudo joe less haproxy openvpn squid net-tools wget stunnel pwgen; \
  rm -rf /var/lib/apt/lists/*; \
  echo "lthn ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers; \
  mkdir /home/lthn/vpn; \
  chown -R lthn /home/lthn/vpn

WORKDIR /home/lthn/vpn/build

COPY --from=lthn/chain /home/lthn/bin/chain /usr/bin

COPY ./src /home/lthn/vpn/

RUN rm -rf /home/lthn/vpn/build/

COPY --chown=lthn:lthn ./src/server/docker-run.sh /lethean-vpn.sh

RUN chown -R lthn /home/lthn/vpn; \
  chmod +x /lethean-vpn.sh; \
  chmod +x /home/lthn/vpn/install.sh
RUN echo -e "domain lthn.local\nsearch lthn.local\nnameserver 127.0.0.1\n >/etc/resolv.conf"

RUN pip3 install --upgrade pip; pip3 install -r /home/lthn/vpn/requirements.txt ;

USER lthn

WORKDIR /home/lthn/vpn

RUN chmod +x configure.sh; ./configure.sh --runas-user lthn --runas-group lthn --client

RUN make install SERVER=1 CLIENT=1

RUN mkdir -p /home/lthn/vpn/var/log /home/lthn/vpn/var/run ;

CMD ["run"]
ENTRYPOINT ["/lethean-vpn.sh"]
