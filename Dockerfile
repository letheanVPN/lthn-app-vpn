FROM ubuntu:18.04 as base

MAINTAINER Lethean.io <contact@lethean.io>
LABEL "io.lethean.vpn-server"="Lethean.IO"
LABEL version="2.0"
LABEL description="Letehan.io VPN server"

RUN apt update && apt install -y build-essential openvpn haproxy stunnel python3-pip python3-dev \
                  make squid less joe pwgen net-tools zsync bash openssl sudo

WORKDIR /usr/local/src/lethean.io/vpn/exit-node
COPY . .

COPY ./server/docker-run.sh /usr/local/bin/docker-run.sh

RUN pip3 install -r requirements.txt

RUN adduser --system --group --disabled-password lethean; \
	mkdir -p /home/lethean/.intensecoin /opt/lethean/var/log /opt/lethean/var/run; \
	chown -R lethean:lethean /home/lethean /usr/local/src/lethean.io/vpn/exit-node/; \
    chmod +x /usr/local/bin/docker-run.sh configure.sh install.sh; \
    echo "lethean ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers;

VOLUME /home/lethean

RUN echo -e "domain lthn.local\nsearch lthn.local\nnameserver 127.0.0.1\n >/etc/resolv.conf"

COPY --from=registry.gitlab.com/lethean.io/blockchain/lethean:latest /home/lethean/bin /home/lethean/blockchain


USER lethean
RUN ./configure.sh --runas-user lethean --runas-group lethean --client --server

RUN make install SERVER=1 CLIENT=1

RUN sudo rm -rf /opt/lethean/etc/ca /opt/lethean/etc/*.ini /opt/lethean/etc/*.json /opt/lethean/etc/*.pem /opt/lethean/etc/*.tlsauth /opt/lethean/etc/*.keys /opt/lethean/etc/provider* \
        /opt/lethean/var/* /usr/local/src/lethean.io/vpn/exit-node/build /usr/local/src/lethean.io/vpn/exit-node/env.mk ;

RUN sudo mkdir -p /opt/lethean/var/log /opt/lethean/var/run;


WORKDIR /home/lethean



# Service port
EXPOSE ${PORT}

ENTRYPOINT exec docker-run.sh sh
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
