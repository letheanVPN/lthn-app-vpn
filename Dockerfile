FROM debian:latest
MAINTAINER Lukas Macura <lukas@lethean.io>

LABEL "io.lethean.vpn-server"="Lethean.IO"
LABEL version="1.0"
LABEL description="Letehan.io VPN server"

#VOLUME ["/opt/lthn"]

EXPOSE 8080/tcp
EXPOSE 8088/tcp

ENV USER=lthn
ENV LTHNPREFIX=/opt/lthn
ENV BRANCH=master
ENV PROVIDERID=""
ENV PROVIDERKEY=""
ENV DAEMON_BIN_URL="https://itns.s3.us-east-2.amazonaws.com/Cli/Cli_Ubuntu160464bitStaticRelease/1755/lethean-cli-linux-64bit-v3.0.0.b3.tar.bz2"
ENV DAEMON_HOST="sync.lethean.io"
ENV WALLETPASS="abcd1234"
ENV CAPASS=1234
ENV CACN=ITNSFakeNode
ENV ENDPOINT="1.2.3.4"
ENV PORT="8080"
ENV PROVTYPE="residential"
ENV EMAIL=""
ENV ZABBIX_SERVER="localhost"
ENV ZABBIX_HOSTNAME="localhost"
ENV ZABBIX_META="LETHEANNODE"
ENV HTTP_PROXY=""
ENV HTTPS_PROXY=""
ENV NO_PROXY=""

ENTRYPOINT ["/entrypiont-lethean-vpn.sh"]
CMD ["run"]

RUN useradd -ms /bin/bash lthn; \
  apt-get update; \
  apt-get install -y sudo joe less mc git python3 python3-pip haproxy openvpn tmux squid net-tools wget; \
  echo "lthn ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers; \
  mkdir /usr/src/lethean-vpn

COPY ./ /usr/src/lethean-vpn/
COPY ./server/docker-run.sh /entrypiont-lethean-vpn.sh
RUN chown -R lthn /usr/src/; chmod +x /entrypiont-lethean-vpn.sh

WORKDIR /usr/src/lethean-vpn
RUN wget -nc -c $DAEMON_BIN_URL; \
  tar --strip-components 1 -C /usr/bin/ -xjvf $(basename $DAEMON_BIN_URL); \
  wget https://repo.zabbix.com/zabbix/4.0/debian/pool/main/z/zabbix-release/zabbix-release_4.0-2+stretch_all.deb; \
  dpkg -i zabbix-release_4.0-2+stretch_all.deb; \
  apt-get update; \
  apt-get install -y zabbix-agent zabbix-sender; \
  mkdir /var/run/zabbix; \
  chown -R lthn /var/log/zabbix /var/run/zabbix; \
  sed -i "s/Hostname=(.*)/Hostname=$ZABBIX_HOSTNAME/" /etc/zabbix/zabbix_agentd.conf; \
  sed -i "s/Server=(.*)/Server=$ZABBIX_SERVER/" /etc/zabbix/zabbix_agentd.conf; \
  sed -i "s/ServerActive=(.*)/ServerActive=$ZABBIX_SERVER/" /etc/zabbix/zabbix_agentd.conf; \
  sed -i "s/Hostname=(.*)/Hostname=$ZABBIX_HOSTNAME/" /etc/zabbix/zabbix_agentd.conf; \
  sed -i "s/HostMetadata=(.*)/HostMetadata=$ZABBIX_META/" /etc/zabbix/zabbix_agentd.conf;

USER lthn
RUN pip3 install -r /usr/src/lethean-vpn/requirements.txt; \
  ./configure.sh --runas-user lthn --runas-group lthn --easy; \
  make install
