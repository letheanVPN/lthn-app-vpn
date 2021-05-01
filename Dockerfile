FROM ubuntu:18.04
MAINTAINER Lethean.io <contact@lethean.io>
LABEL "io.lethean.vpn-server"="Lethean.IO"
LABEL version="2.0"
LABEL description="Letehan.io VPN server"

RUN apt update && apt install -y build-essential openvpn haproxy stunnel python3-pip python3-dev \
                  make squid less joe pwgen net-tools zsync bash openssl sudo

WORKDIR /usr/local/src/lethean.io/vpn/exit-node
COPY . .

RUN pip3 install -r requirements.txt

RUN useradd -ms /bin/bash lthn; \
  echo "lthn ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers;

COPY ./server/docker-run.sh /home/lthn/entrypiont-lethean-vpn.sh

RUN chown -R lthn /usr/local/src/lethean.io/vpn/exit-node/; \
  chmod +x /home/lthn/entrypiont-lethean-vpn.sh; \
  chmod +x /usr/local/src/lethean.io/vpn/exit-node/install.sh
RUN echo -e "domain lthn.local\nsearch lthn.local\nnameserver 127.0.0.1\n >/etc/resolv.conf"

USER lthn

RUN chmod +x configure.sh; ./configure.sh --runas-user lthn --runas-group lthn --client
RUN make install SERVER=1 CLIENT=1
RUN rm -rf /opt/lthn/etc/ca /opt/lthn/etc/*.ini /opt/lthn/etc/*.json /opt/lthn/etc/*.pem /opt/lthn/etc/*.tlsauth /opt/lthn/etc/*.keys /opt/lthn/etc/provider* \
        /opt/lthn/var/* \
        /usr/local/src/lethean.io/vpn/exit-node/build /usr/local/src/lethean.io/vpn/exit-node/env.mk ; \
      mkdir -p /opt/lthn/var/log /opt/lthn/var/run;

WORKDIR /home/lthn

# Service port
EXPOSE ${PORT}


#WORKDIR /usr/src/lethean-vpn/build
#
#RUN wget https://repo.zabbix.com/zabbix/4.0/debian/pool/main/z/zabbix-release/zabbix-release_4.0-2+stretch_all.deb && \
#   dpkg -i zabbix-release_4.0-2+stretch_all.deb
#RUN apt-get update && apt-get install -y zabbix-agent zabbix-sender && mkdir /var/run/zabbix && chown -R lthn /var/log/zabbix /var/run/zabbix
#RUN sed -i "s/Hostname=(.*)/Hostname=$ZABBIX_HOSTNAME/" /etc/zabbix/zabbix_agentd.conf; \
#  sed -i "s/Server=(.*)/Server=$ZABBIX_SERVER/" /etc/zabbix/zabbix_agentd.conf; \
#  sed -i "s/ServerActive=(.*)/ServerActive=$ZABBIX_SERVER/" /etc/zabbix/zabbix_agentd.conf; \
#  sed -i "s/Hostname=(.*)/Hostname=$ZABBIX_HOSTNAME/" /etc/zabbix/zabbix_agentd.conf; \
#  sed -i "s/HostMetadata=(.*)/HostMetadata=$ZABBIX_META/" /etc/zabbix/zabbix_agentd.conf;
