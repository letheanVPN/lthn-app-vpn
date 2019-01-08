FROM python:3.7.1-stretch
MAINTAINER Lukas Macura <lukas@lethean.io>

LABEL "io.lethean.vpn-server"="Lethean.IO"
LABEL version="1.0"
LABEL description="Letehan.io VPN server"

ARG DAEMON_BIN_URL="https://github.com/LetheanMovement/lethean/releases/download/v3.0.0/lethean-cli-linux-64bit-v3.0.0.tar.bz2"
ARG DAEMON_HOST="sync.lethean.io"
ARG PORT="8080"

ARG ZSYNC_URL="https://monitor.lethean.io/bc/data.mdb.zsync"
ARG ZSYNC_DATA_URL="http://monitor.lethean.io/bc/data.mdb"
ARG ZSYNC_DATA_SHA="http://monitor.lethean.io/bc/data.mdb.sha256"

ENV LTHNPREFIX="/opt/lthn"
ENV DAEMON_HOST="$DAEMON_HOST"

ENV WALLET_FILE="vpn"
ENV WALLET_RPC_URI=""
ENV WALLET_PASSWORD=""
ENV WALLET_RPC_PASSWORD=""
ENV WALLET_RESTORE_HEIGHT=349516

ENV CA_PASSWORD=""
ENV CA_CN="LTHNEasyDeploy"

ENV PROVIDER_ID=""
ENV PROVIDER_KEY=""
ENV PROVIDER_NAME="EasyProvider"
ENV PROVIDER_TYPE="residential"
ENV ENDPOINT="127.0.0.1"
ENV PORT="$PORT"

ENV ZABBIX_SERVER="zabbix"
ENV ZABBIX_HOSTNAME="lethean-vpn"
ENV ZABBIX_META="LETHEANNODE"

ENV ZSYNC_URL="$ZSYNC_URL"
ENV ZSYNC_DATA_URL="$ZSYNC_DATA_URL"
ENV ZSYNC_DATA_SHA="$ZSYNC_DATA_SHA"

ENTRYPOINT ["/entrypiont-lethean-vpn.sh"]
CMD ["run"]

RUN useradd -ms /bin/bash lthn; \
  apt-get update; \
  apt-get install -y sudo joe less haproxy openvpn squid net-tools wget stunnel zsync pwgen; \
  echo "lthn ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers; \
  mkdir /usr/src/lethean-vpn; \
  chown -R lthn /usr/src/lethean-vpn

WORKDIR /usr/src/lethean-vpn/build
RUN wget -nc -c $DAEMON_BIN_URL && \
   tar --strip-components 1 -C /usr/bin/ -xjvf $(basename $DAEMON_BIN_URL)
RUN wget https://repo.zabbix.com/zabbix/4.0/debian/pool/main/z/zabbix-release/zabbix-release_4.0-2+stretch_all.deb && \
   dpkg -i zabbix-release_4.0-2+stretch_all.deb
RUN apt-get update && apt-get install -y zabbix-agent zabbix-sender && mkdir /var/run/zabbix && chown -R lthn /var/log/zabbix /var/run/zabbix
RUN sed -i "s/Hostname=(.*)/Hostname=$ZABBIX_HOSTNAME/" /etc/zabbix/zabbix_agentd.conf; \
  sed -i "s/Server=(.*)/Server=$ZABBIX_SERVER/" /etc/zabbix/zabbix_agentd.conf; \
  sed -i "s/ServerActive=(.*)/ServerActive=$ZABBIX_SERVER/" /etc/zabbix/zabbix_agentd.conf; \
  sed -i "s/Hostname=(.*)/Hostname=$ZABBIX_HOSTNAME/" /etc/zabbix/zabbix_agentd.conf; \
  sed -i "s/HostMetadata=(.*)/HostMetadata=$ZABBIX_META/" /etc/zabbix/zabbix_agentd.conf;

USER root
COPY ./ /usr/src/lethean-vpn/
RUN pip3 install -r /usr/src/lethean-vpn/requirements.txt
COPY ./server/docker-run.sh /entrypiont-lethean-vpn.sh
RUN chown -R lthn /usr/src/; \
  chmod +x /entrypiont-lethean-vpn.sh; \
  chmod +x /usr/src/lethean-vpn/install.sh

USER lthn
WORKDIR /usr/src/lethean-vpn/
RUN chmod +x configure.sh; ./configure.sh --runas-user lthn --runas-group lthn --client
RUN make install SERVER=1 CLIENT=1
RUN rm -rf /opt/lthn/etc/ca /opt/lthn/etc/*.ini /opt/lthn/etc/*.json /opt/lthn/etc/*.pem /opt/lthn/etc/*.tlsauth /opt/lthn/etc/*.keys /opt/lthn/etc/provider* \
        /opt/lthn/var/* \
        /usr/src/lethean-vpn/build /usr/src/lethean-vpn/env.mk ; \
      mkdir -p /opt/lthn/var/log /opt/lthn/var/run;

WORKDIR /home/lthn
