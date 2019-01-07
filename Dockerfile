FROM python:3.7.1-stretch
MAINTAINER Lukas Macura <lukas@lethean.io>

LABEL "io.lethean.vpn-server"="Lethean.IO"
LABEL version="1.0"
LABEL description="Letehan.io VPN server"

ARG PROVIDERID=""
ARG PROVIDERKEY=""
ARG DAEMON_BIN_URL="https://github.com/LetheanMovement/lethean/releases/download/v3.0.0/lethean-cli-linux-64bit-v3.0.0.tar.bz2"
ARG DAEMON_HOST="sync.lethean.io"
ARG WALLETFILE="vpn"
ARG WALLETPASS="abcd1234"
ARG CAPASS=1234
ARG CACN=ITNSFakeNode
ARG ENDPOINT="1.2.3.4"
ARG PORT="8080"
ARG PROVTYPE="residential"
ARG EMAIL=""
ARG ZABBIX_SERVER="localhost"
ARG ZABBIX_HOSTNAME="localhost"
ARG ZABBIX_META="LETHEANNODE"
ARG HTTP_PROXY="${HTTP_PROXY}"
ARG HTTPS_PROXY="${HTTPS_PROXY}"
ARG NO_PROXY=""
ARG PUBLIC_BUILD="y"
ARG ZSYNC_URL="https://monitor.lethean.io/bc/data.mdb.zsync"
ARG ZSYNC_DATA_URL="http://monitor.lethean.io/bc/data.mdb"
ARG ZSYNC_DATA_SHA="http://monitor.lethean.io/bc/data.mdb.sha256"

ENV LTHNPREFIX="/opt/lthn"
ENV PORT="$PORT"
ENV DAEMON_HOST="$DAEMON_HOST"
ENV WALLETFILE="$WALLETFILE"
ENV WALLETPASS="$WALLETPASS"
ENV CAPASS="$CAPASS"
ENV ZABBIX_SERVER="$ZABBIX_SERVER"
ENV ZABBIX_HOSTNAME="$ZABBIX_HOSTNAME"
ENV ZABBIX_META="$ZABBIX_META"
ENV ENDPOINT="$ENDPOINT"
ENV PROVTYPE="$PROVTYPE"
ENV ZSYNC_URL="$ZSYNC_URL"
ENV ZSYNC_DATA_URL="$ZSYNC_DATA_URL"

ENTRYPOINT ["/entrypiont-lethean-vpn.sh"]
CMD ["run"]

RUN useradd -ms /bin/bash lthn; \
  apt-get update; \
  apt-get install -y sudo joe less haproxy openvpn squid net-tools wget stunnel zsync; \
  echo "lthn ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers; \
  mkdir /usr/src/lethean-vpn; \
  chown -R lthn /usr/src/lethean-vpn

WORKDIR /usr/src/lethean-vpn
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

USER lthn
COPY ./requirements.txt /usr/src/lethean-vpn/

USER root
RUN pip3 install -r /usr/src/lethean-vpn/requirements.txt
COPY ./ /usr/src/lethean-vpn/
COPY ./server/docker-run.sh /entrypiont-lethean-vpn.sh
RUN chown -R lthn /usr/src/; \
  chmod +x /entrypiont-lethean-vpn.sh; \
  chmod +x /usr/src/lethean-vpn/install.sh

USER lthn
RUN chmod +x configure.sh; ./configure.sh --runas-user lthn --runas-group lthn --client
RUN make install SERVER=1 CLIENT=1
RUN if [ -n "$PUBLIC_BUILD" ]; then \
      rm -rf /opt/lthn/etc/ca /opt/lthn/etc/*.ini /opt/lthn/etc/*.json /opt/lthn/etc/*.pem /opt/lthn/etc/*.tlsauth /opt/lthn/etc/*.keys /opt/lthn/etc/provider* \
        /opt/lthn/var/* \
        /usr/src/lethean-vpn/build /usr/src/lethean-vpn/env.mk; \
      mkdir -p /opt/lthn/var/log /opt/lthn/var/run; \
    fi
