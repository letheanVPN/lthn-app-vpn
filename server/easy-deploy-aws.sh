#!/bin/sh

## Run as:
#wget -O- https://raw.githubusercontent.com/LetheanMovement/lethean-vpn/master/server/easy-deploy-aws.sh | sudo -i -u ubuntu

[ -z "$DAEMONURL" ] && DAEMONURL=https://itns.s3.us-east-2.amazonaws.com/Cli/Cli_Ubuntu160464bitStaticRelease/640/lethean-cli-linux-64bit-letheanize-617a36c.tar.bz2
[ -z "$EMAIL" ] && EMAIL=lukas@lethean.io
[ -z "$BRANCH" ] && BRANCH=master
[ -z "$DAEMONOPTS" ] && DAEMONOPTS=""
DAEMONBZ2=$(basename $DAEMONURL)
DAEMONDIR=$(basename $DAEMONURL .tar.bz2)
export EMAIL DAEMONBZ2 DAEMONDIR DAEMONURL DAEMONOPTS BRANCH

install_daemon(){
  wget -nc -c $DAEMONURL && \
  tar -xjvf $DAEMONBZ2 && \
  sudo cp $DAEMONDIR/* /usr/local/bin/ && \
  echo @reboot /usr/local/bin/letheand --restricted-rpc --rpc-bind-ip 0.0.0.0 --confirm-external-bind --detach >letheand.crontab && \
  crontab letheand.crontab && \
  DEFAULTOPTS="--restricted-rpc --rpc-bind-ip 0.0.0.0 --confirm-external-bind --detach"
  /usr/local/bin/letheand ${DEFAULTOPTS} ${DAEMONOPTS}
}

install_zabbix(){
  wget -nc -c https://repo.zabbix.com/zabbix/3.4/ubuntu/pool/main/z/zabbix-release/zabbix-release_3.4-1+xenial_all.deb && \
  sudo dpkg -i zabbix-release_3.4-1+xenial_all.deb && \
  sudo apt-get update && \
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q zabbix-agent zabbix-sender
  sudo sed -i s/Server=127.0.0.1/Server=monitor.intensecoin.com/ /etc/zabbix/zabbix_agentd.conf
  sudo sed -i s/ServerActive=127.0.0.1/ServerActive=monitor.intensecoin.com/ /etc/zabbix/zabbix_agentd.conf
  sudo sed -i s/^Hostname=.*/HostnameItem=system.hostname/ /etc/zabbix/zabbix_agentd.conf
  sudo sed -i "s/# HostMetadata=/HostMetadata=ITNSNode/" /etc/zabbix/zabbix_agentd.conf
  sudo service zabbix-agent restart
  sudo systemctl enable zabbix-agent
}

install_packages(){
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y postfix mailutils joe tmux
  sudo apt-get upgrade -y -q
}

install_dispatcher(){
  wget https://raw.githubusercontent.com/LetheanMovement/lethean-vpn/${BRANCH}/server/easy-deploy-node.sh
  chmod +x easy-deploy-node.sh
  EMAIL="$EMAIL" ./easy-deploy-node.sh
  sudo systemctl daemon-reload
  sudo systemctl enable lthnvpnd
  sudo service lthnvpnd restart
}

install_packages
install_daemon >daemon.log 2>&1 || mail -s "Daemon installation error" $EMAIL <daemon.log
install_zabbix >zabbix.log 2>&1 || mail -s "Zabbix installation error" $EMAIL <zabbix.log
install_dispatcher >dispatcher.log 2>&1

