#!/bin/bash

export HOME=/home/lthn
export BIN_DIR=/opt/lthn/bin
export PATH=$BIN_DIR:/sbin:/usr/sbin:$PATH
export CONF=$HOME/config
export WALLET=$HOME/wallet


export LMDB=$HOME/.intensecoin/lmdb

if [ -f "$CONF/env.sh" ]; then
  . "$CONF/env.sh"
fi

errorExit() {
  echo "$2" >&2
  echo "Exiting with return code $1" >&2
  exit $1
}

prepareConf() {
  cd /usr/src/lethean-vpn || exit
  ./configure.sh --runas-user lthn --runas-group lthn --client
  make install CLIENT=1 || { errorExit 2 "Cannot prepare $CONF! "; }
}

prepareRsyncConf() {
  if ! [ -f $CONF/rsyncd.conf ]; then
    cat >$CONF/rsyncd.conf <<EOF
 [lmdb]
    path = $LMDB
    comment = Lethean Blockchain
    read only = yes
EOF
  fi
}

prepareLmdb() {
  if ! [ -d "$LMDB" ] || [ "$1" = "force" ]; then
    echo "Fetching Blockchain data..." >&2
    mkdir -p $LMDB && cd $LMDB || errorExit 4 "Cannot create $LMDB dir!"
    rm -f data.mdb.zsync
    wget "$ZSYNC_URL" && zsync data.mdb.zsync
    if ! [ -f data.mdb ]; then
      errorExit 4 "Cannot fetch Blockchain data!"
    fi
    if [ -n "$ZSYNC_DATA_SHA" ]; then
      echo "Testing blockchain file for consistency..." >&2
      localsum=$(sha256sum data.mdb | cut -d ' ' -f 1)
      remotesum=$(wget -O- $ZSYNC_DATA_SHA)
      if [ "$localsum" != "$remotesum" ]; then
        errorExit 4 "Blockchain data corrupted!"
      fi
    fi
    echo "Blockchain data downloaded!" >&2
  else
    echo "Blockchain data already exists. Skipping fetch." >&2
  fi
}

runDaemon() {
  if [ -t 0 ]; then
    prepareLmdb
    echo "Starting lethean daemon..." >&2
    letheand "$@"
  else
    errorExit 3 "You must allocate TTY to run letheand! Use -t option"
  fi
}

runWalletRpc() {
  cd $HOME/var || exit
  if [ -z "$WALLET_RPC_URI" ]; then
    echo "Starting Wallet RPC server with $WALLET/$WALLET_FILE." >&2
    rm -f lethean-wallet-vpn-rpc*.login
    lethean-wallet-vpn-rpc --vpn-rpc-bind-port 14660 --wallet-file "$WALLET/$WALLET_FILE" --daemon-host "$DAEMON_HOST" --rpc-login "dispatcher:$WALLET_RPC_PASSWORD" --password "$WALLET_PASSWORD" --log-file /var/log/wallet.log &
    sleep 4
    WALLET_RPC_URI="http://localhost:14660"
  else
    echo "Wallet is outside of container ($WALLET_RPC_URI)." >&2
  fi
}

runWalletCli() {
  cd $BIN_DIR || exit
  if ! [ -t 0 ]; then
    errorExit 3 "You must allocate TTY to run letheand! Use -t option"
  fi
  if [ -z "$WALLET_RPC_URI" ]; then
    echo "Starting Wallet cli with $WALLET/$WALLET_FILE." >&2
    lethean-wallet-cli --wallet-file "$CONF/$WALLET_FILE" --daemon-host "$DAEMON_HOST" --password "$WALLET_PASSWORD"
    sleep 4
  else
    echo "Wallet is outside of container ($WALLET_RPC_URI)." >&2
  fi
}

prepareSquid() {
  cat >$CONF/squid.conf <<EOF
acl SSL_ports port 443
acl Safe_ports port 80          # http
acl Safe_ports port 21          # ftp
acl Safe_ports port 443         # https
acl Safe_ports port 70          # gopher
acl Safe_ports port 210         # wais
acl Safe_ports port 1025-65535  # unregistered ports
acl Safe_ports port 280         # http-mgmt
acl Safe_ports port 488         # gss-http
acl Safe_ports port 591         # filemaker
acl Safe_ports port 777         # multiling http
acl Safe_ports port 8080
acl SSL_ports port 8443
acl SSL_ports port 8080
acl SSL_ports port 80
acl CONNECT method CONNECT
acl localnet dst 172.16.0.0/12
acl localnet dst 192.168.0.0/16
acl localnet dst 10.0.0.0/8
access_log syslog:local0.info squid
cache_log /dev/null
http_access deny !Safe_ports
http_access deny CONNECT !SSL_ports
http_access deny localnet
http_access allow localhost manager
http_access deny manager
http_access allow localhost
http_access deny all
http_port 3128
coredump_dir /var/spool/squid
refresh_pattern ^ftp:           1440    20%     10080
refresh_pattern ^gopher:        1440    0%      1440
refresh_pattern -i (/cgi-bin/|\?) 0     0%      0
refresh_pattern .               0       20%     4320
EOF
}

prepareZabbix() {
  cat >$CONF/zabbix_agentd.conf <<EOF
PidFile=$HOME/var/run/zabbix_agentd.pid
LogFile=/dev/null
LogFileSize=0
Server=127.0.0.1
ServerActive=127.0.0.1
HostnameItem=system.hostname
EOF
}

generateEnv() {
  echo "WALLET_PASSWORD='$WALLET_PASSWORD'"
  echo "WALLET_RPC_PASSWORD=$WALLET_RPC_PASSWORD'"
  echo "CA_PASSWORD='$CA_PASSWORD'"
  echo "PROVIDER_ID='$PROVIDER_ID'"
  echo "PROVIDER_KEY='$PROVIDER_KEY'"
  echo "WALLET_FILE='$WALLET_FILE'"
  echo "WALLET_RPC_URI='$WALLET_RPC_URI'"
}

printWelcome() {
  cat <<EOF
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
*     ___      _______  __   __  __    _        ___   _______     *
*    |   |    |       ||  | |  ||  |  | |      |   | |       |    *
*    |   |    |_     _||  |_|  ||   |_| |      |   | |   _   |    *
*    |   |      |   |  |       ||       |      |   | |  | |  |    *
*    |   |___   |   |  |   _   ||  _    | ___  |   | |  |_|  |    *
*    |       |  |   |  |  | |  || | |   ||   | |   | |       |    *
*    |_______|  |___|  |__| |__||_|  |__||___| |___| |_______|    *
*                                                                 *
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
*                                                                 *
*     Installing Lethean VPN Exit Node, starting in 5 seconds     *
*                                                                 *
*          Welcome to Lethean! We are glad to see you!            *
*                                                                 *
*   We are updating the code, taking advantage of improvements    *
*   not around in 2017. Join our discord and keep track!          *
*                                                                 *
*         Help Docs: https://vpn.lethean.help                     *
*         Discord:   https://discord.lt.hn                        *
*                                                                 *
*           PLEASE CONFIGURE IF YOU KEEP SEEING THIS              *
*                                                                 *
*              docker run lthn/vpn config                         *
*                                                                 *
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
EOF

}

testServerConf() {
  if ! [ -f $HOME/etc/sdp.json ] || ! [ -f $HOME/etc/dispatcher.ini ]; then
    printWelcome
    sleep 5
    configVpn "$@"
    exit
  fi
}

configVpn() {
  cd /usr/src/lethean-vpn || exit

  if [ -z "$WALLET_PASSWORD" ]; then
    WALLET_PASSWORD=$(pwgen 32 1)
  fi
  if [ -z "$WALLET_RPC_PASSWORD" ]; then
    WALLET_RPC_PASSWORD=$(pwgen 32 1)
  fi
  if [ -z "$CA_PASSWORD" ]; then
    CA_PASSWORD=$(pwgen 32 1)
  fi
  if [ -n "$PROVIDER_ID" ]; then
    provideropts="--with-providerid '$PROVIDER_ID' --with-providerkey '$PROVIDER_KEY'"
  else
    provideropts="--generate-providerid"
  fi
  if [ -z "$WALLET_RPC_URI" ]; then
    if ! [ -f "$CONF/$WALLET_FILE" ]; then
      echo "Generating wallet $WALLET_FILE" >&2
      lethean-wallet-cli --mnemonic-language English --generate-new-wallet "$CONF/$WALLET_FILE" --daemon-host $DAEMON_HOST \
        --restore-height "$WALLET_RESTORE_HEIGHT" --password "$WALLET_PASSWORD" --log-file /dev/stdout --log-level 4 --command exit ||
        { errorExit 2 "Cannot create Wallet file! "; }
    fi
    WALLET_ADDRESS=$(cat "$CONF/${WALLET_FILE}.address.txt")
  else
    echo "Wallet is outside of this image." >&2
  fi

  if [ -z "$WALLET_RPC_URI" ]; then
    WALLET_RPC_URI="http://localhost:14660"
  fi

  ./configure.sh --prefix "$HOME" --runas-user lthn --runas-group lthn --easy --with-wallet-address "$WALLET_ADDRESS" \
    --with-wallet-rpc-user dispatcher --with-wallet-rpc-pass "$WALLET_RPC_PASSWORD" $provideropts --with-capass "$CA_PASSWORD" ||
    { errorExit 3 "Cannot configure! Something is wrong."; }
  make install FORCE=y || { errorExit 4 "Cannot install! Something is wrong."; }
  $HOME/bin/lvmgmt --generate-sdp \
    --sdp-provider-type "$PROVIDER_TYPE" \
    --sdp-provider-name "$PROVIDER_NAME" \
    --wallet-address "$WALLET_ADDRESS" \
    --sdp-service-crt $HOME/etc/ca/certs/ha.cert.pem \
    --sdp-service-name proxy --sdp-service-id 1a --sdp-service-endpoint "$ENDPOINT" --sdp-service-port "$PORT" \
    --sdp-service-type proxy --sdp-service-cost 0.001 --sdp-service-dlspeed 1 --sdp-service-ulspeed 1 \
    --sdp-service-prepaid-mins 10 --sdp-service-verifications 0 ||
    { errorExit 5 "Cannot create initial SDP!"; }
  echo >&2
  echo "These are generated ids and settings. Save this information somewhere!" >&2
  echo "If you loose some of these information, you will not be able to recover!" >&2
  if [ -z "$PROVIDER_ID" ]; then
    PROVIDER_ID=$(cat $CONF/provider.public)
    PROVIDER_KEY=$(cat $CONF/provider.private)
  fi
  generateEnv
  echo >&2

}

case $1 in
config | easy-config)
  configVpn "$@"

  ;;

prepare-conf)
  prepareConf
  ;;

upload-sdp)
  $BIN_DIR/lvmgmt --upload-sdp
  ;;

lthnvpnd | run)
  cd $BIN_DIR || exit
  testServerConf "$@"
  if ! [ -f $CONF/zabbix_agentd.conf.conf ]; then
    prepareZabbix || { errorExit 2 "Cannot create $CONF/zabbix_agentd.conf! "; }
  fi
  if [ -x /usr/sbin/zabbix_agentd ]; then
    echo "Starting zabbix agent" >&2
    zabbix_agentd -c /etc/zabbix/zabbix_agentd.conf
  fi
  if ! [ -f $CONF/squid.conf ]; then
    prepareSquid || { errorExit 2 "Cannot create $CONF/squid.conf! "; }
  fi
  echo "Starting squid -f $CONF/squid.conf" >&2
  squid -f $CONF/squid.conf
  if [ -z "$DAEMON_HOST" ]; then
    runDaemon
  fi
  runWalletRpc
  unset HTTP_PROXY
  unset http_proxy
  shift
  while ! curl "$WALLET_RPC_URI" >/dev/null 2>/dev/null; do
    echo "Waiting for wallet rpc server."
    sleep 5
  done
  echo "Starting dispatcher" >&2
  exec lthnvpnd --wallet-rpc-uri "$WALLET_RPC_URI" --syslog "$@"
  ;;

wallet-rpc)
  shift
  runWalletRpc "$@"
  ;;

wallet-cli)
  shift
  runWalletCli "$@"
  ;;

zsync-make)
  if [ -d "$LMDB" ]; then
    cd $LMDB
    zsyncmake -v -b 262144 -f data.mdb -u "$ZSYNC_DATA_URL" data.mdb
    sha256sum data.mdb | cut -d ' ' -f 1 >data.mdb.sha256
  else
    errorExit 2 "LMDB database does not exist!"
  fi
  ;;

sync-bc)
  shift
  prepareLmdb force
  ;;

letheand)
  shift
  runDaemon "$@"
  ;;

connect | lthnvpnc)
  if ! [ -f "$CONF/ha_info.http" ] || ! [ -f "$CONF/dispatcher.ini" ]; then
    prepareConf
  fi
  shift
  exec lthnvpnc connect "$@"
  ;;

list)
  if ! [ -f "$CONF/ha_info.http" ] || ! [ -f "$CONF/dispatcher.ini" ]; then
    prepareConf
  fi
  shift
  exec lthnvpnc list "$@"
  ;;

lvmgmt)
  shift
  exec lvmgmt "$@"
  ;;

root)
  cd $HOME || exit
  su --preserve-environment lthn
  ;;

sh | bash)
  /bin/bash
  ;;

*)
#  run "$@"
  echo "Bad command. Use one of:"
  echo "run [args] to run dispatcher"
  echo "list [args] to list available services"
  echo "connect uri [args] to run client"
  echo "letheand [args] to run letheand"
  echo "easy-deploy [args] to easy deploy node"
  echo "prepare-conf [args] to prepare new conf dir"
  echo "upload-sdp [args] to upload SDP"
  echo "sync-bc to fast sync blockhain data from server."
  echo "wallet-rpc [args] to run wallet-rpc-daemon"
  echo "wallet-cli [args] to run wallet-cli"
  echo "sh to go into shell"
  exit 0
  ;;
esac
