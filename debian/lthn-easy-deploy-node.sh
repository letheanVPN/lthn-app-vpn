#!/bin/bash

set -e

if [ "$(whoami)" == "root" ]; then
  sleep 1
  chown -R lthn:lthn /etc/lthn
  chmod -R o-rwx /etc/lthn
  sudo -E -u lthn bash $(realpath "$0") "$@"
  systemctl disable haproxy
  systemctl stop haproxy
  systemctl disable openvpn
  systemctl stop openvpn
  systemctl enable tinyproxy
  systemctl start tinyproxy
  exit
else
  if [ "$(whoami)" != "lthn" ]; then
    echo "Must be run as root, not $(whoami). Exiting"
    exit 2
  fi
fi

if [ -f /etc/lthn/dispatcher.ini ]; then
  echo "dispatcher.ini already exists! Stopping. To continue, remove old /etc/lthn/dispatcher.ini and run again by yourself!"
  exit 2
fi

# Set defaults. Can be overriden by env variables
[ -z "$LTHNPREFIX" ] && LTHNPREFIX=/
[ -z "$PROVIDERID" ] && PROVIDERID=""
[ -z "$PROVIDERKEY" ] && PROVIDERKEY=""
[ -z "$DAEMON_HOST" ] && DAEMON_HOST="sync.lethean.io"
[ -z "$WALLETFILE" ] && WALLETFILE="/var/lib/lthn/wallet"
[ -z "$WALLETPASS" ] && WALLETPASS="walletpass"
[ -z "$CAPASS" ] && CAPASS=1234
[ -z "$CACN" ] && CACN=ITNSFakeNode
[ -z "$ENDPOINT" ] && ENDPOINT="1.2.3.4"
[ -z "$PORT" ] && PORT="8080"
[ -z "$PROVTYPE" ] && PROVTYPE="residential"

if [ -z "$DAEMON_HOST" ]; then
  DAEMON_ARG=""
else
  DAEMON_ARG="--daemon-host $DAEMON_HOST"
fi

export LTHNPREFIX BRANCH CAPASS CACN ENDPOINT PORT PROVTYPE WALLET EMAIL DAEMON_BIN_URL DAEMON_HOST WALLETPASS PROVIDERID PROVIDERKEY ZABBIX_SERVER ZABBIX_PSK ZABBIX_PORT ZABBIX_META USER HOME HTTP_PROXY HTTPS_PROXY

#rm -rf /tmp/lthn-easy
mkdir -p /tmp/lthn-easy
cd /tmp/lthn-easy
mkdir -p conf

cat >conf/ca.cfg <<EOF
[ ca ]
default_ca = CA_itnsvpn
[ CA_itnsvpn ]
dir               = ./
certs             = \$dir/certs
crl_dir           = \$dir/crl
new_certs_dir     = \$dir/newcerts
database          = \$dir/index.txt
serial            = \$dir/serial
RANDFILE          = \$dir/private/.rand
private_key       = \$dir/private/ca.key.pem
certificate       = \$dir/certs/ca.cert.pem
crlnumber         = \$dir/crlnumber
crl               = \$dir/crl/ca.crl.pem
crl_extensions    = crl_ext
default_crl_days  = 30
default_md        = sha256
name_opt          = ca_default
cert_opt          = ca_default
default_days      = 375
preserve          = no
policy            = policy_strict
[ req ]
default_bits        = 4096
distinguished_name  = req_distinguished_name
string_mask         = utf8only
default_md          = sha256
x509_extensions     = v3_ca
[ usr_cert ]
basicConstraints = CA:FALSE
nsCertType = client, email
nsComment = "OpenSSL Generated Client Certificate"
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
keyUsage = critical, nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth, emailProtection

[ server_cert ]
basicConstraints = CA:FALSE
nsCertType = server
nsComment = "OpenSSL Generated Server Certificate"
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer:always
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth

[ v3_ca ]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical, CA:true
keyUsage = critical, digitalSignature, cRLSign, keyCertSign

[ req_distinguished_name ]
countryName                     = Country Name (2 letter code)
stateOrProvinceName             = State or Province Name
localityName                    = Locality Name
0.organizationName              = Organization Name
organizationalUnitName          = Organizational Unit Name
commonName                      = Common Name
emailAddress                    = Email Address

[ policy_strict ]
countryName             = optional
stateOrProvinceName     = optional
organizationName        = optional
organizationalUnitName  = optional
commonName              = supplied
emailAddress            = optional
EOF

if [ -z "$DAEMON_HOST" ]; then
  sysctl enable lethean-daemon
  sysctl start lethean-daemon
fi

if ! [ -f "$WALLETFILE" ]; then
  lethean-wallet-cli --mnemonic-language English --generate-new-wallet $WALLETFILE $DAEMON_ARG --restore-height 254293 --password "$WALLETPASS" --log-file /dev/stdout --log-level 4 --command exit
fi
WALLET=$(cat ${WALLETFILE}.address.txt)

cat >conf/dispatcher.ini.tmpl <<EOF
[global]
provider-id={providerid}
provider-key={providerkey}
EOF

TOPDIR=$(pwd) /usr/lib/lthn/lthn-configure.sh --generate-providerid --with-wallet-address "$WALLET" --with-wallet-rpc-pass "user" --with-wallet-rpc-pass "pass" --easy --client --server --prefix / --python-bin /usr/bin/python3 --pip-bin /usr/bin/pip3 --runas-user lthn --runas-group lthn "$@"
PROVIDERID=$(cat build/etc/provider.public)
PROVIDERKEY=$(cat build/etc/provider.private)


cat >/etc/lthn/dispatcher.ini <<EOF
[global]
;log-level=DEBUG
ca=/etc/lthn/ca/certs/ca.cert.pem
provider-id=$PROVIDERID
provider-key=$PROVIDERKEY
provider-name=Provider
provider-terms=Some Terms

wallet-address=$WALLET
wallet-username=user
wallet-password=pass

[service-1A]
name=Proxy
backend_proxy_server=localhost:8888
crt=/etc/lthn/ca/certs/ha.cert.pem
key=/etc/lthn/ca/private/ha.key.pem
crtkey=/etc/lthn/ca/certs/ha.both.pem
endpoint=127.0.0.1

[service-1B]
crt=/etc/lthn/ca/certs/vpn.cert.pem
key=/etc/lthn/ca/private/vpn.key.pem
crtkey=/etc/lthn/ca/certs/vpn.both.pem
reneg=60
enabled=false

EOF

rm -f build/etc/dispatcher.ini
if [ -d /etc/lthn/ca/ ]; then
  echo "Old CA dir already exists! Stopping. To continue, remove old /etc/lthn/ca and run again by yourself!"
  exit 2
fi
rm -rf /etc/lthn/ca/
cp -R build/etc/* /etc/lthn/

lvmgmt --generate-sdp \
     --sdp-provider-type $PROVTYPE \
     --sdp-provider-name EasyProvider \
     --wallet-address "$WALLET" \
     --sdp-service-crt /etc/lthn/ca/certs/ha.cert.pem \
     --sdp-service-name proxy --sdp-service-id 1a --sdp-service-endpoint $ENDPOINT --sdp-service-port $PORT \
     --sdp-service-type proxy --sdp-service-cost 0.001 --sdp-service-dlspeed 1 --sdp-service-ulspeed 1 \
     --sdp-service-prepaid-mins 10 --sdp-service-verifications 0

cat /etc/lthn/sdp.json
lvmgmt --upload-sdp
