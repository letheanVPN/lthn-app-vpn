#!/bin/sh

sudo -i -u ubuntu <<EOF

DAEMONURL=https://github.com/valiant1x/intensecoin/releases/download/v2.0.2.1/intensecoin-cli-linux-64bit-v2.0.2.1.tar.bz2
DAEMONBZ2=$(basename $DAEMONURL)
DAEMONDIR=$(basename $DAEMONURL .tar.bz2)
EMAIL=lukas@intensecoin.com 
export EMAIL

install_daemon(){
  wget -nc -c $DAEMONURL && \
  tar -xjvf $DAEMONBZ2 && \
  cd $DAEMONDIR && \
  sudo cp * /usr/local/bin/ && \
  echo @reboot /usr/local/bin/intensecoind --restricted-rpc --rpc-bind-ip 0.0.0.0 --confirm-external-bind --detach >intensecoind.crontab && \
  crontab intensecoind.crontab && \
  /usr/local/bin/intensecoind --restricted-rpc --rpc-bind-ip 0.0.0.0 --confirm-external-bind --detach
}

install_zabbix(){
  wget -nc -c https://repo.zabbix.com/zabbix/3.4/ubuntu/pool/main/z/zabbix-release/zabbix-release_3.4-1+xenial_all.deb && \
  sudo dpkg -i zabbix-release_3.4-1+xenial_all.deb && \
  sudo apt-get update && \
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y zabbix-agent zabbix-sender
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
  sudo apt-get upgrade -y
}

install_dispatcher(){
  wget https://raw.githubusercontent.com/valiant1x/intense-vpn/master/server/easy-deploy-node.sh
  chmod +x easy-deploy-node.sh
  EMAIL="$EMAIL" ./easy-deploy-node.sh
  sudo systemctl daemon-reload
  sudo systemctl enable itnsdispatcher
  sudo service itnsdispatcher restart
}

install_packages
install_daemon >daemon.log 2>&1 || mail -s "Daemon installation error" $EMAIL <daemon.log
cd 
install_zabbix >zabbix.log 2>&1 || mail -s "Zabbix installation error" $EMAIL <zabbix.log
cd
install_dispatcher >dispatcher.log 2>&1

EOF

