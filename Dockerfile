FROM python:3-buster
MAINTAINER Snider <snider@lt.hn>

LABEL version="1.0"
LABEL description="Lethean VPN Exit Node"

RUN apt-get update; \
    apt-get upgrade -y; \
    apt-get install -y sudo joe less haproxy openvpn squid net-tools wget stunnel zsync pwgen unzip;

ARG DAEMON_BIN_URL="https://github.com/letheanVPN/blockchain-iz/releases/latest/download/linux.tar"
ARG DAEMON_HOST="seed.lethean.io"
ARG PORT="8080"

ENV LTHNPREFIX="/opt/lthn"

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

ENTRYPOINT ["/entrypoint-lethean-vpn.sh"]
CMD ["run"]

RUN useradd -ms /bin/bash lthn; \
  echo "lthn ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers; \
  mkdir /usr/src/lethean-vpn; \
  chown -R lthn /usr/src/lethean-vpn

WORKDIR /usr/src/lethean-vpn/build
RUN wget -nc -c $DAEMON_BIN_URL && mkdir -p /usr/bin/lethean-latest-linux && tar -xf $(basename $DAEMON_BIN_URL) -C /usr/bin/lethean-latest-linux && mv /usr/bin/lethean-latest-linux/lethean* /usr/bin && chmod +x /usr/bin/lethean*

USER root

COPY ./ /usr/src/lethean-vpn/

RUN rm -rf /usr/src/lethean-vpn/build/

RUN /usr/local/bin/python -m pip install --upgrade pip

RUN pip3 install -r /usr/src/lethean-vpn/requirements.txt

COPY ./server/docker-run.sh /entrypoint-lethean-vpn.sh

RUN chown -R lthn /usr/src/; \
  chmod +x /entrypoint-lethean-vpn.sh; \
  chmod +x /usr/src/lethean-vpn/install.sh;

RUN echo -e "domain lthn.local\nsearch lthn.local\nnameserver 127.0.0.1\n >/etc/resolv.conf"

USER lthn
WORKDIR /usr/src/lethean-vpn/
RUN chmod +x configure.sh; ./configure.sh --runas-user lthn --runas-group lthn --client;

RUN make install SERVER=1 CLIENT=1;

RUN rm -rf /opt/lthn/etc/ca /opt/lthn/etc/*.ini /opt/lthn/etc/*.json /opt/lthn/etc/*.pem /opt/lthn/etc/*.tlsauth /opt/lthn/etc/*.keys /opt/lthn/etc/provider* \
        /opt/lthn/var/* \
        /usr/src/lethean-vpn/build /usr/src/lethean-vpn/env.mk ; \
      mkdir -p /opt/lthn/var/log /opt/lthn/var/run;

WORKDIR /home/lthn
